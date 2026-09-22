"""AWS What's New Notifier — メインエントリーポイント"""
import argparse
import logging
import sys
from pathlib import Path

import boto3
import yaml

import classifier
import fetcher
import filter as filter_mod
import notifier
import state
import summarizer

DEFAULT_CONFIG_PATH = Path("config/filter_config.yaml")
DEFAULT_STATE_PATH = Path("state/seen.json")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
        stream=sys.stderr,
    )


def load_config(config_path: Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="AWS What's New Notifier")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="フィルタ設定 YAML ファイルのパス",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="既読状態ファイルのパス",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="SNS publish と state 更新を行わない",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="デバッグログを出力する",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # 設定読み込み
    cfg = load_config(args.config)
    sns_config = cfg.get("sns", {})
    topic_arn = sns_config.get("topic_arn", "")
    region = sns_config.get("region", "ap-northeast-1")

    if not topic_arn and not args.dry_run:
        logger.error("sns.topic_arn が設定されていません。config/filter_config.yaml を確認してください。")
        return 1

    # 既読状態読み込み
    current_state = state.load(args.state_file)

    # RSS 取得
    try:
        xml_text = fetcher.fetch_rss()
    except Exception as e:
        logger.error("RSS 取得失敗: %s", e)
        return 1

    # パース
    items = fetcher.parse_rss(xml_text)

    # 差分検出
    new_items = state.filter_new(items, current_state)
    if not new_items:
        logger.info("新着記事なし。終了します。")
        if not args.dry_run:
            state.save(current_state, args.state_file)
        return 0

    # 分類
    for item in new_items:
        item.service_category = classifier.classify(item)

    # フィルタリング
    passed_items, excluded_items = filter_mod.apply_filter(new_items, cfg)

    for exc in excluded_items:
        logger.info("EXCLUDED: %s — %s", exc["title"][:60], exc["reason"])

    if not passed_items:
        logger.info("フィルタ通過記事なし。終了します。")
        if not args.dry_run:
            state.mark_seen([i.guid for i in new_items], current_state)
            state.save(current_state, args.state_file)
        return 0

    # SNS クライアント（dry-run でも初期化はするが publish しない）
    sns_client = boto3.client("sns", region_name=region)

    # 要約 → SNS 通知
    published_guids: list[str] = []

    for item in passed_items:
        logger.info("Processing: %s", item.title[:60])

        summary = summarizer.summarize(item)

        if args.dry_run:
            logger.info("[DRY-RUN] Would publish: %s", item.title[:60])
            logger.info("[DRY-RUN] Summary: %s", summary)
            published_guids.append(item.guid)
            continue

        success = notifier.publish(sns_client, topic_arn, item, summary)
        if success:
            published_guids.append(item.guid)

    # 状態更新（dry-run では行わない）
    if not args.dry_run:
        all_new_guids = [i.guid for i in new_items]
        state.mark_seen(all_new_guids, current_state)
        state.save(current_state, args.state_file)

    logger.info(
        "完了: 新着 %d 件 / フィルタ通過 %d 件 / SNS publish %d 件",
        len(new_items),
        len(passed_items),
        len(published_guids),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
