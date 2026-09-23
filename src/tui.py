"""AWS What's New — TUI ブラウザ

カテゴリ一覧 → 記事一覧 → ブラウザで開く の2段ドリルダウン。
--dry-run フラグで tests/fixtures/feed_sample.json を使う。
"""
import argparse
import json
import sys
import webbrowser
from collections import defaultdict
from pathlib import Path

import yaml
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, ListItem, ListView, Static

ROOT = Path(__file__).parent.parent
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "feed_sample.json"
CONFIG_PATH = ROOT / "config" / "filter_config.yaml"


# ---------------------------------------------------------------------------
# データ取得
# ---------------------------------------------------------------------------

def load_items(dry_run: bool) -> list[dict]:
    """フィードアイテムをロードして返す。dry_run 時はフィクスチャを使う。"""
    if dry_run:
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            return json.load(f)

    # 実 RSS 取得
    sys.path.insert(0, str(ROOT / "src"))
    import classifier
    import fetcher
    import filter as filter_mod

    cfg = yaml.safe_load(open(CONFIG_PATH, encoding="utf-8"))
    items = fetcher.parse_rss(fetcher.fetch_rss())
    for item in items:
        item.service_category = classifier.classify(item)
    passed, _ = filter_mod.apply_filter(items, cfg)
    return [
        {
            "guid": i.guid,
            "title": i.title,
            "description_plain": i.description_plain,
            "pub_date": i.pub_date,
            "link": i.link,
            "service_category": i.service_category,
        }
        for i in passed
    ]


def group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    """service_category でグループ化して件数降順に返す。"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        groups[item["service_category"]].append(item)
    return dict(sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True))


# ---------------------------------------------------------------------------
# 記事一覧画面
# ---------------------------------------------------------------------------

class ArticleScreen(Screen):
    """選択されたカテゴリの記事一覧を表示する画面。"""

    BINDINGS = [
        Binding("escape,q", "app.pop_screen", "戻る"),
        Binding("enter", "open_link", "ブラウザで開く", show=True),
    ]

    def __init__(self, category: str, articles: list[dict]) -> None:
        super().__init__()
        self.category = category
        self.articles = articles

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(f" 📂 {self.category}  ({len(self.articles)} 件)", id="subtitle")
        lv = ListView(
            *[
                ListItem(
                    Static(f"  {a['title']}", classes="article-title"),
                    id=f"article-{i}",
                )
                for i, a in enumerate(self.articles)
            ]
        )
        yield lv
        yield Footer()

    def action_open_link(self) -> None:
        lv = self.query_one(ListView)
        idx = lv.index
        if idx is not None and 0 <= idx < len(self.articles):
            url = self.articles[idx]["link"]
            webbrowser.open(url)
            self.notify(f"ブラウザで開きました: {url[:60]}…")


# ---------------------------------------------------------------------------
# カテゴリ一覧画面
# ---------------------------------------------------------------------------

class CategoryScreen(Screen):
    """カテゴリ一覧をトップ画面として表示する。"""

    BINDINGS = [
        Binding("q", "app.quit", "終了"),
        Binding("enter", "select_category", "開く", show=True),
    ]

    def __init__(self, groups: dict[str, list[dict]]) -> None:
        super().__init__()
        self.groups = groups
        self.category_keys = list(groups.keys())

    def compose(self) -> ComposeResult:
        total = sum(len(v) for v in self.groups.values())
        yield Header(show_clock=False)
        yield Static(f" 🔔 AWS What's New — {total} 件がフィルタを通過", id="subtitle")
        lv = ListView(
            *[
                ListItem(
                    Static(
                        f"  {cat:<38}  ({len(articles):>2}件)",
                        classes="category-row",
                    ),
                    id=f"cat-{i}",
                )
                for i, (cat, articles) in enumerate(self.groups.items())
            ]
        )
        yield lv
        yield Footer()

    def action_select_category(self) -> None:
        lv = self.query_one(ListView)
        idx = lv.index
        if idx is not None and 0 <= idx < len(self.category_keys):
            cat = self.category_keys[idx]
            self.app.push_screen(ArticleScreen(cat, self.groups[cat]))


# ---------------------------------------------------------------------------
# アプリ本体
# ---------------------------------------------------------------------------

CSS = """
Screen {
    background: $surface;
}

#subtitle {
    padding: 0 1;
    color: $text-muted;
    margin-bottom: 1;
}

ListView {
    height: 1fr;
    border: solid $primary;
}

ListItem {
    padding: 0;
}

ListItem:focus, ListItem.-highlighted {
    background: $accent;
    color: $text;
}

.category-row, .article-title {
    width: 100%;
}
"""


class WhatsnewApp(App):
    """AWS What's New TUI ブラウザ。"""

    TITLE = "AWS What's New Browser"
    CSS = CSS

    def __init__(self, dry_run: bool = False) -> None:
        super().__init__()
        self.dry_run = dry_run

    def on_mount(self) -> None:
        items = load_items(self.dry_run)
        groups = group_by_category(items)
        self.push_screen(CategoryScreen(groups))


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="AWS What's New TUI ブラウザ")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="フィクスチャデータを使う（ネットワーク不要）",
    )
    args = parser.parse_args()
    app = WhatsnewApp(dry_run=args.dry_run)
    app.run()


if __name__ == "__main__":
    main()
