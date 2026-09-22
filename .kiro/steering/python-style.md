# Python Style Guide

This guide defines coding conventions for this project. Kiro must follow these rules whenever generating or editing Python code.

## Type Hints

Add type hints to every function. Always annotate `-> None` explicitly when a function returns nothing.

```python
# Good
def fetch_rss(url: str, timeout: int = 30) -> str:
    ...

# Bad
def fetch_rss(url, timeout=30):
    ...
```

## Logging

Never use `print()`. Use the `logging` module instead. Choose log levels as follows:

- `DEBUG`: detailed processing (e.g., per-item filter decisions)
- `INFO`: normal milestones (e.g., item counts, SNS publish success)
- `WARNING`: recoverable issues that need attention
- `ERROR`: failures (e.g., SNS publish failure, RSS fetch failure)

```python
import logging
logger = logging.getLogger(__name__)

# Good
logger.info("Fetched %d items from RSS", len(items))

# Bad
print(f"Fetched {len(items)} items")
```

## Dataclasses

Use `@dataclass` instead of plain dicts for passing structured data.

```python
from dataclasses import dataclass, field

@dataclass
class FeedItem:
    guid: str
    title: str
    category: str = "uncategorized"
```

## boto3 Clients

Pass boto3 clients as function arguments or via dependency injection — never create them at module level. This keeps them replaceable in tests.

```python
# Good
def publish(sns_client: Any, topic_arn: str, message: str) -> None:
    sns_client.publish(TopicArn=topic_arn, Message=message)

# Bad
sns = boto3.client("sns")  # module level
```

## Error Handling

Catch `botocore.exceptions.ClientError` on every AWS API call. Log the error and either re-raise or continue processing. Do not let a single failure stop the entire run.

## Directory Layout

```
src/          # application code
config/       # configuration files (YAML)
state/        # runtime state (seen.json) — gitignored
tests/        # test code
```
