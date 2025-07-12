import socketio
import time
import threading

# Config
NUM_REQUESTS = 100
CONCURRENCY = 10
SERVER_URL = 'http://127.0.0.1:5001'

# Shared counters
success_count = 0
fail_count = 0
lock = threading.Lock()

sample_data = {
    "data": [{
        "id": "7521631307152084231_3",
        "topic_name": "Vinamilk",
        "type": "NEWS_TOPIC",
        "topic_id": "5cd2a99d2e81050a12e5339a",
        "siteId": "7427331267015197703",
        "siteName": "baothegioisua",
        "title": "Vinamilk dính nghi vấn lừa đảo cộng tác viên qua app nhập liệu",
        "content": "Nhiều người phản ánh bị treo tiền, không hoàn tiền khi làm cộng tác viên qua nền tảng app được cho là của Vinamilk. Một số nghi ngờ đây là hình thức lừa đảo tinh vi.",
        "description": "",
        "is_kol": False,
        "total_interactions": 57
    }]
}

def test_socket_request():
    sio = socketio.Client()

    def on_result(data):
        nonlocal sio
        global success_count
        with lock:
            success_count += 1
        sio.disconnect()

    try:
        sio.on('result', on_result)
        sio.connect(SERVER_URL)
        sio.emit('predict', sample_data)
        sio.wait()
    except Exception as e:
        global fail_count
        with lock:
            fail_count += 1
        print(f"🚨 Error: {e}")

def run_benchmark():
    global success_count, fail_count
    threads = []
    start_time = time.time()

    for i in range(NUM_REQUESTS):
        t = threading.Thread(target=test_socket_request)
        threads.append(t)
        t.start()

        # Giới hạn số luồng song song
        while threading.active_count() > CONCURRENCY:
            time.sleep(0.01)

    for t in threads:
        t.join()

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n⏱️ Total time: {duration:.2f} seconds")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed:  {fail_count}")
    print(f"📈 Throughput: {success_count / duration:.2f} req/s")

if __name__ == '__main__':
    run_benchmark()
