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
    
    # Clean up any existing lock file
    if os.path.exists(lock_file):
        os.remove(lock_file)

    # Kill any existing processes that might be using our ports/display
    try:
        subprocess.run(["pkill", "-f", f"x11vnc.*-rfbport.*{port}"], capture_output=True)
        subprocess.run(["pkill", "-f", f"Xvfb.*:{display_num}"], capture_output=True)
        time.sleep(1)  # Give processes time to die
    except Exception:
        pass

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
            "-rfbport", str(port), "-clip", "1600x1200", "-xrandr", "resize","--shared"
        ]
    )
    procs.append(vnc_proc)

    SESSION_PROCESSES[session_id] = procs
    return display


def start_novnc_proxy(session_id: str, vnc_port: int, web_port: int):
    """Start noVNC websockify proxy"""
    # Kill any existing websockify process using this port
    try:
        subprocess.run(["pkill", "-f", f"websockify.*{web_port}"], capture_output=True)
        time.sleep(1)  # Give process time to die
    except Exception:
        pass
        
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
    
    # First try graceful termination
    for proc in procs:
        try:
            if proc.poll() is None:  # Process is still running
                proc.terminate()
        except Exception as e:
            log.warning(f"Error terminating process {proc.pid}: {e}")
    
    # Wait a bit for graceful termination
    time.sleep(2)
    
    # Force kill any remaining processes
    for proc in procs:
        try:
            if proc.poll() is None:  # Process is still running
                log.warning(f"Force killing process {proc.pid}")
                proc.kill()
                proc.wait(timeout=5)  # Wait up to 5 seconds for process to die
        except Exception as e:
            log.warning(f"Error force killing process {proc.pid}: {e}")
      # Additional cleanup: kill any remaining processes using the specific ports
    try:
        # Get the ports for this session
        from utility.constants import SESSION_ID_TO_VNC_PORT, SESSION_ID_TO_WEB_PORT
        if session_id in SESSION_ID_TO_VNC_PORT:
            vnc_port = SESSION_ID_TO_VNC_PORT[session_id]
            web_port = SESSION_ID_TO_WEB_PORT[session_id]
            
            # Kill processes using VNC port
            subprocess.run([
                "pkill", "-f", f"x11vnc.*-rfbport.*{vnc_port}"
            ], capture_output=True)
            
            # Kill processes using web port  
            subprocess.run([
                "pkill", "-f", f"websockify.*{web_port}"
            ], capture_output=True)
            
            # Kill any remaining Xvfb processes for this display
            display_num = session_id.split('_')[1] if '_' in session_id else '0'
            display_num = int(display_num) + 101  # Based on your BASE_DISPLAY_NUM
            subprocess.run([
                "pkill", "-f", f"Xvfb.*:{display_num}"
            ], capture_output=True)
            
    except Exception as e:
        log.warning(f"Error in additional cleanup for session {session_id}: {e}")
    
    log.info("Cleaned up processes for session %s", session_id)


async def create_browser_session(session_id: str, display_num: int, vnc_port: int, web_port: int) -> BrowserSession:
    """Create a browser session bound to a VNC/Xvfb display"""
    try:
        log.info("Creating browser session for %s with display %s, vnc_port %s, web_port %s", 
                session_id, display_num, vnc_port, web_port)
        
        display = start_vnc_session(session_id, display_num, vnc_port)
        start_novnc_proxy(session_id, vnc_port, web_port)

        # Give VNC server time to fully start
        await asyncio.sleep(2)

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
                    
                    session:BrowserSession = BrowserSession(browser_profile=profile,keep_alive=True)

                    # Start the browser session and connect
                    await session.start()
                    
                    # Give browser time to fully launch
                    await asyncio.sleep(3)
                    
                    # Quick probe → navigate to a blank page to test connection
                    
                    
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
                            f"Chrome failed to attach to display {display} after {retries} retries: {str(e)}"
                        )
        finally:
            # Restore original DISPLAY environment
            if original_display is not None:
                os.environ["DISPLAY"] = original_display
            elif "DISPLAY" in os.environ:
                del os.environ["DISPLAY"]
                
    except Exception as e:
        log.error("Failed to create browser session for %s: %s", session_id, str(e))
        cleanup_session_processes(session_id)
        raise
