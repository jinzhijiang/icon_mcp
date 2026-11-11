"""Icon saver - saves icons to local filesystem."""

from __future__ import annotations

import os
import sys
import time
from typing import Any

from ..lang import t
from ..models import SelectionData, SelectionStatus
from .cache import CacheManager

__all__ = ["IconSaver"]

_UNSAFE_FILENAME_CHARS = '<>:"/\\|?*\0'


def _unique_file_name(name: str, used_names: set[str]) -> str:
    """Build a safe, unique .svg file name for an icon.

    iconfont often returns several icons with the same name, so duplicates
    within one batch get a numeric suffix instead of overwriting each other.
    """
    stem = "".join(
        "_" if c in _UNSAFE_FILENAME_CHARS or c.isspace() else c for c in name
    ).strip("._") or "icon"

    file_name = f"{stem}.svg"
    counter = 1
    while file_name in used_names:
        file_name = f"{stem}_{counter}.svg"
        counter += 1
    return file_name


class IconSaver:
    """Handles saving icons to local files and sending selections to MCP client."""

    def __init__(self, cache: CacheManager):
        self.cache = cache

    async def save_icons(
        self, icons: list[dict[str, Any]], save_path: str = "./saved-icons"
    ) -> dict[str, Any]:
        """Save icon SVG data to local files."""
        if not icons:
            raise ValueError("No icons to save")

        full_path = os.path.abspath(save_path)
        os.makedirs(full_path, exist_ok=True)

        saved: list[str] = []
        failed: list[str] = []
        used_names: set[str] = set()

        for icon in icons:
            name = icon.get("name", "unknown")
            svg_content = icon.get("svg", icon.get("show_svg", ""))
            if not svg_content:
                failed.append(name)
                continue

            file_name = _unique_file_name(name, used_names)
            used_names.add(file_name)
            file_path = os.path.join(full_path, file_name)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(svg_content)
                saved.append(file_name)
                print(t("download.saved", {"fileName": file_name}), file=sys.stderr)
            except Exception as e:
                print(
                    t("download.saveFailed", {"name": name}) + f": {e}",
                    file=sys.stderr,
                )
                failed.append(name)

        return {
            "saved": saved,
            "failed": failed,
            "save_path": full_path,
            "message": t(
                "download.saveCompleted", {"count": len(saved), "path": full_path}
            ),
        }

    def send_to_mcp_client(
        self, icons: list[dict[str, Any]], search_id: str
    ) -> None:
        """Mark selection as completed in the cache.

        The MCP server will pick up the completed selection
        when check_selection_status is polled.
        """
        self.cache.set_selection(
            search_id,
            SelectionData(
                status=SelectionStatus.COMPLETED,
                search_id=search_id,
                timestamp=time.time(),
                connected=True,
                selected_icons=icons,
            ),
        )

        print(
            t("selection.userSelectedIcons", {"count": len(icons)}),
            file=sys.stderr,
        )
