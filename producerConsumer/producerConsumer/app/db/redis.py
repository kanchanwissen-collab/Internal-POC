import redis
import os

# --- Redis Connection ---
try:
    # Use the service name 'redis' as the host, which is standard in Docker Compose.
    # Default to 'localhost' for local development outside of Docker.
    REDIS_HOST =os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT"))

    # decode_responses=True decodes responses from bytes to utf-8 strings
    redis_client = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
    )
    # Check if the connection is successful
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")
    # In a real application, you might want to exit or handle this more gracefully
    redis_client = None
except Exception as e:
    print(f"An unexpected error occurred when connecting to Redis: {e}")
    redis_client = None
