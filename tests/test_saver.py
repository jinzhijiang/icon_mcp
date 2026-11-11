"""Tests for IconSaver."""

from __future__ import annotations

import os
import tempfile

import pytest

from icon_mcp.utils.cache import CacheManager
from icon_mcp.utils.saver import IconSaver


class TestIconSaver:
    def setup_method(self):
        self.cache = CacheManager()
        self.saver = IconSaver(self.cache)

    @pytest.mark.asyncio
    async def test_save_icons_creates_files(self):
        icons = [
            {"name": "home", "svg": "<svg><path d='M0 0'/></svg>"},
            {"name": "star", "show_svg": "<svg><circle r='5'/></svg>"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await self.saver.save_icons(icons, save_path=tmpdir)
            assert "home.svg" in result["saved"]
            assert "star.svg" in result["saved"]
            assert result["failed"] == []
            # Verify file contents
            with open(os.path.join(tmpdir, "home.svg")) as f:
                assert "<svg>" in f.read()
            with open(os.path.join(tmpdir, "star.svg")) as f:
                assert "<circle" in f.read()

    @pytest.mark.asyncio
    async def test_save_icons_duplicate_names_do_not_overwrite(self):
        icons = [
            {"name": "setting", "svg": "<svg id='1'/>"},
            {"name": "setting", "svg": "<svg id='2'/>"},
            {"name": "setting", "svg": "<svg id='3'/>"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await self.saver.save_icons(icons, save_path=tmpdir)
            assert result["saved"] == ["setting.svg", "setting_1.svg", "setting_2.svg"]
            with open(os.path.join(tmpdir, "setting_1.svg")) as f:
                assert "id='2'" in f.read()
            with open(os.path.join(tmpdir, "setting_2.svg")) as f:
                assert "id='3'" in f.read()

    @pytest.mark.asyncio
    async def test_save_icons_sanitizes_path_separators(self):
        icons = [{"name": "../../evil", "svg": "<svg/>"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await self.saver.save_icons(icons, save_path=tmpdir)
            assert result["saved"] == ["evil.svg"]
            assert os.listdir(tmpdir) == ["evil.svg"]

    @pytest.mark.asyncio
    async def test_save_icons_handles_missing_svg(self):
        icons = [
            {"name": "empty_icon"},  # No svg or show_svg
            {"name": "valid", "svg": "<svg/>"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await self.saver.save_icons(icons, save_path=tmpdir)
            assert "empty_icon" in result["failed"]
            assert "valid.svg" in result["saved"]

    @pytest.mark.asyncio
    async def test_save_icons_empty_raises(self):
        with pytest.raises(ValueError, match="No icons"):
            await self.saver.save_icons([], save_path="/tmp/nope")

    @pytest.mark.asyncio
    async def test_save_icons_creates_directory(self):
        icons = [{"name": "test", "svg": "<svg/>"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "a", "b", "c")
            result = await self.saver.save_icons(icons, save_path=nested)
            assert os.path.exists(os.path.join(nested, "test.svg"))
            assert result["save_path"] == nested
