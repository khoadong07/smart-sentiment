import socketio
from aiohttp import web
import asyncio
import json
import redis
import uuid

from settings import Settings

settings = Settings()

redis_conn = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)
REDIS_REQUEST_QUEUE = "sentiment_request_queue"
REDIS_RESULT_QUEUE = "sentiment_result_queue"

# Socket.IO setup
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Đẩy request vào Redis queue
async def enqueue_request(data_input, meta):
    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "data_input": data_input,
        "meta": meta
    }
    redis_conn.rpush(REDIS_REQUEST_QUEUE, json.dumps(payload))
    return job_id

# Đợi kết quả từ Redis
async def wait_for_result(job_id, timeout=5):
    for _ in range(timeout * 10):  # Kiểm tra mỗi 100ms
        results = redis_conn.lrange(REDIS_RESULT_QUEUE, 0, -1)
        for item in results:
            obj = json.loads(item)
            if obj.get("job_id") == job_id:
                redis_conn.lrem(REDIS_RESULT_QUEUE, 1, item)
                return obj["result"]
        await asyncio.sleep(0.1)
    return {"error": "Timeout"}

# Socket events
@sio.event
async def connect(sid, environ):
    print(f"✅ Client {sid} connected")

@sio.event
async def disconnect(sid):
    print(f"❌ Client {sid} disconnected")

@sio.event
async def predict(sid, data):
    items = data.get("data", [])
    results = []

    for item in items:
        # Tạo data_input theo cấu trúc cần thiết
        data_input = {
            "id": item.get("id", ""),
            "topic_name": item.get("topic_name", ""),
            "type": item.get("type", ""),
            "topic_id": item.get("topic_id", ""),
            "site_id": item.get("siteId", ""),
            "site_name": item.get("siteName", ""),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "description": item.get("description", ""),
            "is_kol": item.get("is_kol", False),
            "total_interactions": item.get("total_interactions", None)
        }

        if not data_input["title"] and not data_input["content"] and not data_input["description"]:
            results.append({
                "id": item.get("id"),
                "error": "Empty text"
            })
            continue

        job_id = await enqueue_request(data_input, {
            "id": item.get("id"),
            "topic_name": item.get("topic_name", ""),
            "topic_id": item.get("topic_id", ""),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "description": item.get("description", ""),
            "siteName": item.get("siteName", ""),
            "siteId": item.get("siteId", ""),
            "type": item.get("type", "")
        })

        result = await wait_for_result(job_id)
        result.update({
            "id": item.get("id"),
            "topic_name": item.get("topic_name", "")
        })
        results.append(result)

    await sio.emit("result", {"results": results}, to=sid)

# Run the app
if __name__ == '__main__':
    web.run_app(app, port=5001)