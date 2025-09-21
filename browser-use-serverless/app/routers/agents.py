# routers/agents.py
from __future__ import annotations

import os
import re
import io
import sys
import json
import logging
from typing import Optional, Any, Dict

import redis
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from browser_use.agent.service import Agent
from browser_use.llm.google.chat import ChatGoogle

from services.displayAllocation import cleanup_session_processes
from utility.customController import tools
from utility.constants import (
    SESSION_ID_TO_AGENT_MAP,
    SESSIONS_MAP,
    SESSION_ID_TO_BROWSER_SESSION,
    USED_DISPLAY_NUMS,
    USED_VNC_PORTS,
    USED_WEB_PORTS,
    SESSION_TO_DISPLAY_NUM,
    SESSION_TO_VNC_PORT,
    SESSION_TO_WEB_PORT,
)

# ---------- env ----------
load_dotenv()

# ---------- api ----------
router = APIRouter()

# ---------- models ----------
class AgentCreateRequest(BaseModel):
    task: str = Field(..., description="The task for the agent")
    session_id: str = Field(..., description="The session ID to associate with the agent")
    request_id: Optional[str] = Field(None, description="Optional request ID for tracking")


# ---------- logging formatting for Redis stream ----------
ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

def clean_msg(s: str) -> str:
    """Strip ANSI color codes and CRs (keep emojis)."""
    return ANSI_RE.sub("", s).rstrip("\r")


def _pretty_name(name: str) -> str:
    """Mimic BrowserUseFormatter's display names."""
    if name.startswith("browser_use.agent"):
        return "Agent"
    if name.startswith("browser_use.browser.session"):
        return "BrowserSession"
    if name.startswith("browser_use.tools"):
        return "tools"
    if name.startswith("browser_use.dom"):
        return "dom"
    if name.startswith("browser_use."):
        return name.split(".")[-1]
    return name


class RedisFormatter(logging.Formatter):
    """Format like console: LEVEL TIMESTAMP [Name] message."""
    def __init__(self, fmt: str):
        super().__init__(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        original = record.name
        try:
            record.name = _pretty_name(original)
            text = super().format(record)
            return clean_msg(text)
        finally:
            record.name = original


# ---------- routes ----------
@router.post("/agents")
async def create_agent(body: AgentCreateRequest):
    """
    Start an agent and stream logs to Redis. This endpoint blocks until the agent finishes.
    """
    # validate requireds first
    if not body.request_id:
        raise HTTPException(status_code=400, detail="request_id is required")

    session_id = body.session_id
    request_id = body.request_id
    task = body.task

    # locals used in finally
    bu = logging.getLogger("browser_use")
    bu_prev_level = bu.level if isinstance(bu.level, int) else logging.INFO
    redis_handler = None
    _stdout = None
    _stderr = None

    try:
        # --- basic guards ---
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY environment variable not set")

        if not SESSIONS_MAP.get(session_id, False):
            raise HTTPException(status_code=400, detail="Invalid or inactive session ID")

        browser_session = SESSION_ID_TO_BROWSER_SESSION.get(session_id)
        if not browser_session:
            raise HTTPException(status_code=404, detail="No browser session found for the given session ID")

        # --- redis stream client ---
        stream_name = os.getenv("REDIS_STREAM", "browser_use_logs").strip()
        stream_key = f"{stream_name}:{request_id}"
        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)

        # --- attach redis log handler to parent 'browser_use' logger ---
        class RedisHandler(logging.Handler):
            def __init__(self, stream_key_: str):
                super().__init__()
                self.stream_key = stream_key_
            def emit(self, record: logging.LogRecord):
                try:
                    formatted = self.format(record)
                    if formatted.strip():
                        r.xadd(self.stream_key, {"msg": formatted})
                except Exception:
                    # never crash the agent if Redis fails
                    pass

        def _remove_handlers_with_stream_key(logger_obj: logging.Logger, key: str):
            for h in list(logger_obj.handlers):
                if hasattr(h, "stream_key") and getattr(h, "stream_key") == key:
                    try:
                        logger_obj.removeHandler(h)
                    except Exception:
                        pass

        redis_handler = RedisHandler(stream_key)
        redis_handler.setFormatter(
            RedisFormatter("%(levelname)-8s %(asctime)s [%(name)s] %(message)s")
        )

        _remove_handlers_with_stream_key(bu, stream_key)
        bu.setLevel(logging.INFO)
        bu.addHandler(redis_handler)

        # ensure relevant children propagate upwards
        for child_name in [
            "browser_use.controller",
            "browser_use.controller.service",
            "browser_use.controller.registry",
            "browser_use.controller.registry.service",
            "browser_use.browser.session",
            "browser_use.agent",
            "browser_use.agent.service",
            "browser_use.agent.message_manager",
            "browser_use.agent.message_manager.utils",
            "browser_use.sync",
            "browser_use.sync.service",
            "browser_use.tokens",
            "browser_use.tokens.service",
            "browser_use.telemetry",
            "browser_use.telemetry.service",
        ]:
            lg = logging.getLogger(child_name)
            # drop prior handlers for this stream
            _remove_handlers_with_stream_key(lg, stream_key)
            lg.propagate = True
            lg.setLevel(logging.INFO)

        # --- allowed upload files exposed to the agent ---
        available_file_paths = [
            "/app/tmp/test_document.pdf",
            "/app/tmp/test_document.txt",
        ]

        # --- build agent (synchronous run; this call will block) ---
        agent: Agent = Agent(
            task=task,
            task_id=session_id,
            browser_session=browser_session,
            llm=ChatGoogle(temperature=0.3, model="gemini-2.5-pro", api_key=api_key),
		    page_extraction_llm=ChatGoogle(temperature=0.2, model="gemini-2.5-pro", api_key=api_key),

            
            extend_system_message="""
You are a powerful browser agent that fills the preauth form.
Tools you have access to:
  -- upload file tool: Upload file to interactive element with file path
Available file paths for upload:
  - /app/tmp/test_document.pdf
  - /app/tmp/test_document.txt

Rules during form filling:
- The website uses multiple iframes; it can be laggy and slow.
- Always wait for the page to load completely before interacting with elements.
- Dropdown menus may take a few seconds to populate; be patient.
- Do NOT use the Enter key for dropdowns; use mouse clicks only.
- There is an AI chat button (Olivia) on the website; never click that.
- If a file upload field appears, use the upload file tool.
- Do not click Continue before file upload completes. If upload repeatedly fails, stop execution.
- The file paths are in `available_file_paths` (custom context).
""",
            tools=tools,
            max_failures=10,
            max_actions_per_step=15,
            available_file_paths=available_file_paths,
            custom_context={"available_file_paths": available_file_paths},
        )

        # store reference for lifecycle ops
        SESSION_ID_TO_AGENT_MAP[session_id] = agent

        # --- tee stdout/stderr for key agent lines into Redis stream as well ---
        agent_line = re.compile(r"\[Agent\]|📍\s*Step|🦾\s*\[ACTION|📄\s*Result", re.UNICODE)

        class _StdTee(io.TextIOBase):
            def __init__(self, orig: io.TextIOBase, pattern: re.Pattern):
                self.orig = orig
                self.pattern = pattern
            def write(self, s: str):
                self.orig.write(s)
                for line in s.splitlines():
                    if self.pattern.search(line):
                        msg = clean_msg(line)
                        if msg.strip():
                            r.xadd(stream_key, {"msg": msg})
                return len(s)
            def flush(self):
                self.orig.flush()

        _stdout, _stderr = sys.stdout, sys.stderr
        sys.stdout = _StdTee(_stdout, agent_line)
        sys.stderr = _StdTee(_stderr, agent_line)

        # probe lines (can be removed)
        logging.getLogger("browser_use.agent.service").info("[Agent] logger path check")
        print("[Agent] print path check")

        # ----- RUN (blocking; you asked for long request) -----
        await agent.run()

       

        return JSONResponse(
            status_code=200,
            content={
                "message": "Agent completed successfully",
                "request_id": request_id,
                "session_id": session_id,
                "remarks":  "No result produced",
            },
        )

    except HTTPException:
        # rethrow fastapi exceptions as-is
        raise
    except Exception as e:
        # generic 500 with message
        raise HTTPException(status_code=500, detail=f"Failed to start/run agent: {str(e)}")
    finally:
        # restore std streams
        try:
            if _stdout is not None and _stderr is not None:
                sys.stdout, sys.stderr = _stdout, _stderr
        except Exception:
            pass

        # detach logging handler & level
        try:
            if redis_handler is not None:
                bu.removeHandler(redis_handler)
            bu.setLevel(bu_prev_level)
        except Exception:
            pass

        # best-effort cleanup of processes/ports/maps
        

        # drop agent map entry
        

        # free display/vnc/web ports (guards)
        


@router.get("/agents/{session_id}/stop")
async def stop_agent(session_id: str):
    try:
        if not SESSIONS_MAP.get(session_id, False):
            raise HTTPException(status_code=400, detail="Invalid or inactive session ID")

        agent: Optional[Agent] = SESSION_ID_TO_AGENT_MAP.get(session_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # cooperative stop
        try:
            agent.stop()
        except Exception:
            # ignore if the underlying lib has different semantics
            pass

        # cleanup
        try:
            cleanup_session_processes(str(session_id))
        except Exception:
            pass

        SESSION_ID_TO_AGENT_MAP.pop(session_id, None)
        SESSIONS_MAP[session_id] = False
        SESSION_ID_TO_BROWSER_SESSION.pop(session_id, None)

        display_num = SESSION_TO_DISPLAY_NUM.pop(session_id, None)
        vnc_port = SESSION_TO_VNC_PORT.pop(session_id, None)
        web_port = SESSION_TO_WEB_PORT.pop(session_id, None)
        if display_num is not None:
            USED_DISPLAY_NUMS[str(display_num)] = False
        if vnc_port is not None:
            USED_VNC_PORTS[str(vnc_port)] = False
        if web_port is not None:
            USED_WEB_PORTS[str(web_port)] = False

        return {"message": f"Agent for session {session_id} stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{session_id}/pause")
async def pause_agent(session_id: str):
    try:
        if not SESSIONS_MAP.get(session_id, False):
            raise HTTPException(status_code=400, detail="Invalid or inactive session ID")

        agent: Optional[Agent] = SESSION_ID_TO_AGENT_MAP.get(session_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        try:
            agent.pause()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Pause failed: {str(e)}")

        return {"message": f"Agent for session {session_id} paused successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{session_id}/resume")
async def resume_agent(session_id: str):
    try:
        if not SESSIONS_MAP.get(session_id, False):
            raise HTTPException(status_code=400, detail="Invalid or inactive session ID")

        agent: Optional[Agent] = SESSION_ID_TO_AGENT_MAP.get(session_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        try:
            agent.resume()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)}")

        return {"message": f"Agent for session {session_id} resumed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _serialize_state(state: Any) -> Dict[str, Any]:
    """
    Helper in case you want to expose state in a stable, JSON-safe format.
    """
    try:
        # if the Agent exposes a dict-like view
        if hasattr(state, "model_dump"):
            return state.model_dump()
        if hasattr(state, "dict"):
            return state.dict()
        return json.loads(json.dumps(state, default=str))
    except Exception:
        return {"repr": str(state)}


@router.get("/agents/{session_id}/status")
async def get_agent_status(session_id: str):
    try:
        if not SESSIONS_MAP.get(session_id, False):
            raise HTTPException(status_code=400, detail="Invalid or inactive session ID")

        agent: Optional[Agent] = SESSION_ID_TO_AGENT_MAP.get(session_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        state = getattr(agent, "state", None)
        safe_state = _serialize_state(state) if state is not None else None

        return {"session_id": session_id, "status": safe_state}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
