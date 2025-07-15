import json
import httpx
from typing import Dict, List
from app.settings import Settings

settings = Settings()

async def check_targeting_topic(data: dict) -> dict:
    topic = data.get("topic_name", "")
    combined_text = " ".join([
        f"Title: {data.get('title', '')}",
        f"Description: {data.get('description', '')}",
        f"Content: {data.get('content', '')}"
    ])

    prompt = f"""
    Bạn là một chuyên gia phân tích nội dung mạng xã hội trong lĩnh vực truyền thông khủng hoảng.

    Dưới đây là một nội dung có sắc thái tiêu cực, bao gồm tiêu đề, mô tả và nội dung:

    {combined_text}

    Chủ đề cần kiểm tra là: "{topic}"

    Nhiệm vụ:
    1. Kiểm tra xem nội dung có **nhắc đến** chủ đề không?
    2. Nếu có, nội dung có đang **nhắm vào**, **công kích**, hoặc **quy trách nhiệm tiêu cực** cho chủ đề không?
    3. Nếu targeting_topic = true, hãy **trích xuất danh sách các từ/cụm từ tiêu cực có thể gây khủng hoảng**. Mỗi phần tử trong danh sách phải là:
      - Từ đơn (ví dụ: "lừa đảo")
      - Từ đôi (ví dụ: "mất tiền")
      - Tối đa 3 từ (ví dụ: "không hoàn tiền")
      - Tuyệt đối không phải là câu dài hay mô tả.

    Trả về JSON hợp lệ với cấu trúc sau:
    {{
      "contains_topic": true/false,
      "targeting_topic": true/false,
      "reason": "giải thích ngắn gọn (1 câu)",
      "crisis_keywords": ["từ khóa 1", "từ khóa 2", ...]
    }}

    ⚠️ Ghi nhớ:
    - Nếu chỉ nhắc chủ đề trong hashtag hoặc không liên quan trực tiếp tới hành vi tiêu cực → targeting_topic = false.
    - Nếu targeting_topic = false thì crisis_keywords là mảng rỗng []
    - Luôn đảm bảo crisis_keywords là list, các phần tử không dài quá 3 từ.

    Chỉ trả về JSON hợp lệ. Không ghi thêm bất kỳ văn bản nào khác.
    """

    messages = [
        {"role": "user", "content": prompt.strip()}
    ]

    headers = {
        "Authorization": f"Bearer {settings.FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "fireworks-playground": "true",
    }

    payload = {
        "model": "accounts/fireworks/models/llama4-scout-instruct-basic",
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.6,
        "top_p": 1,
        "top_k": 40,
        "n": 1,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "stream": False,
        "echo": False,
        "logprobs": True
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.fireworks.ai/inference/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            json_str = content[json_start:json_end]
            result = json.loads(json_str)

            default_result = {
                "contains_topic": False,
                "targeting_topic": False,
                "reason": "Không xác định hoặc lỗi đầu ra.",
                "crisis_keywords": []
            }

            for key in default_result:
                if key not in result:
                    result[key] = default_result[key]

            result["contains_topic"] = bool(result["contains_topic"])
            result["targeting_topic"] = bool(result["targeting_topic"])
            result["reason"] = str(result["reason"])
            if not isinstance(result.get("crisis_keywords", []), list):
                result["crisis_keywords"] = []

            return result

    except Exception as e:
        return {
            "contains_topic": False,
            "targeting_topic": False,
            "reason": f"Lỗi xử lý từ Fireworks: {str(e)}",
            "crisis_keywords": []
        }
