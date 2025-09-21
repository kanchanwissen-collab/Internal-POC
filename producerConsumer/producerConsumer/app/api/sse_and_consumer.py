from fastapi import APIRouter, HTTPException,Request
import asyncio
from sse_starlette.sse import EventSourceResponse
import datetime
import json
from pydantic import BaseModel
from app.db.redis import redis_client


router = APIRouter(tags=["SSE and Redis Consumer"])


# --- API Endpoints ---

@router.post("/publish")
async def publish_message(message_data: dict,batch_id :str):
    """
    Publishes a message to the Redis Stream.
    The request body should be a JSON object with key-value pairs.
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")
    try:
        # XADD adds a new entry to the stream. '*' generates a new ID automatically.
        message_id = redis_client.xadd(batch_id, message_data)
        return {"status": "success", "stream": batch_id, "message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish message: {e}")

@router.get("/consume")
async def consume_messages(batch_id :str):
    """
    Consumes all messages from the beginning of the Redis Stream.
    Uses a simple XREAD command.
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")
    try:
        # XREAD reads from one or more streams.
        # '0-0' is a special ID to start reading from the very beginning.
        # The result is a list of streams, each with a list of messages.
        response = redis_client.xread(streams={batch_id: '0-0'})

        if not response:
            return {"messages": []}

        # The response is nested, e.g., [['my_message_stream', [('id1', {'k':'v'}), ('id2', {'k':'v'})]]]
        # We format it into a simpler list of objects.
        stream_messages = response[0][1]
        formatted_messages = [
            {"id": msg_id, "data": msg_data} for msg_id, msg_data in stream_messages
        ]

        return {"messages": formatted_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to consume messages: {e}")

@router.get("/stream-logs/{batch_id}")
async def stream_logs(request: Request, batch_id: str):
    """
    Streams messages from Redis Stream using Server-Sent Events (SSE).
    Accepts a batch_id to create a specific event stream.
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")

    async def event_generator():
        last_id = '0-0'
        while True:
            try:
                if await request.is_disconnected():
                    print("Client disconnected.")
                    break

                # Run the blocking xread call in a thread to avoid blocking the event loop
                response = await asyncio.to_thread(
                    redis_client.xread,
                    streams={batch_id: last_id},
                    count=None,  # Get all available new messages
                    block=5000  # Wait for up to 5 seconds for a new message
                )

                if response:
                    stream_messages = response[0][1]
                    for msg_id, msg_data in stream_messages:
                        message = msg_data.get("message", "")
                        now = datetime.datetime.now()
                        timestamp = now.strftime('%Y-%m-%d %H:%M:%S') + f',{now.microsecond // 1000:03d}'
                        log_message = f"{timestamp} INFO  [main] com.example.MyClass - {message}"
                        
                        yield {
                            "event": batch_id,
                            "data": log_message
                        }
                    
                    # Update last_id to the last message we've processed
                    last_id = stream_messages[-1][0]

            except asyncio.CancelledError:
                print("Client disconnected, closing stream.")
                break
            except Exception as e:
                print(f"Error in stream-logs: {e}")
                # In case of a Redis error, you might want to log it and break or continue
                break

    return EventSourceResponse(event_generator())


@router.get("/stream-logs/request/{request_id}")
async def stream_logs_by_request(request: Request, request_id: str):
    """
    Streams messages from Redis pub/sub using Server-Sent Events (SSE) for a specific request_id.
    This endpoint matches the agent.py publishing pattern: browser_use_logs:{request_id}
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")

    # Use the same pattern as agent.py
    redis_channel = f"browser_use_logs:{request_id}"
    
    async def event_generator():
        pubsub = None
        try:
            # Send initial connection event
            yield {
                "data": json.dumps({
                    "type": "connected",
                    "request_id": request_id,
                    "message": f"Connected to logs for request {request_id}",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            }

            # Create a new Redis connection for pub/sub
            import redis as redis_lib
            redis_host = redis_client.connection_pool.connection_kwargs.get('host', 'redis')
            redis_port = redis_client.connection_pool.connection_kwargs.get('port', 6379)
            
            # Create dedicated Redis client for pub/sub
            pubsub_redis = redis_lib.Redis(host=redis_host, port=redis_port, decode_responses=True)
            pubsub = pubsub_redis.pubsub()
            pubsub.subscribe(redis_channel)
            
            # Send status update
            yield {
                "data": json.dumps({
                    "type": "status", 
                    "message": f"Subscribed to Redis channel: {redis_channel}",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            }

            # Listen for messages
            while True:
                try:
                    if await request.is_disconnected():
                        print(f"Client disconnected from request_id: {request_id}")
                        break

                    # Get message from Redis pub/sub with timeout
                    message = pubsub.get_message(timeout=5.0)
                    
                    if message:
                        if message['type'] == 'message':
                            data = message['data']
                            
                            try:
                                # Try to parse as JSON (from agent.py with PUBSUB_JSON=1)
                                parsed_data = json.loads(data)
                                
                                # Send structured log event
                                yield {
                                    "data": json.dumps({
                                        "type": "log",
                                        "data": {
                                            "level": "INFO",
                                            "message": parsed_data.get("msg", data),
                                            "source": parsed_data.get("agent_name", "browser-agent"),
                                            "request_id": parsed_data.get("request_id", request_id),
                                            "timestamp": parsed_data.get("timestamp", datetime.datetime.now().timestamp()),
                                            "log_source": parsed_data.get("source", "logger")
                                        },
                                        "timestamp": datetime.datetime.now().isoformat(),
                                        "channel": redis_channel
                                    })
                                }
                            except (json.JSONDecodeError, TypeError):
                                # Handle plain text messages
                                yield {
                                    "data": json.dumps({
                                        "type": "log",
                                        "data": {
                                            "level": "INFO",
                                            "message": str(data),
                                            "source": "browser-agent",
                                            "request_id": request_id,
                                            "log_source": "text"
                                        },
                                        "timestamp": datetime.datetime.now().isoformat(),
                                        "channel": redis_channel
                                    })
                                }
                    else:
                        # Send periodic heartbeat when no messages
                        yield {
                            "data": json.dumps({
                                "type": "heartbeat",
                                "timestamp": datetime.datetime.now().isoformat()
                            })
                        }
                    
                    # Small async sleep to prevent blocking
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"Error in stream-logs for request_id {request_id}: {e}")
                    yield {
                        "data": json.dumps({
                            "type": "error",
                            "message": f"Stream error: {str(e)}",
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    }
                    break
            
        except Exception as e:
            print(f"Fatal error in SSE for request_id {request_id}: {e}")
            yield {
                "data": json.dumps({
                    "type": "error",
                    "message": f"Connection error: {str(e)}",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            }
        finally:
            # Clean up Redis subscription
            if pubsub:
                try:
                    pubsub.unsubscribe(redis_channel)
                    pubsub.close()
                except Exception as e:
                    print(f"Error cleaning up Redis subscription for {request_id}: {e}")

    return EventSourceResponse(event_generator())


# --- SSE Client Management ---
sse_clients: list[asyncio.Queue] = []

class SSEMessage(BaseModel):
    message: str
    type: str

class SSEPost(BaseModel):
    event_name: str | None = None
    data: SSEMessage

@router.post("/send-sse")
async def send_sse(post_data: SSEPost):
    """
    Sends a message to all connected SSE clients.
    If event_name is provided, it's a user-specific event.
    Otherwise, it's a global message.
    """
    for client_queue in sse_clients:
        await client_queue.put(post_data)
    return {"status": "success", "clients_notified": len(sse_clients)}

@router.get("/events")
async def events(request: Request):
    """
    SSE endpoint for clients to connect and receive messages.
    """
    client_queue = asyncio.Queue()
    sse_clients.append(client_queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                post_data: SSEPost = await client_queue.get()
                
                message_data = post_data.data.dict()
                message_data["timestamp"] = datetime.datetime.now().isoformat()

                if post_data.event_name:
                    message_data["isUserSpecific"] = True
                    message_data["userId"] = post_data.event_name
                    yield {
                        "event": post_data.event_name,
                        "data": json.dumps(message_data)
                    }
                else:
                    message_data["isGlobalMessage"] = True
                    yield {
                        "data": json.dumps(message_data)
                    }
        except asyncio.CancelledError:
            pass
        finally:
            if client_queue in sse_clients:
                sse_clients.remove(client_queue)
            print("Client disconnected and removed.")

    return EventSourceResponse(event_generator())


