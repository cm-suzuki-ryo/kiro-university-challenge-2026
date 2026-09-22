"""pytest 共通設定。

src/ をインポートパスに追加する。filter.py が `from fetcher import FeedItem`
のように src 直下のモジュールを参照しているため。
"""
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
