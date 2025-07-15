import requests

url = "http://localhost:8008/predict"
data = {
    "text": "Sản phẩm này thực sự rất tốt và tôi sẽ mua lại!"
}

res = requests.post(url, json=data)
print(res.json())
