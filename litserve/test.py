import asyncio
import socketio
import time
import json
from collections import defaultdict

NUM_REQUESTS = 100  # tổng số request gửi
CONCURRENT_CLIENTS = 10  # số client socket kết nối song song
SERVER_URL = 'http://127.0.0.1:5001'

# Thống kê
stats = {
    "total_sent": 0,
    "total_received": 0,
    "start_time": None,
    "end_time": None,
    "per_second": defaultdict(int),
}

# Payload mẫu
payload = {
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


async def run_client(index):
    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        stats["total_sent"] += 1
        ts = int(time.time())
        stats["per_second"][ts] += 1
        await sio.emit("predict", payload)

    @sio.on("result")
    async def on_result(data):
        stats["total_received"] += 1
        await sio.disconnect()

    @sio.event
    async def disconnect():
        pass

    try:
        await sio.connect(SERVER_URL)
        await sio.wait()
    except Exception as e:
        print(f"[Client {index}] 🚨 Error: {e}")


async def main():
    stats["start_time"] = time.time()

    tasks = []
    for i in range(NUM_REQUESTS):
        task = asyncio.create_task(run_client(i))
        tasks.append(task)

        # Giới hạn số client cùng lúc
        if (i + 1) % CONCURRENT_CLIENTS == 0:
            await asyncio.gather(*tasks)
            tasks = []

    if tasks:
        await asyncio.gather(*tasks)

    stats["end_time"] = time.time()

    duration = stats["end_time"] - stats["start_time"]
    total = stats["total_received"]
    rpm = total / (duration / 60)
    rps = total / duration

    print("\n====== 📊 PERFORMANCE REPORT ======")
    print(f"⏱ Duration: {duration:.2f} seconds")
    print(f"📤 Total Requests Sent: {stats['total_sent']}")
    print(f"📥 Total Responses Received: {stats['total_received']}")
    print(f"⚡ Requests/sec: {rps:.2f}")
    print(f"🚀 Requests/min: {rpm:.2f}")
    print("📈 Per-second breakdown:")
    for sec, count in sorted(stats["per_second"].items()):
        print(f"  {time.strftime('%H:%M:%S', time.localtime(sec))}: {count} req")
    print("===================================")


if __name__ == '__main__':
    asyncio.run(main())
