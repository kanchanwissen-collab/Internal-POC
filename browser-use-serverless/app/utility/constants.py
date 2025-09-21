import uuid
import secrets

SESSION_ID_TO_VNC_PORT = {}
SESSION_ID_TO_WEB_PORT = {}
SESSION_ID_TO_DISPLAY_NUM = {}
SESSION_ID_TO_BROWSER_SESSION = {}

# Track the current active session (only one allowed)
CURRENT_SESSION_ID = None
BASE_VNC_PORT = 6080
BASE_WEB_PORT = 5080
BASE_DISPLAY_NUM = 101
USED_VNC_PORTS = {"6080": False}
USED_WEB_PORTS = {"5080": False}
USED_DISPLAY_NUMS = {"101": False}
SESSION_ID_TO_AGENT_MAP = {}

def generate_session_id():
    """Generate a random 16-digit hexadecimal session ID in format xxxx-xxxx-xxxx-xxxx"""
    # Generate 16 random hex digits
    hex_digits = secrets.token_hex(8)  # 8 bytes = 16 hex digits
    # Format as xxxx-xxxx-xxxx-xxxx
    formatted_id = f"{hex_digits[0:4]}-{hex_digits[4:8]}-{hex_digits[8:12]}-{hex_digits[12:16]}"
    return formatted_id

# Debug: Print the initialization
print("DEBUG: Session management initialized for single session with dynamic ID generation")