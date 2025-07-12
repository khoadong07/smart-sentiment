import socketio
import threading
import time
from collections import defaultdict

# Config
SERVER_URL = 'http://127.0.0.1:5001'
DURATION = 60  # chạy trong 60 giây

# Thống kê
success_count = 0
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

def send_and_track():
    global success_count
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
        print(f"🚨 Error: {e}")

def run_test():
    print(f"🚀 Start stress test for {DURATION} seconds...\n")
    start_time = time.time()
    end_time = start_time + DURATION

    def spam_requests():
        while time.time() < end_time:
            threading.Thread(target=send_and_track).start()

    spam_thread = threading.Thread(target=spam_requests)
    spam_thread.start()
    spam_thread.join()

    # Đợi thêm vài giây cho các request xử lý xong
    time.sleep(5)

    # Tổng kết
    print(f"\n✅ Total successful requests in {DURATION}s: {success_count}")
    print("📊 Requests per second:")
    for sec in sorted(per_second_counter):
        print(f"  🕒 {time.strftime('%H:%M:%S', time.localtime(sec))}: {per_second_counter[sec]}")

if __name__ == '__main__':
    run_test()
