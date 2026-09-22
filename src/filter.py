"""フィルタリングロジック"""
import logging
from dataclasses import dataclass

from fetcher import FeedItem

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    passed: bool
    reason: str = ""


def _is_region_expansion(item: FeedItem, config: dict) -> bool:
    """リージョン追加系のアナウンスかどうか判定する"""
    rc = config.get("region_expansion", {})
    if not rc.get("enabled", False):
        return False

    text = (item.title + " " + item.description_plain).lower()
    patterns = [p.lower() for p in rc.get("patterns", [])]

    if not any(p in text for p in patterns):
        return False

    allow_regions = [r.lower() for r in rc.get("allow_regions", [])]
    return not any(r in text for r in allow_regions)


def evaluate(item: FeedItem, config: dict) -> FilterResult:
    """
    フィルタ設定に従いアイテムを評価する。
    除外すべき場合は passed=False と理由を返す。
    """
    category_lower = item.category.lower()
    title_lower = item.title.lower()
    full_text = (item.title + " " + item.description_plain).lower()

    # カテゴリ除外
    for exc in config.get("exclude_categories", []):
        if exc.lower() in category_lower:
            return FilterResult(passed=False, reason=f"exclude_category: {exc}")

    # キーワード除外（タイトルのみ）
    for kw in config.get("exclude_keywords", []):
        if kw.lower() in title_lower:
            return FilterResult(passed=False, reason=f"exclude_keyword: {kw}")

    # リージョン追加系除外
    if _is_region_expansion(item, config):
        return FilterResult(passed=False, reason="region_expansion (non-allow region)")

    # 高額サービス除外
    for exp in config.get("exclude_expensive", []):
        if exp.lower() in full_text:
            return FilterResult(passed=False, reason=f"exclude_expensive: {exp}")

    return FilterResult(passed=True)


def apply_filter(items: list[FeedItem], config: dict) -> tuple[list[FeedItem], list[dict]]:
    """
    アイテムリストにフィルタを適用し、
    (通過したアイテムリスト, 除外されたアイテムの詳細リスト) を返す。
    """
    passed: list[FeedItem] = []
    excluded: list[dict] = []

    for item in items:
        result = evaluate(item, config)
        if result.passed:
            passed.append(item)
            logger.debug("PASS: %s", item.title[:60])
        else:
            excluded.append({"title": item.title, "reason": result.reason})
            logger.debug("SKIP: %s — %s", item.title[:60], result.reason)

    logger.info("Filter result: %d passed, %d excluded", len(passed), len(excluded))
    return passed, excluded
