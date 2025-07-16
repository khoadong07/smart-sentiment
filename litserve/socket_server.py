import socketio
from fastapi import FastAPI
import requests
import re
from pyvi import ViTokenizer
from pydantic import BaseModel
from typing import List

# -------------------------
# Khai báo SIO + FastAPI app
# -------------------------
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
fastapi_app = FastAPI()
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# -------------------------
# Word cloud xử lý
# -------------------------
class WordCloudResponse(BaseModel):
    word: str
    frequency: int

def generate_word_cloud(content: str) -> List[dict]:
    tokenized_content = ViTokenizer.tokenize(content)
    words = re.findall(r'\w+', tokenized_content.lower())
    meaningful_words = [word for word in words if '_' in word]

    freq = {}
    for word in meaningful_words:
        freq[word] = freq.get(word, 0) + 1

    seen = set()
    word_cloud = []
    for word in meaningful_words:
        if word not in seen:
            seen.add(word)
            word_cloud.append(WordCloudResponse(word=word, frequency=freq[word]))

    word_cloud.sort(key=lambda x: x.frequency, reverse=True)
    return [item.dict() for item in word_cloud]

# -------------------------
# Gọi API sentiment
# -------------------------
PREDICT_API_URL = "http://0.0.0.0:8989/predict"

def call_inference(text: str) -> str:
    try:
        response = requests.post(PREDICT_API_URL, json={"text": text}, timeout=5)
        if response.status_code == 200:
            return response.json().get("predicted_label", "neutral").lower()
        return "neutral"
    except Exception as e:
        print(f"❌ Error calling inference: {e}")
        return "neutral"

# -------------------------
# Socket.IO events
# -------------------------
@sio.event
async def connect(sid, environ):
    print(f"✅ Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"⚠️ Client disconnected: {sid}")

@sio.event
async def predict(sid, data):
    print("📩 Received predict event")
    results = []

    for item in data.get("data", []):
        text = f"{item.get('title', '')} {item.get('description', '')} {item.get('content', '')}"
        sentiment = call_inference(text)
        word_cloud = generate_word_cloud(text)

        result = {
            "id": item.get("id", ""),
            "topic_name": item.get("topic_name", ""),
            "topic_id": item.get("topic_id", ""),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "description": item.get("description", ""),
            "site_name": item.get("siteName", ""),
            "site_id": item.get("siteId", ""),
            "type": item.get("type", ""),
            "log_level": None,
            "reason": "",
            "input_type": item.get("type", ""),
            "sentiment": sentiment,
            "contains_topic": False,
            "targeting_topic": False,
            "crisis_keywords": [],
            "is_kol": item.get("is_kol", False),
            "total_interactions": item.get("total_interactions", 0),
            "word_cloud": word_cloud
        }

        results.append(result)

    await sio.emit('result', {'results': results}, to=sid)
