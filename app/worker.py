import redis
import json
from transformers import AutoTokenizer, AutoConfig, AutoModelForSequenceClassification
from wordcloud import generate_word_cloud
from settings import Settings
from sentiment import sentiment_filtering

settings = Settings()
redis_conn = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

REDIS_REQUEST_QUEUE = "sentiment_request_queue"
REDIS_RESULT_QUEUE = "sentiment_result_queue"

model_path = settings.MODEL
tokenizer = AutoTokenizer.from_pretrained(model_path)
config = AutoConfig.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Hàm inference chính
def predict_sentiment(data_input):
    try:
        if not isinstance(data_input, dict):
            raise ValueError("⚠️ Invalid input data")

        # Gọi hàm sentiment_filtering từ sentiment.py
        result = sentiment_filtering(data_input, tokenizer, config, model)
        return result

    except Exception as e:
        return {"error": str(e)}

# Worker loop
while True:
    try:
        packed = redis_conn.blpop(REDIS_REQUEST_QUEUE, timeout=5)
        if not packed:
            continue

        _, payload = packed
        task = json.loads(payload)

        job_id = task.get("job_id")
        data_input = task.get("data_input", {})
        meta = task.get("meta", {})

        print(f"📥 job_id={job_id} | id={meta.get('id')}")

        try:
            prediction = predict_sentiment(data_input)
            full_content = meta.get("title", "") + " " + meta.get("description", "") + " " + meta.get("content", "")
            result = {
                "id": meta.get("id", ""),
                "topic_name": meta.get("topic_name", ""),
                "topic_id": meta.get("topic_id", ""),
                "title": meta.get("title", ""),
                "content": meta.get("content", ""),
                "description": meta.get("description", ""),
                "site_name": meta.get("siteName", ""),
                "site_id": meta.get("siteId", ""),
                "type": meta.get("type", ""),
                "word_cloud": generate_word_cloud(full_content),
                **prediction
            }

            print(f"✅ job_id={job_id} | result={result}")

        except Exception as e:
            result = {"error": str(e)}
            print(f"❌ job_id={job_id} | Lỗi xử lý: {e}")
            print(f"📝 Data: {repr(data_input)}")

        redis_conn.rpush(REDIS_RESULT_QUEUE, json.dumps({
            "job_id": job_id,
            "result": result
        }))

    except Exception as e:
        print(f"🔥 Worker loop error: {e}")