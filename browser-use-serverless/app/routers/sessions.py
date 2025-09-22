from fastapi import APIRouter, HTTPException
from services.displayAllocation import create_browser_session, cleanup_session_processes
from utility.constants import (
    USED_DISPLAY_NUMS, USED_VNC_PORTS, USED_WEB_PORTS, 
    SESSION_ID_TO_BROWSER_SESSION, SESSION_ID_TO_VNC_PORT, SESSION_ID_TO_WEB_PORT, SESSION_ID_TO_DISPLAY_NUM,
    BASE_VNC_PORT, BASE_WEB_PORT, BASE_DISPLAY_NUM, generate_session_id
)
import os 

router = APIRouter()

# Global variable to track the current active session
current_session_id = None

def is_session_active(session_id: str) -> bool:
    """Check if a given session ID is the current active session"""
    return current_session_id is not None and current_session_id == session_id

def get_current_session_id() -> str | None:
    """Get the current active session ID"""
    return current_session_id

def clear_current_session():
    """Clear the current active session - used by agent cleanup"""
    global current_session_id
    current_session_id = None

@router.post("/sessions")
async def create_session():
    global current_session_id
    
    try:
        # Check if there's already an active session
        if current_session_id is not None:
            raise HTTPException(status_code=503, detail="Session is already in use. Only one session is supported.")
        
        # Generate a new random session ID
        session_id = generate_session_id()
        current_session_id = session_id
        
        # Assign fixed ports and display for the single session
        vnc_port = BASE_VNC_PORT
        web_port = BASE_WEB_PORT 
        display_num = BASE_DISPLAY_NUM
        
        # Store the mappings
        SESSION_ID_TO_VNC_PORT[session_id] = vnc_port
        SESSION_ID_TO_WEB_PORT[session_id] = web_port
        SESSION_ID_TO_DISPLAY_NUM[session_id] = display_num
        
        # Mark the corresponding ports and display as used
        USED_VNC_PORTS[str(vnc_port)] = True
        USED_WEB_PORTS[str(web_port)] = True
        USED_DISPLAY_NUMS[str(display_num)] = True
        
        # Create browser session
        browser_session = await create_browser_session(session_id, display_num, vnc_port, web_port)
        SESSION_ID_TO_BROWSER_SESSION[session_id] = browser_session
        
        vnc_url = f"{os.getenv('VNC_BASE_URL', 'http://localhost:8080')}/sessions/{session_id}/vnc/vnc.html?autoconnect=1"

        return {
            "session_id": session_id,
            "vnc_url": vnc_url,
            "vnc_port": vnc_port,
            "web_port": web_port,
            "display_num": display_num
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup in case of error
        if current_session_id:
            current_session_id = None
            if 'vnc_port' in locals():
                USED_VNC_PORTS[str(vnc_port)] = False
            if 'web_port' in locals(): 
                USED_WEB_PORTS[str(web_port)] = False
            if 'display_num' in locals():
                USED_DISPLAY_NUMS[str(display_num)] = False
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    global current_session_id
    
    try:
        if current_session_id is None or current_session_id != session_id:
            raise HTTPException(status_code=404, detail="Session not found or not active")

        # Clear the current session
        current_session_id = None

        # Get the associated ports and display numbers
        vnc_port = SESSION_ID_TO_VNC_PORT.get(session_id)
        web_port = SESSION_ID_TO_WEB_PORT.get(session_id)
        display_num = SESSION_ID_TO_DISPLAY_NUM.get(session_id)

        # Free up the ports and display
        if vnc_port:
            USED_VNC_PORTS[str(vnc_port)] = False
        if web_port:
            USED_WEB_PORTS[str(web_port)] = False
        if display_num:
            USED_DISPLAY_NUMS[str(display_num)] = False

        # Close the browser session if it exists
        browser_session = SESSION_ID_TO_BROWSER_SESSION.get(session_id)
        if browser_session:
            try:
                await browser_session.stop()
            except Exception as e:
                print(f"Error stopping browser session: {e}")
            del SESSION_ID_TO_BROWSER_SESSION[session_id]

        # Clean up session mappings
        if session_id in SESSION_ID_TO_VNC_PORT:
            del SESSION_ID_TO_VNC_PORT[session_id]
        if session_id in SESSION_ID_TO_WEB_PORT:
            del SESSION_ID_TO_WEB_PORT[session_id]
        if session_id in SESSION_ID_TO_DISPLAY_NUM:
            del SESSION_ID_TO_DISPLAY_NUM[session_id]

        # Clean up all session processes (Xvfb, x11vnc, websockify)
        cleanup_session_processes(session_id)

        return {"message": f"Session {session_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def list_sessions():
    """Get status of active sessions"""
    try:
        sessions = []
        
        if current_session_id is not None:
            vnc_url = f"{os.getenv('VNC_BASE_URL', 'http://localhost:8080')}/sessions/{current_session_id}/vnc/vnc.html?autoconnect=1"
            
            session_info = {
                "session_id": current_session_id,
                "active": True,
                "vnc_url": vnc_url,
                "vnc_port": SESSION_ID_TO_VNC_PORT.get(current_session_id),
                "web_port": SESSION_ID_TO_WEB_PORT.get(current_session_id),
                "display_num": SESSION_ID_TO_DISPLAY_NUM.get(current_session_id)
            }
            sessions.append(session_info)
        
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))