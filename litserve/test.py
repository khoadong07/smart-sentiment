import socketio
import threading
import time
from collections import defaultdict

# Cấu hình
SERVER_URL = 'http://127.0.0.1:5001'
MAX_REQUESTS = 600
DURATION = 60  # giây
RPS_LIMIT = MAX_REQUESTS // DURATION  # ~10 req/s

# Thống kê
success_count = 0
fail_count = 0
lock = threading.Lock()
per_second_counter = defaultdict(int)

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
        print(f"🚨 Error: {e}")

def run_limited_requests():
    print(f"🚀 Sending max {MAX_REQUESTS} requests in {DURATION} seconds (~{RPS_LIMIT}/s)...\n")
    start_time = time.time()

    for i in range(MAX_REQUESTS):
        threading.Thread(target=send_request).start()

        # Giới hạn tốc độ gửi ~10 req/s
        time.sleep(1.0 / RPS_LIMIT)

    # Đợi thêm 5s để các request xử lý xong
    time.sleep(5)

    print(f"\n✅ Total success: {success_count}")
    print(f"❌ Total failed: {fail_count}")
    print("📊 Requests per second:")
    for sec in sorted(per_second_counter):
        print(f"  🕒 {time.strftime('%H:%M:%S', time.localtime(sec))}: {per_second_counter[sec]}")

if __name__ == '__main__':
    run_limited_requests()
