# Python スタイル規約

このプロジェクトの Python コードは以下の規約に従う。これは Kiro がコードを生成・編集するときに常に守るべき基準である。

## 型ヒント

すべての関数に型ヒントを付ける。戻り値が None の場合も `-> None` を明示する。

```python
# Good
def fetch_rss(url: str, timeout: int = 30) -> str:
    ...

# Bad
def fetch_rss(url, timeout=30):
    ...
```

## ロギング

`print()` を使わず `logging` モジュールを使う。ログレベルは以下の基準で使い分ける。

- `DEBUG`: 処理の詳細（各アイテムの判定結果など）
- `INFO`: 正常な処理の節目（取得件数、通過件数、SNS publish 成功など）
- `WARNING`: 処理は続行できるが注意が必要な状況
- `ERROR`: 処理が失敗した場合（SNS publish 失敗、RSS fetch 失敗など）

```python
import logging
logger = logging.getLogger(__name__)

# Good
logger.info("Fetched %d items from RSS", len(items))

# Bad
print(f"Fetched {len(items)} items")
```

## dataclass の使用

データの受け渡しには辞書ではなく `@dataclass` を使う。

```python
from dataclasses import dataclass, field

@dataclass
class FeedItem:
    guid: str
    title: str
    category: str = "uncategorized"
```

## boto3 クライアント

boto3 クライアントはモジュールレベルではなく関数の引数または依存注入で渡す。テストで差し替えられるようにする。

```python
# Good
def publish(sns_client: Any, topic_arn: str, message: str) -> None:
    sns_client.publish(TopicArn=topic_arn, Message=message)

# Bad
sns = boto3.client("sns")  # module level
```

## エラー処理

AWS API 呼び出しは `botocore.exceptions.ClientError` を捕捉し、ログに記録してから再 raise または処理を継続する。1 件の失敗で全体を止めない。

## ファイル構成

```
src/          # アプリケーションコード
config/       # 設定ファイル（YAML）
state/        # 実行時状態（seen.json）—gitignore 対象
tests/        # テストコード
```
