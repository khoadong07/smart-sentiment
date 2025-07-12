import socketio
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

SERVER_URL = 'http://127.0.0.1:5001'
MAX_CONCURRENCY = 500  # giới hạn socket mở đồng thời
TEST_DURATION = 60  # giây

# Thống kê
success_count = 0
fail_count = 0
per_second_counter = defaultdict(int)
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

def send_request():
    global success_count, fail_count
    sio = socketio.Client()

    def on_result(data):
        nonlocal sio
        ts = int(time.time())
        with lock:
            success_count += 1
            per_second_counter[ts] += 1
        sio.disconnect()

    try:
        sio.on('result', on_result)
        sio.connect(SERVER_URL)
        sio.emit('predict', sample_data)
        sio.wait()
    except Exception as e:
        with lock:
            fail_count += 1
        try:
            sio.disconnect()
        except:
            pass

def run_test_60s():
    print(f"🚀 Running test for {TEST_DURATION} seconds with max {MAX_CONCURRENCY} concurrent sockets...\n")
    start_time = time.time()
    end_time = start_time + TEST_DURATION

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        while time.time() < end_time:
            executor.submit(send_request)

    # Chờ thêm 5s cho các request xử lý xong
    time.sleep(5)

    print(f"\n✅ Total success in {TEST_DURATION} seconds: {success_count}")
    print(f"❌ Total failed: {fail_count}")
    print("📊 Requests per second:")
    for sec in sorted(per_second_counter):
        print(f"  🕒 {time.strftime('%H:%M:%S', time.localtime(sec))}: {per_second_counter[sec]}")

if __name__ == '__main__':
    run_test_60s()
