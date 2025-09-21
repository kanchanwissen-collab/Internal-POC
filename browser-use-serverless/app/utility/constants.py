
import uuid


SESSION_ID_TO_VNC_PORT = {}
SESSION_ID_TO_WEB_PORT = {}
SESSION_ID_TO_DISPLAY_NUM = {}
SESSION_ID_TO_BROWSER_SESSION = {}
## populate the session map with 10 sessions: session_00 to session_09
SESSIONS_MAP = {f"session_{i:02d}": False for i in range(10)}
BASE_VNC_PORT = 6080
BASE_WEB_PORT = 5080
BASE_DISPLAY_NUM = 101
USED_VNC_PORTS = {f"{BASE_VNC_PORT + i}": False for i in range(10)}
USED_WEB_PORTS = {f"{BASE_WEB_PORT + i}": False for i in range(10)}
USED_DISPLAY_NUMS = {f"{BASE_DISPLAY_NUM + i}": False for i in range(10)}
SESSION_ID_TO_AGENT_MAP = {}

# Session to port/display mapping for easy lookup
SESSION_TO_VNC_PORT = {f"session_{i:02d}": BASE_VNC_PORT + i for i in range(10)}
SESSION_TO_WEB_PORT = {f"session_{i:02d}": BASE_WEB_PORT + i for i in range(10)}
SESSION_TO_DISPLAY_NUM = {f"session_{i:02d}": BASE_DISPLAY_NUM + i for i in range(10)}

# Debug: Print the mappings to ensure they're properly initialized
print(f"DEBUG: SESSION_TO_VNC_PORT initialized with {len(SESSION_TO_VNC_PORT)} entries")
print(f"DEBUG: SESSION_TO_WEB_PORT initialized with {len(SESSION_TO_WEB_PORT)} entries") 
print(f"DEBUG: SESSION_TO_DISPLAY_NUM initialized with {len(SESSION_TO_DISPLAY_NUM)} entries")
print(f"DEBUG: SESSIONS_MAP initialized with {len(SESSIONS_MAP)} entries")  