"""src/filter.py の evaluate() に対するプロパティベーステスト。

.kiro/specs/filter-and-notify.md の「フィルタリング」要件を検証する。

検証するプロパティ:
1. exclude_categories に一致するアイテムは必ず passed=False になる
2. exclude_keywords に一致するタイトルは必ず passed=False になる
3. すべての除外条件を満たさないアイテムは必ず passed=True になる
4. region_expansion が無効の場合はリージョン系アナウンスも通過する

evaluate() の判定順序は
  exclude_categories -> exclude_keywords -> region_expansion -> exclude_expensive
であることに留意する。あるプロパティを分離して検証するには、
それより前段の条件に「偶然」一致しない入力を生成する必要がある。
"""
from typing import Any

from hypothesis import assume, given
from hypothesis import strategies as st

from fetcher import FeedItem
from filter import evaluate

# --- テスト用の固定設定値 -------------------------------------------------

EXCLUDE_CATEGORIES = ["amazon-eks", "amazon-sagemaker", "amazon-connect"]
EXCLUDE_KEYWORDS = ["GovCloud", "SageMaker", "Parallel Computing Service"]
EXCLUDE_EXPENSIVE = ["Trainium", "Inferentia", "Outposts", "CloudHSM"]
REGION_PATTERNS = ["now available in", "launches in", "expands to"]
ALLOW_REGIONS = ["Tokyo", "ap-northeast-1"]

# 上記のどのキーワード・パターンにも部分文字列として現れない安全な文字。
# 除外語はすべて ASCII 英字とハイフン・空白で構成されるため、
# 数字のみで生成したテキストは絶対にどの除外条件にもマッチしない。
SAFE_ALPHABET = "0123456789"

safe_text = st.text(alphabet=SAFE_ALPHABET, min_size=0, max_size=40)


def make_config(region_enabled: bool = True) -> dict[str, Any]:
    return {
        "exclude_categories": list(EXCLUDE_CATEGORIES),
        "exclude_keywords": list(EXCLUDE_KEYWORDS),
        "region_expansion": {
            "enabled": region_enabled,
            "patterns": list(REGION_PATTERNS),
            "allow_regions": list(ALLOW_REGIONS),
        },
        "exclude_expensive": list(EXCLUDE_EXPENSIVE),
    }


def make_item(
    *,
    title: str = "0",
    description_plain: str = "0",
    category: str = "0",
) -> FeedItem:
    """テスト対象に必要なフィールドを埋めた FeedItem を作る。"""
    return FeedItem(
        guid="guid-0",
        title=title,
        description_plain=description_plain,
        description_html="",
        pub_date="",
        category=category,
        link="",
        service_category="uncategorized",
    )


# --- プロパティ 1: カテゴリ除外 -------------------------------------------


@given(
    prefix=safe_text,
    suffix=safe_text,
    exclude=st.sampled_from(EXCLUDE_CATEGORIES),
    case_shift=st.booleans(),
)
def test_excluded_category_always_fails(prefix, suffix, exclude, case_shift):
    """category に exclude_categories のいずれかを含むアイテムは必ず passed=False。

    evaluate は category を小文字化して部分一致で判定するため、大文字混在でも
    除外されることを確認する。カテゴリ判定は最初のチェックなので、
    他フィールドはどんな安全テキストでも結果に影響しない。
    """
    category = prefix + (exclude.upper() if case_shift else exclude) + suffix
    item = make_item(category=category)
    result = evaluate(item, make_config())

    assert result.passed is False
    assert result.reason.startswith("exclude_category:")


# --- プロパティ 2: キーワード除外（タイトル） -----------------------------


@given(
    prefix=safe_text,
    suffix=safe_text,
    keyword=st.sampled_from(EXCLUDE_KEYWORDS),
    case_shift=st.booleans(),
    description=safe_text,
)
def test_excluded_keyword_in_title_always_fails(
    prefix, suffix, keyword, case_shift, description
):
    """title に exclude_keywords のいずれかを含むアイテムは必ず passed=False。

    キーワード判定はカテゴリ判定の次段なので、カテゴリは除外語を含まない
    安全なテキストにしておく必要がある。
    """
    title = prefix + (keyword.lower() if case_shift else keyword) + suffix
    item = make_item(title=title, description_plain=description, category="0")
    result = evaluate(item, make_config())

    assert result.passed is False
    assert result.reason.startswith("exclude_keyword:")


# --- プロパティ 3: 全条件を満たさなければ通過 -----------------------------


@given(
    title=safe_text,
    description=safe_text,
    category=safe_text,
    region_enabled=st.booleans(),
)
def test_no_exclusion_always_passes(title, description, category, region_enabled):
    """どの除外条件にもマッチしないアイテムは必ず passed=True。

    安全な文字（数字のみ）で生成したテキストは、いかなる除外語・
    リージョンパターンとも部分一致しない。よって region_expansion の
    有効・無効に関わらず必ず通過するはず。
    """
    item = make_item(title=title, description_plain=description, category=category)
    result = evaluate(item, make_config(region_enabled=region_enabled))

    assert result.passed is True
    assert result.reason == ""


# --- プロパティ 4: region_expansion 無効ならリージョン系も通過 -------------


@given(
    pattern=st.sampled_from(REGION_PATTERNS),
    prefix=safe_text,
    suffix=safe_text,
    region_text=st.text(alphabet=SAFE_ALPHABET + "abcdefghijklmnopqrstuvwxyz ", max_size=30),
    place_in_title=st.booleans(),
)
def test_region_expansion_disabled_passes_region_announcements(
    pattern, prefix, suffix, region_text, place_in_title
):
    """region_expansion.enabled=False のとき、リージョン追加系アナウンスも通過する。

    パターンを含むテキストを title か description に埋め込んでも、
    リージョン展開判定が無効化されているため除外されない。
    ただし他の除外条件（categories/keywords/expensive）には
    一致しないよう、パターン以外は安全テキストにする。

    region_text はパターン以外の英字を許すが、除外語（Trainium 等）を
    偶然含む可能性があるため assume で排除する。
    """
    text = prefix + pattern + " " + region_text + suffix
    lowered = text.lower()
    # 他の除外条件に偶然マッチする入力は本プロパティの対象外なので除外する。
    for kw in EXCLUDE_KEYWORDS + EXCLUDE_EXPENSIVE:
        assume(kw.lower() not in lowered)

    if place_in_title:
        item = make_item(title=text, description_plain="0", category="0")
    else:
        item = make_item(title="0", description_plain=text, category="0")

    result = evaluate(item, make_config(region_enabled=False))

    assert result.passed is True
    assert result.reason == ""


# --- 補助プロパティ: region_expansion 有効かつ allow_region なしなら除外 ----


@given(
    pattern=st.sampled_from(REGION_PATTERNS),
    prefix=safe_text,
    suffix=safe_text,
)
def test_region_expansion_enabled_excludes_non_allow_region(pattern, prefix, suffix):
    """region_expansion 有効時、パターンを含み allow_regions を含まなければ除外。

    プロパティ 4 の対となる確認。安全テキスト（数字）は allow_regions
    (Tokyo 等) を含まないため、必ず region_expansion で除外される。
    """
    text = prefix + pattern + suffix
    item = make_item(title=text, description_plain="0", category="0")
    result = evaluate(item, make_config(region_enabled=True))

    assert result.passed is False
    assert result.reason.startswith("region_expansion")
