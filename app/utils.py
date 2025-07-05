import torch
import numpy as np
from settings import Settings
import json
import requests

settings = Settings()
def sentiment_inference(text: str, tokenizer, config, model):
    # Label mapping
    label_mapping = {
        'POS': 'positive',
        'NEG': 'negative',
        'NEU': 'neutral'
    }

    # Tokenize input
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    input_ids = inputs["input_ids"]

    # Inference
    with torch.no_grad():
        outputs = model(input_ids)
        scores = outputs.logits.softmax(dim=-1).cpu().numpy()[0]

    # Process results
    ranking = np.argsort(scores)[::-1]
    result = {}
    for i in range(len(scores)):
        original_label = config.id2label[ranking[i]]
        mapped_label = label_mapping.get(original_label, original_label.lower())
        score = scores[ranking[i]]
        result[mapped_label] = np.round(float(score), 4)

    # Top label
    top_original_label = config.id2label[ranking[0]]
    top_label = label_mapping.get(top_original_label, top_original_label.lower())

    # Convert to list format
    ref_list = [{"label": label, "confidence": confidence} for label, confidence in result.items()]

    return ref_list, top_label


def check_targeting_topic(data: dict) -> dict:
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


    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": settings.GEMINI_API_KEY
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt.strip()
                            }
                        ]
                    }
                ]
            }
        )
        response.raise_for_status()

        raw_output = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        # Tách phần JSON trong chuỗi
        json_start = raw_output.find("{")
        json_end = raw_output.rfind("}") + 1
        json_str = raw_output[json_start:json_end]

        result = json.loads(json_str)

        # Đảm bảo đúng định dạng
        default_result = {
            "contains_topic": False,
            "targeting_topic": False,
            "reason": "Không xác định hoặc lỗi đầu ra."
        }

        for key in default_result:
            if key not in result:
                result[key] = default_result[key]

        result["contains_topic"] = bool(result["contains_topic"])
        result["targeting_topic"] = bool(result["targeting_topic"])
        result["reason"] = str(result["reason"])

        return result

    except Exception as e:
        return {
            "contains_topic": False,
            "targeting_topic": False,
            "reason": f"Lỗi xử lý đầu ra từ Gemini: {str(e)}"
        }