import os
import subprocess
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, List

from browser_use.browser.session import BrowserSession, BrowserProfile

log = logging.getLogger("ext")

USER_DATA_DIR_BASE = "/tmp/browser_profiles"
os.makedirs(USER_DATA_DIR_BASE, exist_ok=True)

# Prefer container ENV; fallback to repo path for local runs
EXTENSIONS_DIR = os.environ.get(
    "EXTENSIONS_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extensions", "capsolver")),
)

# Track PIDs for each session so we can clean up later
SESSION_PROCESSES: Dict[str, List[subprocess.Popen]] = {}


def _valid_ext_dir(p: str) -> bool:
    """Check if extension directory is valid"""
    pth = Path(p)
    return pth.is_dir() and (pth / "manifest.json").is_file()


def wait_for_display(display: str, timeout: int = 10):
    """Wait until Xvfb display is ready"""
    for _ in range(timeout):
        try:
            subprocess.check_call(
                ["xdpyinfo", "-display", display],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"X display {display} not ready after {timeout}s")


def start_vnc_session(session_id: str, display_num: int, port: int) -> str:
    """Start Xvfb + x11vnc for a session"""
    display = f":{display_num}"
    screen = "1600x1200x24"
    lock_file = f"/tmp/.X{display_num}-lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)

    procs = []

    # Start Xvfb
    xvfb_proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", screen, "+extension", "RANDR", "-ac"]
    )
    procs.append(xvfb_proc)

    # ✅ Wait until display is ready
    wait_for_display(display)

    # Match framebuffer
    xrandr_proc = subprocess.Popen(["xrandr", "--display", display, "--fb", "1600x1200"])
    procs.append(xrandr_proc)

    # Start VNC server
    vnc_proc = subprocess.Popen(
        [
            "x11vnc", "-display", display, "-nopw", "-forever",
            "-rfbport", str(port), "-clip", "1600x1200", "-xrandr", "resize"
        ]
    )
    procs.append(vnc_proc)

    SESSION_PROCESSES[session_id] = procs
    return display


def start_novnc_proxy(session_id: str, vnc_port: int, web_port: int):
    """Start noVNC websockify proxy"""
    proxy_proc = subprocess.Popen([
        "websockify",
        str(web_port),
        f"localhost:{vnc_port}",
        "--web", "/usr/share/novnc",
        "--cert=/dev/null"
    ])
    SESSION_PROCESSES.setdefault(session_id, []).append(proxy_proc)


def cleanup_session_processes(session_id: str):
    """Kill all processes for a session"""
    procs = SESSION_PROCESSES.pop(session_id, [])
    for proc in procs:
        try:
            proc.terminate()
        except Exception:
            pass
    log.info("Cleaned up processes for session %s", session_id)


async def create_browser_session(session_id: str, display_num: int, vnc_port: int, web_port: int) -> BrowserSession:
    """Create a browser session bound to a VNC/Xvfb display"""
    display = start_vnc_session(session_id, display_num, vnc_port)
    start_novnc_proxy(session_id, vnc_port, web_port)

    downloads_dir = f"{USER_DATA_DIR_BASE}/{session_id}/downloads"
    os.makedirs(downloads_dir, exist_ok=True)

    # Build extension flags if the dir is valid
    ext_flags = []
    if _valid_ext_dir(EXTENSIONS_DIR):
        ext_flags = [
            "--enable-extensions",
            f"--load-extension={EXTENSIONS_DIR}",
            f"--disable-extensions-except={EXTENSIONS_DIR}",
        ]
        log.info("Loading extension from %s", EXTENSIONS_DIR)
    else:
        log.warning("Extension directory invalid or missing manifest.json: %s (skipping)", EXTENSIONS_DIR)

    profile = BrowserProfile(
        user_data_dir=f"{USER_DATA_DIR_BASE}/{session_id}",
        allowed_domains=["*"],
        downloads_path=downloads_dir,
        headless=False,
        enable_default_extensions=False,
        env={"DISPLAY": display},  # Set DISPLAY in browser environment
        args=ext_flags + [
            "--start-maximized",
            "--window-position=0,0",
            "--window-size=1600,1200",
            f"--display={display}",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu-sandbox",
            "--remote-debugging-port=0",  # Let Chrome choose an available port
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--force-device-scale-factor=1",
        ],
    )

    # Set DISPLAY environment for this session
    original_display = os.environ.get("DISPLAY")
    os.environ["DISPLAY"] = display
    
    try:
        # ✅ Retry Chrome attach up to 3 times
        retries = 3
        for attempt in range(1, retries + 1):
            try:
                log.info("Attempt %d: Launching Chrome on %s", attempt, display)
                log.info("Chrome args: %s", profile.args)
                log.info("DISPLAY environment: %s", os.environ.get("DISPLAY"))
                
                session = BrowserSession(browser_profile=profile)

                # Start the browser session and connect
                await session.start()
                
                # Give browser time to fully launch
                await asyncio.sleep(3)
                
                # Quick probe → navigate to a blank page to test connection
                await session.navigate_to("about:blank")
                log.info("✅ Chrome attached to %s successfully", display)
                return session

            except Exception as e:
                log.warning(
                    "Chrome failed to attach on %s (attempt %d/%d): %s",
                    display, attempt, retries, e
                )
                try:
                    if 'session' in locals():
                        await session.stop()
                except:
                    pass
                if attempt < retries:
                    await asyncio.sleep(2 * attempt)  # exponential backoff
                else:
                    cleanup_session_processes(session_id)
                    raise RuntimeError(
                        f"Chrome failed to attach to display {display} after {retries} retries"
                    )
    finally:
        # Restore original DISPLAY environment
        if original_display is not None:
            os.environ["DISPLAY"] = original_display
        elif "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]
