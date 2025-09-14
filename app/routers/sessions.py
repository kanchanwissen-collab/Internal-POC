from fastapi import APIRouter
from services.displayAllocation import create_browser_session, cleanup_session_processes
from utility.constants import (
    SESSIONS_MAP, USED_DISPLAY_NUMS, USED_VNC_PORTS, USED_WEB_PORTS, 
    SESSION_ID_TO_BROWSER_SESSION, SESSION_TO_VNC_PORT, SESSION_TO_WEB_PORT, SESSION_TO_DISPLAY_NUM
)
import os 

router = APIRouter()

@router.post("/sessions")
async def create_session():
    try:
        # Find the first free session in the SESSIONS_MAP
        free_session_id = next((sid for sid, used in SESSIONS_MAP.items() if not used), None)
        if not free_session_id:
            return {"error": "No free sessions available"}, 503
        
        # Mark session as used
        SESSIONS_MAP[free_session_id] = True
        session_id = free_session_id
        
        # Get predefined ports and display number for this session
        vnc_port = SESSION_TO_VNC_PORT[session_id]
        web_port = SESSION_TO_WEB_PORT[session_id] 
        display_num = SESSION_TO_DISPLAY_NUM[session_id]
        
        # Mark the corresponding ports and display as used
        USED_VNC_PORTS[str(vnc_port)] = True
        USED_WEB_PORTS[str(web_port)] = True
        USED_DISPLAY_NUMS[str(display_num)] = True
        
        # Create browser session
        browser_session = await create_browser_session(session_id, display_num, vnc_port, web_port)
        SESSION_ID_TO_BROWSER_SESSION[session_id] = browser_session
        
        vnc_url = f"{os.getenv('VNC_BASE_URL', 'http://localhost')}/sessions/{session_id}/vnc/vnc.html?autoconnect=1"

        return {
            "session_id": session_id,
            "vnc_url": vnc_url,
            "vnc_port": vnc_port,
            "web_port": web_port,
            "display_num": display_num
        }
        
    except Exception as e:
        # Cleanup in case of error
        if 'session_id' in locals():
            SESSIONS_MAP[session_id] = False
            if 'vnc_port' in locals():
                USED_VNC_PORTS[str(vnc_port)] = False
            if 'web_port' in locals(): 
                USED_WEB_PORTS[str(web_port)] = False
            if 'display_num' in locals():
                USED_DISPLAY_NUMS[str(display_num)] = False
        return {"error": str(e)}, 500
@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        if session_id not in SESSIONS_MAP or not SESSIONS_MAP[session_id]:
            return {"error": "Session ID not found or already free"}, 404

        # Mark the session as free
        SESSIONS_MAP[session_id] = False

        # Free up the associated ports and display numbers using predefined mapping
        vnc_port = SESSION_TO_VNC_PORT[session_id]
        web_port = SESSION_TO_WEB_PORT[session_id]
        display_num = SESSION_TO_DISPLAY_NUM[session_id]

        USED_DISPLAY_NUMS[str(display_num)] = False
        USED_VNC_PORTS[str(vnc_port)] = False
        USED_WEB_PORTS[str(web_port)] = False

        # Close the browser session if it exists
        browser_session = SESSION_ID_TO_BROWSER_SESSION.get(session_id)
        if browser_session:
            try:
                await browser_session.stop()
            except Exception as e:
                print(f"Error stopping browser session: {e}")
            del SESSION_ID_TO_BROWSER_SESSION[session_id]

        # Clean up all session processes (Xvfb, x11vnc, websockify)
        cleanup_session_processes(session_id)

        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

@router.get("/sessions")
async def list_sessions():
    """Get status of all sessions"""
    sessions_status = []
    for session_id, is_active in SESSIONS_MAP.items():
        sessions_status.append({
            "session_id": session_id,
            "active": is_active,
            "vnc_port": SESSION_TO_VNC_PORT[session_id],
            "web_port": SESSION_TO_WEB_PORT[session_id],
            "display_num": SESSION_TO_DISPLAY_NUM[session_id]
        })
    return {"sessions": sessions_status}