#!/bin/bash
set -e

# Start the first process
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --proxy-headers &

# Start the second process
python consumer.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
