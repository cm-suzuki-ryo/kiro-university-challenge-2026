"""既読状態管理（seen.json）"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STATE_PATH = Path("state/seen.json")
MAX_SEEN_GUIDS = 1000


def load(state_path: Path = DEFAULT_STATE_PATH) -> dict:
    """seen.json を読み込む。存在しない場合は空の状態を返す"""
    if state_path.exists():
        with open(state_path, encoding="utf-8") as f:
            return json.load(f)
    return {"seen_guids": [], "last_check": None}


def save(state: dict, state_path: Path = DEFAULT_STATE_PATH) -> None:
    """seen.json に状態を書き込む"""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    # 古い GUID を上限まで保持
    guids = state.get("seen_guids", [])
    if len(guids) > MAX_SEEN_GUIDS:
        state["seen_guids"] = guids[-MAX_SEEN_GUIDS:]
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    logger.debug("State saved: %d seen GUIDs", len(state["seen_guids"]))


def filter_new(items: list, state: dict) -> list:
    """既読でないアイテムのみを返す"""
    seen = set(state.get("seen_guids", []))
    new_items = [item for item in items if item.guid not in seen]
    logger.info("New items: %d (total fetched: %d)", len(new_items), len(items))
    return new_items


def mark_seen(guids: list[str], state: dict) -> None:
    """GUID リストを既読に追加する（state を in-place 更新）"""
    current = set(state.get("seen_guids", []))
    current.update(guids)
    state["seen_guids"] = list(current)
