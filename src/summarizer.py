"""kiro-cli を使った日本語要約"""
import logging
import subprocess
import textwrap

from fetcher import FeedItem

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT_TEMPLATE = textwrap.dedent("""\
    以下の AWS What's New アナウンスを日本語で 3 文以内に要約してください。
    要約には「対象サービス」「何が変わったか」「開発者・利用者への影響」を含めてください。
    マークダウンや箇条書きは使わず、平文で出力してください。

    タイトル: {title}
    本文:
    {description}
""")


def summarize(item: FeedItem, timeout: int = 60) -> str:
    """
    kiro-cli chat --no-interactive でアイテムを日本語要約する。
    失敗した場合はタイトルをそのまま返す。
    """
    prompt = SUMMARIZE_PROMPT_TEMPLATE.format(
        title=item.title,
        description=item.description_plain[:1000],
    )

    try:
        result = subprocess.run(
            ["kiro-cli", "chat", "--no-interactive", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0 and result.stdout.strip():
            summary = result.stdout.strip()
            logger.debug("Summarized: %s -> %d chars", item.title[:40], len(summary))
            return summary
        else:
            logger.warning(
                "kiro-cli summarization failed for '%s': %s",
                item.title[:40],
                result.stderr[:200],
            )
            return item.title

    except subprocess.TimeoutExpired:
        logger.warning("kiro-cli timed out for '%s'", item.title[:40])
        return item.title
    except FileNotFoundError:
        logger.error("kiro-cli not found. Falling back to title only.")
        return item.title
