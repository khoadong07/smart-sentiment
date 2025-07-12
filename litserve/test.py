import socketio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import threading

SERVER_URL = 'http://127.0.0.1:5001'
MAX_REQUESTS = 600
MAX_CONCURRENCY = 100  # ✨ giới hạn tối đa socket mở đồng thời
RPS_LIMIT = MAX_REQUESTS // 60

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
        with lock:
            success_count += 1
            per_second_counter[int(time.time())] += 1
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
        try:
            sio.disconnect()
        except:
            pass

def run_test():
    print(f"🚀 Sending {MAX_REQUESTS} requests with max {MAX_CONCURRENCY} concurrent sockets\n")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        futures = [executor.submit(send_request) for _ in range(MAX_REQUESTS)]
        for future in as_completed(futures):
            pass  # có thể xử lý result nếu cần

    duration = time.time() - start_time
    print(f"\n✅ Success: {success_count}")
    print(f"❌ Failed:  {fail_count}")
    print(f"⏱️ Duration: {duration:.2f}s")
    print(f"📈 Avg throughput: {success_count / duration:.2f} req/s")
    print("📊 Requests per second:")
    for sec in sorted(per_second_counter):
        print(f"  🕒 {time.strftime('%H:%M:%S', time.localtime(sec))}: {per_second_counter[sec]}")

if __name__ == '__main__':
    run_test()
