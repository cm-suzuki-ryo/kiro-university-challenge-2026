# Feature Spec: AWS What's New Filter and Notify

## Overview

AWS What's New RSS フィードを取得し、分類・フィルタリング後に日本語要約して Amazon SNS に通知する CLI ツール。

## Requirements

### RSS 取得と差分検出

WHEN the tool is executed  
THE SYSTEM SHALL fetch the AWS What's New RSS feed from `https://aws.amazon.com/about-aws/whats-new/recent/feed/`

WHEN the RSS feed is fetched successfully  
THE SYSTEM SHALL compare item GUIDs against a local state file to identify new items only

WHEN no new items are found  
THE SYSTEM SHALL exit with a message "No new items" without publishing to SNS

### 分類

WHEN a new RSS item is identified  
THE SYSTEM SHALL classify it by AWS service category using the `category` field in the RSS item

WHEN an item has no category field  
THE SYSTEM SHALL assign it to the "uncategorized" category

### フィルタリング

WHEN an item is classified  
THE SYSTEM SHALL evaluate it against the filter rules defined in `config/filter_config.yaml`

WHEN an item matches an exclude_categories rule  
THE SYSTEM SHALL skip the item and record the exclusion reason in the run log

WHEN an item matches an exclude_keywords rule (title match)  
THE SYSTEM SHALL skip the item and record the exclusion reason in the run log

WHEN an item matches a region_expansion pattern AND does not contain an allow_regions keyword  
THE SYSTEM SHALL skip the item as a non-relevant region announcement

WHEN an item passes all filter rules  
THE SYSTEM SHALL mark it as eligible for summarization and notification

### 日本語要約

WHEN an item is eligible for notification  
THE SYSTEM SHALL generate a Japanese summary using kiro-cli in headless mode

WHEN the summary is generated  
THE SYSTEM SHALL include: service name, what changed, and impact in 3 sentences or fewer

### SNS 通知

WHEN a Japanese summary is ready  
THE SYSTEM SHALL publish it to the configured Amazon SNS topic ARN

WHEN the SNS publish succeeds  
THE SYSTEM SHALL update the state file to mark the item's GUID as seen

WHEN the SNS publish fails  
THE SYSTEM SHALL log the error and continue processing remaining items without updating state for the failed item

### Dry-run モード

WHEN the tool is executed with `--dry-run`  
THE SYSTEM SHALL perform all steps except SNS publish and state file update

## Design

### Data Flow

```
config/filter_config.yaml
        │
        ▼
src/main.py
  ├─ fetcher.py    → RSS XML → list[FeedItem]
  ├─ classifier.py → FeedItem → category: str
  ├─ filter.py     → FeedItem + config → passed / excluded
  ├─ summarizer.py → FeedItem → Japanese summary (kiro-cli)
  └─ notifier.py   → summary → SNS publish
        │
        ▼
state/seen.json  (GUID records)
```

### Key Components

| Module | Responsibility |
|--------|---------------|
| `src/fetcher.py` | RSS fetch, XML parse, FeedItem dataclass |
| `src/classifier.py` | Service category classification from RSS category field |
| `src/filter.py` | Filter rule evaluation against filter_config.yaml |
| `src/summarizer.py` | Japanese summary via kiro-cli headless |
| `src/notifier.py` | boto3 SNS publish |
| `src/state.py` | seen.json read/write |
| `src/main.py` | CLI entry point, orchestration |
| `config/filter_config.yaml` | Filter rules (exclude categories, keywords, regions, expensive) |

### FeedItem Dataclass

```python
@dataclass
class FeedItem:
    guid: str
    title: str
    description_plain: str
    pub_date: str
    category: str
    link: str
    service_category: str = "uncategorized"  # set by classifier
```

### Configuration Schema (filter_config.yaml)

```yaml
exclude_categories: [list of RSS category keywords]
exclude_keywords: [list of title keywords]
region_expansion:
  enabled: bool
  patterns: [list of phrases]
  allow_regions: [list of region names]
exclude_expensive: [list of service/instance keywords]
sns:
  topic_arn: "arn:aws:sns:..."
  region: "ap-northeast-1"
```

## Tasks

- [ ] 1. `src/fetcher.py` — RSS fetch と FeedItem parse
- [ ] 2. `src/classifier.py` — category 分類
- [ ] 3. `src/filter.py` — フィルタリングロジック
- [ ] 4. `src/summarizer.py` — kiro-cli 呼び出しで日本語要約
- [ ] 5. `src/notifier.py` — SNS publish
- [ ] 6. `src/state.py` — seen.json 管理
- [ ] 7. `src/main.py` — CLI エントリーポイント（argparse、dry-run オプション）
- [ ] 8. `config/filter_config.yaml` — フィルタ設定（example 込み）
- [ ] 9. `requirements.txt` — 依存パッケージ
- [ ] 10. AWS リソース作成 — SNS Topic、SQS Queue、SNS→SQS サブスクリプション
