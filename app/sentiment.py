from utils import sentiment_inference, check_targeting_topic

def analyze_sentiment(data_input, tokenizer, config, model):
    """
    Hàm phân tích sentiment của nội dung đầu vào.
    Trả về label sentiment và thông tin cơ bản.
    """
    text = data_input['type'] + ' ' + data_input.get('content', '') + ' ' + data_input.get('description', '')
    input_type = data_input.get('type', '')
    title = data_input.get('title', '')
    site_name = data_input.get('siteName', '')
    is_kol = data_input.get("is_kol", False)
    total_interactions = data_input.get("total_interactions", 0)

    ref_list, top_label = sentiment_inference(text, tokenizer, config, model)
    label = top_label if top_label else None

    # Kết quả cơ bản
    result = {
        "log_level": 0,
        "reason": "Không phải nội dung tiêu cực.",
        "id": data_input.get('id', ''),
        "topic_id": data_input.get('topic_id', ''),
        "topic_name": data_input.get('topic_name', ''),
        "site_id": data_input.get('siteId', ''),
        "site_name": site_name,
        "title": title,
        "description": data_input.get('description', ''),
        "content": data_input.get('content', ''),
        "input_type": input_type,
        "sentiment": label,
        "contains_topic": False,
        "targeting_topic": False,
        "crisis_keywords": [],
        "is_kol": is_kol,
        "total_interactions": total_interactions,
    }

    return result, label

def filter_negative_content(data_input, result):
    """
    Hàm lọc nội dung tiêu cực, chỉ gọi khi sentiment là negative.
    """
    array_type_comment = [
        "FBPAGE_COMMENT", "FBGROUP_COMMENT", "FBUSER_COMMENT", "FORUM_COMMENT",
        "NEWS_COMMENT", "YOUTUBE_COMMENT", "BLOG_COMMENT", "QA_COMMENT",
        "SNS_COMMENT", "TIKTOK_COMMENT", "LINKEDIN_COMMENT", "ECOMMERCE_COMMENT"
    ]

    array_type_post = [
        "FBPAGE_TOPIC", "FBGROUP_TOPIC", "FBUSER_TOPIC", "FORUM_TOPIC", "NEWS_TOPIC",
        "YOUTUBE_TOPIC", "BLOG_TOPIC", "QA_TOPIC", "SNS_TOPIC", "TIKTOK_TOPIC",
        "LINKEDIN_TOPIC", "ECOMMERCE_TOPIC"
    ]

    input_type = data_input.get('type', '')
    is_kol = data_input.get("is_kol", False)
    total_interactions = data_input.get("total_interactions", 0)
    reason = None

    # Level 1: Bình luận tiêu cực
    if input_type in array_type_comment:
        result.update({
            "log_level": 1,
            "reason": "Bình luận tiêu cực trên mạng xã hội."
        })
        return result

    # Là bài đăng (post)
    if input_type in array_type_post:
        topic_analysis = check_targeting_topic(data_input)

        targeting_topic = topic_analysis.get("targeting_topic", False)
        contains_topic = topic_analysis.get("contains_topic", False)
        crisis_keywords = topic_analysis.get("crisis_keywords", [])
        reason = topic_analysis.get("reason", [])

        result.update({
            "contains_topic": contains_topic,
            "targeting_topic": targeting_topic,
            "crisis_keywords": crisis_keywords
        })

        # Check điều kiện Level 3
        if targeting_topic and len(crisis_keywords) > 0:
            if "NEWS" in input_type or is_kol or total_interactions >= 100:
                result.update({
                    "log_level": 3,
                    "reason": reason
                })
                return result

        # Nếu không đủ Level 3 → Level 2
        result.update({
            "log_level": 2,
            "reason": reason
        })
        return result

    # Nếu không xác định rõ type → fallback
    result.update({
        "log_level": 2,
        "reason": reason
    })
    return result

def sentiment_filtering(data_input, tokenizer, config, model):
    """
    Hàm chính gọi sentiment và filter khi cần.
    """
    result, label = analyze_sentiment(data_input, tokenizer, config, model)

    if label == 'negative':
        result = filter_negative_content(data_input, result)

    return result