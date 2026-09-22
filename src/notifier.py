"""Amazon SNS への通知"""
import json
import logging
from typing import Any

import botocore.exceptions

from fetcher import FeedItem

logger = logging.getLogger(__name__)


def build_message(item: FeedItem, summary: str) -> str:
    """SNS に publish するメッセージ JSON を構築する"""
    payload = {
        "title": item.title,
        "summary": summary,
        "link": item.link,
        "pub_date": item.pub_date,
        "service_category": item.service_category,
    }
    return json.dumps(payload, ensure_ascii=False)


def publish(
    sns_client: Any,
    topic_arn: str,
    item: FeedItem,
    summary: str,
) -> bool:
    """
    SNS トピックにメッセージを publish する。
    成功したら True、失敗したら False を返す（例外は上位へ伝播させない）。
    """
    message = build_message(item, summary)
    subject = item.title[:100]  # SNS subject は 100 文字制限

    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject,
        )
        message_id = response.get("MessageId", "unknown")
        logger.info("Published to SNS: MessageId=%s title='%s'", message_id, item.title[:50])
        return True

    except botocore.exceptions.ClientError as e:
        logger.error(
            "SNS publish failed for '%s': %s",
            item.title[:50],
            e.response["Error"]["Message"],
        )
        return False
