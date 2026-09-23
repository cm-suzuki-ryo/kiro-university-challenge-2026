# AWS What's New Notifier — Setup Skill

## Overview

This skill provides guidance for setting up and operating the AWS What's New Notifier.
It polls the AWS What's New RSS feed, filters items by service category, and publishes
Japanese-language summaries to Amazon SNS.

## Project Structure

```
kiro-university-challenge-2026/
├── src/
│   ├── main.py          # Entry point
│   ├── fetcher.py       # RSS fetch and XML parse
│   ├── classifier.py    # Service category classification
│   ├── filter.py        # Filter logic
│   ├── summarizer.py    # Plain-text summary generation
│   ├── notifier.py      # SNS publish
│   └── state.py         # Seen-GUID state management
├── config/
│   └── filter_config.yaml  # Filter rules and SNS config
├── tests/
│   └── test_filter_properties.py  # Property-based tests (hypothesis)
└── .kiro/
    ├── specs/filter-and-notify.md
    ├── steering/python-style.md
    ├── hooks/hooks.json
    └── powers/aws-whatsnew/  # This power
```

## Prerequisites

- Python 3.12+
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- Amazon SNS topic created in `ap-northeast-1`

## Setup Steps

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure SNS topic ARN in `config/filter_config.yaml`:
   ```yaml
   sns:
     topic_arn: arn:aws:sns:ap-northeast-1:<account-id>:<topic-name>
     region: ap-northeast-1
   ```

3. Run in dry-run mode to verify:
   ```bash
   python src/main.py --dry-run --verbose
   ```

4. Run for real:
   ```bash
   python src/main.py
   ```

## Key Conventions

- Follow `.kiro/steering/python-style.md` for all Python code
- All functions must have type hints
- Use `logging` (not `print`) for output
- State file is stored at `state/seen.json`

## RSS Feed

- URL: `https://aws.amazon.com/about-aws/whats-new/recent/feed/`
- Format: RSS 2.0 (XML)
- Parsed by `src/fetcher.py` into `FeedItem` dataclasses

## Filter Configuration

Edit `config/filter_config.yaml` to control which services trigger notifications.
The `include_categories` list accepts service names matched by `src/classifier.py`.
