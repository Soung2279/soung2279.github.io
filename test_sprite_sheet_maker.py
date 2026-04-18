"""
Tests for sprite_sheet_maker.py
"""

import os
import math
import tempfile
import pytest
from PIL import Image

from sprite_sheet_maker import (
    collect_images,
    make_sprite_sheet,
    natural_sort_key,
    parse_color,
    parse_size,
    SUPPORTED_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def frame_dir(tmp_path):
    """Create a directory with 6 RGBA frames (32x32) in distinct colors."""
    colors = [
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
        (255, 255, 0, 255),
        (255, 0, 255, 255),
        (0, 255, 255, 255),
    ]
    for i, color in enumerate(colors, 1):
        img = Image.new("RGBA", (32, 32), color)
        img.save(tmp_path / f"frame{i:02d}.png")
    return tmp_path


# ---------------------------------------------------------------------------
# natural_sort_key
# ---------------------------------------------------------------------------

class TestNaturalSortKey:
    def test_sorts_numerically(self):
        names = ["frame10", "frame2", "frame1", "frame20"]
        assert sorted(names, key=natural_sort_key) == [
            "frame1", "frame2", "frame10", "frame20"
        ]

    def test_case_insensitive(self):
        names = ["FrameB", "frameA", "frameC"]
        assert sorted(names, key=natural_sort_key) == ["frameA", "FrameB", "frameC"]


# ---------------------------------------------------------------------------
# collect_images
# ---------------------------------------------------------------------------

class TestCollectImages:
    def test_collects_supported_images(self, frame_dir):
        paths = collect_images(str(frame_dir))
        assert len(paths) == 6
        assert all(os.path.isfile(p) for p in paths)

    def test_sorted_naturally(self, frame_dir):
        paths = collect_images(str(frame_dir))
        basenames = [os.path.basename(p) for p in paths]
        assert basenames == sorted(basenames, key=natural_sort_key)

    def test_ignores_non_image_files(self, frame_dir):
        (frame_dir / "notes.txt").write_text("not an image")
        paths = collect_images(str(frame_dir))
        assert all(p.endswith(tuple(SUPPORTED_EXTENSIONS)) for p in paths)

    def test_empty_folder(self, tmp_path):
        assert collect_images(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# make_sprite_sheet
# ---------------------------------------------------------------------------

class TestMakeSpriteSheet:
    def test_auto_columns(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = tmp_path / "sheet.png"
        make_sprite_sheet(paths, output_path=str(out))
        img = Image.open(out)
        # 6 frames → ceil(sqrt(6))=3 cols, 2 rows of 32x32
        assert img.size == (96, 64)

    def test_fixed_columns(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = tmp_path / "sheet.png"
        make_sprite_sheet(paths, columns=2, output_path=str(out))
        img = Image.open(out)
        # 2 cols, 3 rows
        assert img.size == (64, 96)

    def test_padding(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = tmp_path / "sheet.png"
        make_sprite_sheet(paths, columns=3, padding=4, output_path=str(out))
        img = Image.open(out)
        # 3 cols, 2 rows; w = 3*32 + 2*4 = 104, h = 2*32 + 1*4 = 68
        assert img.size == (104, 68)

    def test_resize(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = tmp_path / "sheet.png"
        make_sprite_sheet(paths, resize=(16, 16), columns=6, output_path=str(out))
        img = Image.open(out)
        assert img.size == (96, 16)

    def test_background_color(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = tmp_path / "sheet.png"
        # 3 frames, 4 columns → 4th slot is background
        make_sprite_sheet(
            paths[:3], columns=4, bg_color=(128, 0, 0, 255), output_path=str(out)
        )
        img = Image.open(out)
        # Pixel inside the empty 4th slot
        px = img.getpixel((32 * 3 + 1, 0))
        assert px[:3] == (128, 0, 0)

    def test_transparent_background(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = tmp_path / "sheet.png"
        make_sprite_sheet(paths[:1], columns=2, bg_color=(0, 0, 0, 0), output_path=str(out))
        img = Image.open(out)
        px = img.getpixel((32 + 1, 0))
        assert px[3] == 0  # transparent

    def test_pixel_colors_correct(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = tmp_path / "sheet.png"
        make_sprite_sheet(paths, columns=3, output_path=str(out))
        img = Image.open(out)
        # First frame is red
        assert img.getpixel((0, 0)) == (255, 0, 0, 255)
        # Second frame (col 1) is green
        assert img.getpixel((32, 0)) == (0, 255, 0, 255)
        # Fourth frame (row 1, col 0) is yellow
        assert img.getpixel((0, 32)) == (255, 255, 0, 255)

    def test_raises_on_empty_list(self, tmp_path):
        with pytest.raises(ValueError, match="No images"):
            make_sprite_sheet([], output_path=str(tmp_path / "out.png"))

    def test_raises_on_mismatched_sizes(self, tmp_path):
        a = tmp_path / "a.png"
        b = tmp_path / "b.png"
        Image.new("RGBA", (32, 32)).save(a)
        Image.new("RGBA", (64, 64)).save(b)
        with pytest.raises(ValueError, match="Frame sizes differ"):
            make_sprite_sheet([str(a), str(b)], output_path=str(tmp_path / "out.png"))

    def test_progress_callback(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        calls = []
        make_sprite_sheet(paths, output_path=str(tmp_path / "out.png"),
                          progress_callback=lambda c, t: calls.append((c, t)))
        assert len(calls) == len(paths)
        assert calls[-1] == (len(paths), len(paths))

    def test_returns_absolute_path(self, frame_dir, tmp_path):
        paths = collect_images(str(frame_dir))
        out = make_sprite_sheet(paths, output_path=str(tmp_path / "out.png"))
        assert os.path.isabs(out)
        assert os.path.isfile(out)


# ---------------------------------------------------------------------------
# parse_color
# ---------------------------------------------------------------------------

class TestParseColor:
    def test_transparent(self):
        assert parse_color("transparent") == (0, 0, 0, 0)

    def test_hex_rgb(self):
        assert parse_color("#ff0000") == (255, 0, 0, 255)

    def test_hex_rgba(self):
        assert parse_color("#ff000080") == (255, 0, 0, 128)

    def test_case_insensitive(self):
        assert parse_color("TRANSPARENT") == (0, 0, 0, 0)
        assert parse_color("#FF0000") == (255, 0, 0, 255)

    def test_invalid(self):
        import argparse
        with pytest.raises(argparse.ArgumentTypeError):
            parse_color("notacolor")


# ---------------------------------------------------------------------------
# parse_size
# ---------------------------------------------------------------------------

class TestParseSize:
    def test_valid(self):
        assert parse_size("64x64") == (64, 64)
        assert parse_size("128x256") == (128, 256)

    def test_case_insensitive(self):
        assert parse_size("64X64") == (64, 64)

    def test_invalid(self):
        import argparse
        with pytest.raises(argparse.ArgumentTypeError):
            parse_size("notasize")
