#!/usr/bin/env python3
"""
Test script to verify the session ID generation functionality
"""

import sys
import os

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from utility.constants import generate_session_id

def test_session_id_generation():
    """Test that session ID generation works correctly"""
    print("Testing session ID generation...")
    
    # Generate multiple session IDs
    session_ids = []
    for i in range(5):
        session_id = generate_session_id()
        session_ids.append(session_id)
        print(f"Generated session ID {i+1}: {session_id}")
        
        # Verify format: xxxx-xxxx-xxxx-xxxx
        parts = session_id.split('-')
        assert len(parts) == 4, f"Session ID should have 4 parts separated by hyphens, got {len(parts)}"
        
        for part in parts:
            assert len(part) == 4, f"Each part should be 4 characters, got {len(part)}"
            assert all(c in '0123456789abcdef' for c in part), f"Part should only contain hex digits, got {part}"
    
    # Verify all generated IDs are unique
    assert len(set(session_ids)) == len(session_ids), "All session IDs should be unique"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_session_id_generation()
