import redis
import json
import multiprocessing
from transformers import AutoTokenizer, AutoConfig, AutoModelForSequenceClassification
from wordcloud import generate_word_cloud
from settings import Settings
from sentiment import sentiment_filtering
from huggingface_hub import snapshot_download

settings = Settings()

def get_redis_connection():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )

# Load model
model_path = settings.MODEL
local_dir = snapshot_download(repo_id=model_path, local_dir="./models")
tokenizer = AutoTokenizer.from_pretrained(local_dir)
config = AutoConfig.from_pretrained(local_dir)
model = AutoModelForSequenceClassification.from_pretrained(local_dir)

REDIS_REQUEST_QUEUE = "sentiment_request_queue"
REDIS_RESULT_QUEUE = "sentiment_result_queue"

def predict_sentiment(data_input):
    try:
        if not isinstance(data_input, dict):
            raise ValueError("⚠️ Invalid input data")

        result = sentiment_filtering(data_input, tokenizer, config, model)
        full_text = ' '.join(filter(None, [
            data_input.get("title", ""),
            data_input.get("content", ""),
            data_input.get("description", "")
        ]))
        word_cloud_items = generate_word_cloud(full_text)
        word_cloud = [{"word": wc.word, "frequency": wc.frequency} for wc in word_cloud_items]

        return result, word_cloud
    except Exception as e:
        return {"error": str(e)}, []

def worker_process():
    redis_conn = get_redis_connection()
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

            prediction, word_cloud = predict_sentiment(data_input)
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
                **prediction,
                "word_cloud": word_cloud
            }

            print(f"✅ job_id={job_id} | result={result}")
            redis_conn.rpush(REDIS_RESULT_QUEUE, json.dumps({
                "job_id": job_id,
                "result": result
            }))

        except Exception as e:
            result = {
                "id": meta.get("id", ""),
                "error": str(e),
                "word_cloud": []
            }
            print(f"❌ job_id={job_id} | Error: {e}")
            redis_conn.rpush(REDIS_RESULT_QUEUE, json.dumps({
                "job_id": job_id,
                "result": result
            }))

if __name__ == "__main__":
    num_processes = multiprocessing.cpu_count()*0.8
    # convert num_processes to int
    num_processes = int(num_processes)

    print(f"Starting {num_processes} worker processes...")
    processes = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker_process)
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Shutting down...")
        for p in processes:
            p.terminate()