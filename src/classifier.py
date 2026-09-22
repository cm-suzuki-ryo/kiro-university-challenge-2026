"""RSS アイテムの AWS サービスカテゴリ分類"""
import logging
import re

from fetcher import FeedItem

logger = logging.getLogger(__name__)

# RSS category フィールドから主要サービス名を正規化するマッピング
_CATEGORY_MAP: dict[str, str] = {
    "amazon-s3": "Amazon S3",
    "amazon-ec2": "Amazon EC2",
    "aws-lambda": "AWS Lambda",
    "amazon-rds": "Amazon RDS",
    "amazon-dynamodb": "Amazon DynamoDB",
    "amazon-cloudfront": "Amazon CloudFront",
    "amazon-vpc": "Amazon VPC",
    "aws-iam": "AWS IAM",
    "amazon-cloudwatch": "Amazon CloudWatch",
    "amazon-sns": "Amazon SNS",
    "amazon-sqs": "Amazon SQS",
    "amazon-bedrock": "Amazon Bedrock",
    "amazon-q": "Amazon Q",
    "aws-kiro": "Kiro",
}


def classify(item: FeedItem) -> str:
    """
    FeedItem の category フィールドからサービスカテゴリを返す。
    マッピングにない場合はカテゴリをそのまま正規化して返す。
    """
    raw = item.category.strip().lower()

    if not raw:
        logger.debug("Item '%s' has no category, using 'uncategorized'", item.title[:50])
        return "uncategorized"

    if raw in _CATEGORY_MAP:
        return _CATEGORY_MAP[raw]

    # kebab-case → Title Case にフォールバック
    normalized = re.sub(r"[-_]", " ", raw).title()
    logger.debug("Item '%s' classified as '%s' (fallback)", item.title[:50], normalized)
    return normalized
