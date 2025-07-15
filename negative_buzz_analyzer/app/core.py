from typing import Dict
from app.llm import check_targeting_topic

array_type_comment = [
    "fbPageComment", "fbGroupComment", "fbUserComment", "forumComment",
    "newsComment", "youtubeComment", "tiktokComment", "snsComment",
    "linkedinComment", "ecommerceComment", "threadsComment"
]

array_type_post = [
    "fbPageTopic", "fbGroupTopic", "fbUserTopic", "forumTopic",
    "newsTopic", "youtubeTopic", "tiktokTopic", "snsTopic",
    "linkedinTopic", "ecommerceTopic", "threadsTopic"
]

async def filter_negative_content(data_input: Dict, result: Dict) -> Dict:
    """
    Hàm lọc nội dung tiêu cực, chỉ gọi khi sentiment là negative.
    """
    input_type = data_input.get('type', '')
    is_kol = data_input.get("is_kol", False)
    total_interactions = data_input.get("total_interactions", 0)

    # Mặc định fallback
    result.update({
        "contains_topic": False,
        "targeting_topic": False,
        "crisis_keywords": [],
        "log_level": 2,
        "should_call_llm": False
    })

    # Level 1: Bình luận tiêu cực
    if input_type in array_type_comment:
        result.update({
            "log_level": 1,
            "reason": "Bình luận tiêu cực trên mạng xã hội.",
            "should_call_llm": False
        })
        return result

    # Level 2-3: Là bài đăng
    if input_type in array_type_post:
        result["should_call_llm"] = True
        try:
            topic_analysis = await check_targeting_topic(data_input)
        except Exception as e:
            result.update({
                "reason": f"Lỗi khi gọi LLM: {str(e)}",
                "log_level": 2
            })
            return result

        targeting_topic = topic_analysis.get("targeting_topic", False)
        contains_topic = topic_analysis.get("contains_topic", False)
        crisis_keywords = topic_analysis.get("crisis_keywords", [])
        reason = topic_analysis.get("reason", "Không rõ lý do.")

        result.update({
            "contains_topic": contains_topic,
            "targeting_topic": targeting_topic,
            "crisis_keywords": crisis_keywords,
            "reason": reason
        })

        # Level 3: targeting + crisis keywords + high impact
        if targeting_topic and crisis_keywords:
            if "news" in input_type.lower() or is_kol or total_interactions >= 100:
                result.update({
                    "log_level": 3
                })
                return result

        # Level 2: targeting không rõ ràng hoặc impact thấp
        result.update({
            "log_level": 2
        })
        return result

    # Không rõ type
    return result
