import socketio
import requests
import re
from pyvi import ViTokenizer
from typing import List
from pydantic import BaseModel

class WordCloudResponse(BaseModel):
    word: str
    frequency: int

def generate_word_cloud(content: str) -> List[dict]:
    tokenized_content = ViTokenizer.tokenize(content)
    words = re.findall(r'\w+', tokenized_content.lower())
    meaningful_words = [word for word in words if '_' in word]

    word_cloud_dict = {}
    for word in meaningful_words:
        if word not in word_cloud_dict:
            word_cloud_dict[word] = 1
        else:
            word_cloud_dict[word] += 1

    word_cloud = [WordCloudResponse(word=word, frequency=word_cloud_dict[word]) for word in meaningful_words if
                  word in word_cloud_dict]

    seen = set()
    ordered_word_cloud = []
    for item in word_cloud:
        if item.word not in seen:
            ordered_word_cloud.append(item)
            seen.add(item.word)

    ordered_word_cloud.sort(key=lambda x: x.frequency, reverse=True)

    # 🔁 Trả về danh sách dict để tránh lỗi serialize
    return [item.dict() for item in ordered_word_cloud]


# Create Socket.IO async server
sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='aiohttp')
from aiohttp import web
app = web.Application()
sio.attach(app)

PREDICT_API_URL = "http://0.0.0.0:9000/predict"

# Function to call inference API
def call_inference(text: str):
    try:
        response = requests.post(
            PREDICT_API_URL,
            json={"text": text},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("predicted_label", "neutral").lower()
        else:
            return "neutral"
    except Exception as e:
        print(f"Error calling inference: {e}")
        return "neutral"

@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)

@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)

@sio.event
async def predict(sid, data):
    print("Received predict event")
    results = []

    for item in data.get("data", []):
        text = f"{item.get('title', '')} {item.get('description', '')} {item.get('content', '')}"
        print(text)

        sentiment = call_inference(text)
        words_cloud = generate_word_cloud(text)
        print(words_cloud)
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
            "word_cloud": words_cloud
        }

        results.append(result)

    await sio.emit('result', {'results': results}, to=sid)

# Run aiohttp app
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5001)
