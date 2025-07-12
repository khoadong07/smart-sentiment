import requests
import time
import threading

URL = "http://148.113.213.217:8990/predict"
HEADERS = {"Content-Type": "application/json"}
PAYLOAD = {"text": "cũng tạm tạm"}

SUCCESS_COUNT = 0
FAIL_COUNT = 0
LOCK = threading.Lock()

def send_request():
    global SUCCESS_COUNT, FAIL_COUNT
    try:
        res = requests.post(URL, json=PAYLOAD, timeout=5)
        if res.status_code == 200:
            with LOCK:
                SUCCESS_COUNT += 1
        else:
            with LOCK:
                FAIL_COUNT += 1
    except Exception:
        with LOCK:
            FAIL_COUNT += 1

def run_for_duration(duration_seconds=60, concurrency=10):
    global SUCCESS_COUNT, FAIL_COUNT
    start_time = time.time()
    threads = []

    while time.time() - start_time < duration_seconds:
        for _ in range(concurrency):
            t = threading.Thread(target=send_request)
            t.start()
            threads.append(t)
        time.sleep(0.1)  # Giảm overload CPU

    for t in threads:
        t.join()

    print(f"\n⏱️  Test duration: {duration_seconds} seconds")
    print(f"✅ Successful requests: {SUCCESS_COUNT}")
    print(f"❌ Failed requests:     {FAIL_COUNT}")
    print(f"📊 Total requests:      {SUCCESS_COUNT + FAIL_COUNT}")
    print(f"⚡ Throughput:          {SUCCESS_COUNT / duration_seconds:.2f} req/s")

if __name__ == "__main__":
    run_for_duration(duration_seconds=60, concurrency=5)
