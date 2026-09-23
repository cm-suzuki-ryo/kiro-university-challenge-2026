# デモ仕様: TUI ブラウザ + アニメーションGIF 録画

## 目的

提出動画として、フィルタ済み What's New 記事をドリルダウンで閲覧できる TUI デモを
アニメーション GIF として生成する。Mac 側の画面録画は使わない。

---

## 1. TUI 仕様

### コマンド

```bash
python src/tui.py [--dry-run]
```

`--dry-run` 時は実際の RSS 取得の代わりにフィクスチャデータを使う（録画用）。

### 画面遷移

```
┌─────────────────────────────────────┐
│  カテゴリ一覧画面（Screen 1）         │
│  ────────────────────────────────   │
│  > Amazon Bedrock        (3)        │
│    AWS Lambda            (2)        │
│    Amazon S3             (1)        │
│    Amazon CloudWatch     (1)        │
│                                     │
│  [↑↓] 選択  [Enter] 開く  [q] 終了  │
└─────────────────────────────────────┘
         ↓ Enter
┌─────────────────────────────────────┐
│  記事一覧画面（Screen 2）             │
│  Amazon Bedrock の新着              │
│  ────────────────────────────────   │
│  > Amazon Bedrock adds custom mo…  │
│    Amazon Bedrock now supports …   │
│    Amazon Bedrock guardrails up…   │
│                                     │
│  [↑↓] 選択  [Enter] ブラウザで開く   │
│  [Esc] 戻る  [q] 終了               │
└─────────────────────────────────────┘
         ↓ Enter
    ブラウザで記事URLを開く（webbrowser.open）
```

### ライブラリ

- `textual` — TUI フレームワーク（requirements.txt に追加）
- 既存モジュール `fetcher`, `filter`, `classifier` をそのまま利用

### 既存コードとの接続

| 既存モジュール | TUI での使い方 |
|---------------|--------------|
| `fetcher.fetch_rss()` + `fetcher.parse_rss()` | RSS取得・パース |
| `classifier.classify(item)` | カテゴリ付与 |
| `filter.apply_filter(items, cfg)` | 除外フィルタ適用 |
| `FeedItem.link` | ブラウザで開くURL |

requirements.txt に追加するもの：
```
textual==3.5.0
```

---

## 2. 画面録画仕様

### ツールチェーン

```
asciinema rec  →  .cast ファイル  →  agg  →  demo.gif
```

- `asciinema`: `uvx asciinema` で実行（v2.4.0 確認済み）
- `agg`: GitHub Releases から `agg-aarch64-unknown-linux-gnu` をダウンロード

### agg のインストール

```bash
curl -L https://github.com/asciinema/agg/releases/download/v1.9.0/agg-aarch64-unknown-linux-gnu \
  -o /usr/local/bin/agg && chmod +x /usr/local/bin/agg
```

### 録画コマンド

```bash
uvx asciinema rec \
  --cols 100 --rows 30 \
  --title "AWS What's New Notifier — TUI Demo" \
  demo.cast \
  -- python src/tui.py --dry-run
```

- `--cols 100 --rows 30`: 見やすいサイズに固定
- `--dry-run`: フィクスチャデータで録画（ネットワーク遅延なし）

### GIF 変換コマンド

```bash
agg \
  --font-size 14 \
  --speed 1.5 \
  demo.cast demo.gif
```

### 出力先

```
/home/ws/daily/202609/23/0923-kiro-university-challenge-lessons5-6/
└── demo/
    ├── demo.cast    # asciinema 録画ファイル
    └── demo.gif     # 最終成果物
```

---

## 3. デモシナリオ（録画スクリプト）

録画時に行う操作の手順（再現性のため明示）：

1. `python src/tui.py --dry-run` 起動
2. カテゴリ一覧が表示される（0.5秒待機）
3. `↓` キーで "Amazon Bedrock" を選択（1秒待機）
4. `Enter` で記事一覧へ遷移（0.5秒待機）
5. `↓` キーで2件目を選択（1秒待機）
6. `Enter` でブラウザ起動（確認メッセージ表示）
7. `q` で終了

---

## 4. フィクスチャデータ仕様

`--dry-run` 時に使うサンプルデータ。
実際の AWS What's New から取得した記事タイトル・リンクを使う（実在URL）。

ファイル: `tests/fixtures/feed_sample.json`

```json
[
  {
    "guid": "https://aws.amazon.com/about-aws/whats-new/2026/09/sample-1",
    "title": "Amazon Bedrock adds custom model import for Llama 3.1 405B",
    "description_plain": "Amazon Bedrock now supports importing custom Llama 3.1 405B models...",
    "pub_date": "Mon, 22 Sep 2026 00:00:00 GMT",
    "category": "amazon-bedrock",
    "link": "https://aws.amazon.com/about-aws/whats-new/2026/09/sample-1",
    "service_category": "Amazon Bedrock"
  }
]
```

件数: カテゴリ 4〜5種、合計 10〜12件（デモとして見やすい量）

---

## 5. 実装順序

1. `tests/fixtures/feed_sample.json` — フィクスチャデータ作成
2. `requirements.txt` — `textual==3.5.0` 追加
3. `src/tui.py` — TUI 実装
4. `agg` バイナリ取得
5. 録画 → GIF 生成
6. `demo/` を GitHub push
