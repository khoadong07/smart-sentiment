import socketio

sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")
    sio.emit('predict', {
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
    })

@sio.event
def disconnect():
    print("❌ Disconnected from server")

@sio.on('result')
def on_result(data):
    print("📥 Received result:")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
    sio.disconnect()

if __name__ == '__main__':
    try:
        sio.connect('http://0.0.0.0:5001')
        sio.wait()
    except Exception as e:
        print(f"🚨 Connection error: {e}")
