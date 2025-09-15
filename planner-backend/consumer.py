# consumer.py
import asyncio
import json
import logging
import os
import signal
from typing import Optional
import httpx
import time
from google.cloud import pubsub_v1
from dotenv import load_dotenv
load_dotenv()

# --- In-memory Cache (replaces Redis) ---
class InMemoryCache:
    def __init__(self):
        self._data = {}
        self._expiry = {}

    def _is_expired(self, key):
        if key in self._expiry and self._expiry[key] < time.time():
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            return True
        return False

    def get(self, key):
        if self._is_expired(key):
            return None
        return self._data.get(key)

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self._data and not self._is_expired(key):
            return False
        
        self._data[key] = value
        if ex:
            self._expiry[key] = time.time() + ex
        else:
            self._expiry.pop(key, None)
        return True

    def setex(self, key, ttl, value):
        self._data[key] = value
        self._expiry[key] = time.time() + ttl
        return True

    def delete(self, key):
        if key in self._data:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            return 1
        return 0

redis_client = InMemoryCache()

# --- Config ---
PROJECT_ID      = os.getenv("GOOGLE_CLOUD_PROJECT", "")
SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION", "")
PROCESSOR_URL   = os.getenv("PROCESSOR_URL", "http://localhost:8001/api/planner-preauth")
CONNECT_TIMEOUT = float(os.getenv("HTTP_CONNECT_TIMEOUT", "5"))
WRITE_TIMEOUT   = float(os.getenv("HTTP_WRITE_TIMEOUT", "10"))
READ_TIMEOUT    = float(os.getenv("HTTP_READ_TIMEOUT", "20"))  # give the handler time to work
POOL_LIMIT      = int(os.getenv("HTTP_POOL_LIMIT", "100"))
POOL_TIMEOUT=float(os.getenv("HTTP_TIMEOUT","5"))
MAX_MESSAGES = int(os.getenv("MAX_OUTSTANDING_MESSAGES", "50"))
MAX_BYTES    = int(os.getenv("MAX_OUTSTANDING_BYTES", str(50 * 1024 * 1024)))
DEDUP_TTL        = int(os.getenv("DEDUP_TTL_SECONDS", "86400"))      # 24h for processed keys
INFLIGHT_TTL     = int(os.getenv("INFLIGHT_TTL_SECONDS", "600"))     # 10m lock to avoid races
# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
_http_client: Optional[httpx.AsyncClient] = None

async def get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=CONNECT_TIMEOUT,
                write=WRITE_TIMEOUT,
                read=READ_TIMEOUT,
                pool=POOL_TIMEOUT,        # <— ADD THIS
            ),
            limits=httpx.Limits(
                max_keepalive_connections=POOL_LIMIT,
                max_connections=POOL_LIMIT,
            ),
        )
    return _http_client

def _req_id_for(msg: pubsub_v1.subscriber.message.Message) -> str:
    # Prefer publisher-provided req_id; fallback to Pub/Sub message_id
    return msg.attributes.get("req_id") or msg.message_id

def _claim_inflight(req_id: str) -> bool:
    # SETNX with TTL = claim if not exists
    return bool(redis_client.set(f"inflight:{req_id}", "1", nx=True, ex=INFLIGHT_TTL))

def _clear_inflight(req_id: str) -> None:
    redis_client.delete(f"inflight:{req_id}")

def _mark_processed(req_id: str) -> None:
    redis_client.setex(f"processed:{req_id}", DEDUP_TTL, "processed")

async def call_planner(payload: dict, req_id: str) -> int:
    client = await get_client()
    resp = await client.post(PROCESSOR_URL, json=payload)
    logging.info("Planner responded (req_id=%s) status=%s", req_id, resp.status_code)
    # Optionally log limited body on non-2xx
    if not resp.is_success:
        body = (await resp.aread())[:500]
        logging.error("Planner HTTP %s (req_id=%s): %r", resp.status_code, req_id, body)
    return resp.status_code

async def handle_message(msg: pubsub_v1.subscriber.message.Message):
    req_id = _req_id_for(msg)
    delivery_attempt = getattr(msg, "delivery_attempt", None)  # may be None on some setups
    if delivery_attempt is not None:
        logging.info("Received message req_id=%s (attempt=%s, msg_id=%s)", req_id, delivery_attempt, msg.message_id)
    else:
        logging.info("Received message req_id=%s (msg_id=%s)", req_id, msg.message_id)
    # Decode & validate JSON
    try:
        raw = msg.data or b""
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        data=json.loads(raw.decode("utf-8").strip())
        payload = {
        "request_id": data.get("request_id"),
        "patient_data": data.get("payload", {}),
        "batch_id": data.get("batch_id", {})
    }
        print(f"Deserialized request_id: {payload['request_id']}")
        print(f"Deserialized batch_id: {payload['batch_id']}")
        print(f"Deserialized payload: {payload['patient_data']}")
        logging.info(f"Deserialized request_id: {payload['request_id']}")
        logging.info(f"Deserialized payload: {payload['patient_data']}")
    except Exception as e:
        logging.error("Bad JSON → ACK to drop (req_id=%s): %s", req_id, e)
        msg.ack()
        return
    processed_key = f"processed:{req_id}"
    # 1) Fast-path dedupe: if already processed, ACK & skip
    if redis_client.get(processed_key):
        logging.info("Duplicate detected (already processed) → ACK (req_id=%s).", req_id)
        msg.ack()
        return
    # 2) Try to claim inflight lock so only one worker does the side-effect
    if not _claim_inflight(req_id):
        # Another worker is currently processing. ack so Pub/Sub can redeliver later if needed.
        logging.info("Another worker holds inflight lock → ack (req_id=%s).", req_id)
        msg.ack()
        return
    # 3) Perform side-effect (call Planner) and ACK only on success
    try:
        status = await call_planner(payload, req_id)
        logging.info(f"after planner beign called : {status}")
        if 200 <= status < 300:
            _mark_processed(req_id)
            msg.ack()
            logging.info("Planner success → processed+ACK (req_id=%s).", req_id)
        else:
            # transient/non-2xx → clear lock & ack to retry
            msg.ack()
            logging.warning("Planner non-success → ack for retry (req_id=%s, status=%s).", req_id, status)
    except (httpx.TimeoutException, httpx.NetworkError) as e:
        msg.ack()
        logging.error("Planner dispatch network/timeout → ack (req_id=%s): %s", req_id, e)
    except Exception as e:
        msg.ack()
        logging.error("Planner dispatch failed → ack (req_id=%s): %s (%s)", req_id, e, type(e).__name__)
    finally:
        _clear_inflight(req_id)

def run():
    if not PROJECT_ID or not SUBSCRIPTION_ID:
        raise SystemExit("Set GOOGLE_CLOUD_PROJECT and PUBSUB_SUBSCRIPTION env vars.")
    if not PROCESSOR_URL or not (PROCESSOR_URL.startswith("http://") or PROCESSOR_URL.startswith("https://")):
        raise SystemExit(f"Invalid PROCESSOR_URL: '{PROCESSOR_URL}'. Must start with http:// or https://")
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    flow = pubsub_v1.types.FlowControl(max_messages=MAX_MESSAGES, max_bytes=MAX_BYTES)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stop_event = asyncio.Event()
    def stop_handler(*_):
        logging.info("Shutdown signal received.")
        stop_event.set()
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, stop_handler)
        except Exception:
            pass
    def callback(message: pubsub_v1.subscriber.message.Message):
        # Schedule the coroutine on the event loop so the streaming pull
        # can keep extending the lease while we await the HTTP call.
        asyncio.run_coroutine_threadsafe(handle_message(message), loop)
    future = subscriber.subscribe(sub_path, callback=callback, flow_control=flow)
    logging.info("Subscribed to %s (ACK-after-success with Redis dedupe) → %s", sub_path, PROCESSOR_URL)
    async def _main():
        try:
            await stop_event.wait()
        finally:
            future.cancel()
            await asyncio.sleep(1)  # let in-flight callbacks settle
            global _http_client
            if _http_client:
                await _http_client.aclose()
    try:
        loop.run_until_complete(_main())
    finally:
        subscriber.close()
        loop.close()

if __name__ == "__main__":
    run()