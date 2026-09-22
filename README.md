# aws-whatsnew-notifier

AWS What's New RSS を定期取得し、分類・フィルタリング後に日本語要約して Amazon SNS に通知する Python CLI ツール。

[Kiro University Challenge 2026](https://kiro.dev/2026/university/) の提出プロジェクトです。

## 概要

```
RSS取得 → 差分検出 → 分類・フィルタリング → 日本語要約 → SNS publish → SQS（確認用）
```

## 対応レッスン

| レッスン | 機能 |
|---------|------|
| L1: Spec-driven development | フィルタリング・通知機能を Feature Spec で定義 |
| L2: Steering documents | Python スタイル規約・boto3 規約を Steering で管理 |
| L3: Hooks | 設定ファイル保存時にバリデーションを自動実行 |
| L4: Property-based testing | フィルタリングロジックをプロパティベーステストで検証 |

## セットアップ

```bash
pip install -r requirements.txt
cp config/filter_config.yaml.example config/filter_config.yaml
# AWS 認証を設定してから実行
python src/main.py --dry-run
```

## 必要な環境

- Python 3.11+
- AWS 認証（SNS publish 権限）
- Kiro CLI（日本語要約に使用）
