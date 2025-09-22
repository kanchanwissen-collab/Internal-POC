#!/usr/bin/env python3
"""
Script to inject CapSolver API key from environment variable into config.js
"""
import os
import sys
import re

def inject_api_key():
    config_file = "/opt/extensions/capsolver/assets/config.js"
    api_key = os.environ.get("CAPSOLVER_API_KEY")
    
    if not api_key:
        print("No CAPSOLVER_API_KEY environment variable found, using default key")
        return
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Replace the API key in the config
        pattern = r"apiKey:\s*['\"]CAP-[A-Z0-9]+['\"]"
        replacement = f"apiKey: '{api_key}'"
        
        new_content = re.sub(pattern, replacement, content)
        
        with open(config_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ CapSolver API key injected successfully")
        
    except Exception as e:
        print(f"❌ Failed to inject CapSolver API key: {e}")
        sys.exit(1)

if __name__ == "__main__":
    inject_api_key()