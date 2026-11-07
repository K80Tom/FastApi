#!/usr/bin/env python3
"""校验教程章节、Markdown 相对链接、代码围栏和 SVG/PNG 图解。"""

from __future__ import annotations

import re
import runpy
import struct
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "00-FastAPI框架独立学习总路线.md"
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CHAPTER_RE = re.compile(r"\[第\s*(\d{2})\s*讲[^\]]*\]\(([^)]+\.md)\)")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def validate_diagrams() -> tuple[list[str], int]:
    namespace = runpy.run_path(str(ROOT / "tools" / "generate_diagrams.py"))
    diagrams = namespace["DIAGRAMS"]
    if len(diagrams) != 28:
        fail(f"图解定义应为 28 组，实际为 {len(diagrams)}")

    stems = [f"{item['num']}-{item['slug']}" for item in diagrams]
    if len(set(stems)) != 28:
        fail("图解编号或 slug 存在重复")

    for stem in stems:
        png_path = ROOT / "images" / f"{stem}.png"
        svg_path = ROOT / "images" / f"{stem}.svg"
        for path in (png_path, svg_path):
            if not path.is_file():
                fail(f"缺少图解文件：{path.relative_to(ROOT)}")
        png = png_path.read_bytes()
        if png[:8] != b"\x89PNG\r\n\x1a\n":
            fail(f"PNG 文件头无效：{png_path.name}")
        width, height = struct.unpack(">II", png[16:24])
        if (width, height) != (1600, 1000):
            fail(f"PNG 尺寸应为 1600×1000：{png_path.name} 为 {width}×{height}")
        svg = svg_path.read_text(encoding="utf-8")
        if 'width="1600"' not in svg or 'height="1000"' not in svg:
            fail(f"SVG 画布尺寸无效：{svg_path.name}")
        if "<title" not in svg or "<desc" not in svg:
            fail(f"SVG 缺少无障碍标题或描述：{svg_path.name}")
    return stems, len(diagrams)


def validate_chapters(stems: list[str]) -> list[Path]:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    links = CHAPTER_RE.findall(roadmap)
    expected_numbers = [f"{number:02d}" for number in range(1, 28)]
    numbers = [number for number, _ in links]
    if numbers != expected_numbers:
        fail(f"总路线章节编号不完整或顺序错误：{numbers}")

    chapter_paths: list[Path] = []
    for number, target in links:
        path = ROOT / unquote(target)
        if not path.is_file():
            fail(f"总路线链接不存在：{target}")
        chapter_paths.append(path)
        text = path.read_text(encoding="utf-8")
        stem = next((value for value in stems if value.startswith(f"{number}-")), None)
        if stem is None:
            fail(f"第 {number} 讲没有图解定义")
        for suffix in ("png", "svg"):
            expected = f"images/{stem}.{suffix}"
            if expected not in text:
                fail(f"第 {number} 讲未引用 {expected}")
    return chapter_paths


def validate_markdown(extra_paths: list[Path]) -> tuple[int, int]:
    paths = sorted(set((ROOT / "README.md", ROOT / "taskhub_api" / "README.md", ROADMAP, *extra_paths)))
    line_count = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        line_count += len(text.splitlines())
        fences = sum(line.lstrip().startswith("```") for line in text.splitlines())
        if fences % 2:
            fail(f"代码围栏数量为奇数：{path.name}")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip().split()[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            local_target = unquote(target.split("#", 1)[0])
            if not local_target:
                continue
            resolved = (path.parent / local_target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                fail(f"链接越出仓库：{path.name} → {target}")
            if not resolved.exists():
                fail(f"相对链接不存在：{path.name} → {target}")
    return len(paths), line_count


def main() -> None:
    stems, diagram_count = validate_diagrams()
    chapters = validate_chapters(stems)
    markdown_count, line_count = validate_markdown(chapters)
    print(
        f"OK: {len(chapters)} chapters, {diagram_count} PNG + {diagram_count} SVG, "
        f"{markdown_count} Markdown files, {line_count} Markdown lines; links and fences valid."
    )


if __name__ == "__main__":
    main()
