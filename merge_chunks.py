"""
Merge chunked PDF parse outputs back into per-issue bundles.

For each directory under ./chunk named like "<prefix>_chunk_<nn>", this script:
1) concatenates per-page markdowns doc_*.md (doc_0.md ... doc_N.md) in chunk order,
    with de-duplication, into output/<prefix>/doc.md.
    De-duplication key: the first non-empty line (exact match) across all chunks of
    the same prefix; first occurrence wins, later duplicates are skipped.
2) copies all images from each chunk's imgs/ folder into output/<prefix>/imgs/
    using original filenames (to keep doc.md image paths valid).

Usage:
  python merge_chunks.py
Optional env vars:
  CHUNK_ROOT: source chunk root (default: ./chunk)
  OUTPUT_ROOT: output root (default: ./output)
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

CHUNK_ROOT = Path(os.getenv("CHUNK_ROOT", "./chunk")).resolve()
OUTPUT_ROOT = Path(os.getenv("OUTPUT_ROOT", "./output")).resolve()
CHUNK_PATTERN = re.compile(r"^(?P<prefix>.+)_chunk_(?P<num>\d+)$")
MIN_SECTION_LEN = int(os.getenv("MIN_SECTION_LEN", "500"))


def find_chunk_groups(chunk_root: Path) -> Dict[str, List[Tuple[int, Path]]]:
    groups: Dict[str, List[Tuple[int, Path]]] = {}
    for entry in chunk_root.iterdir():
        if not entry.is_dir():
            continue
        m = CHUNK_PATTERN.match(entry.name)
        if not m:
            continue
        prefix = m.group("prefix")
        num = int(m.group("num"))
        groups.setdefault(prefix, []).append((num, entry))
    for prefix in groups:
        groups[prefix].sort(key=lambda x: x[0])
    return groups


DOC_FILE_RE = re.compile(r"^doc_(?P<num>\d+)\.md$")


def _first_line_key(text: str) -> str | None:
    """Use the first non-empty line as the dedup key."""
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return None


def concat_docs(chunks: List[Tuple[int, Path]], out_doc: Path) -> None:
    parts: List[str] = []
    seen: set[str] = set()
    skipped = 0

    for chunk_num, folder in chunks:
        candidates: List[Tuple[int, Path]] = []
        for entry in folder.iterdir():
            if not entry.is_file():
                continue
            m = DOC_FILE_RE.match(entry.name)
            if not m:
                continue
            doc_num = int(m.group("num"))
            candidates.append((doc_num, entry))

        for doc_num, path in sorted(candidates, key=lambda x: x[0]):
            raw = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not raw:
                continue
            # Remove known watermark lines/phrases
            watermark = "唯一淘宝店铺：艾米学社"
            if watermark in raw:
                raw = raw.replace(watermark, "")
                raw = raw.replace("\n\n", "\n").strip()
            if not raw:
                continue
            key = _first_line_key(raw)
            if key is None:
                continue
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            header = f"<!-- chunk {chunk_num:02d} {path.name} from {folder.name} -->\n"
            parts.append(header + raw)
            # No per-page output; only merged doc.md is written.

    out_doc.parent.mkdir(parents=True, exist_ok=True)
    out_doc.write_text("\n\n".join(parts), encoding="utf-8")
    print(f"[doc ] wrote {out_doc} ({len(parts)} pages, skipped {skipped} dups)")


def copy_images(chunks: List[Tuple[int, Path]], out_img_dir: Path) -> None:
    out_img_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for num, folder in chunks:
        img_dir = folder / "imgs"
        if not img_dir.exists():
            print(f"[warn] missing imgs/ in {folder}")
            continue
        for img in img_dir.iterdir():
            if not img.is_file():
                continue
            target = out_img_dir / img.name
            # 直接使用原名，避免破坏 doc.md 中的图片路径；重名概率极低，若发生则覆盖。
            shutil.copy2(img, target)
            count += 1
    print(f"[imgs] copied {count} images to {out_img_dir}")


def mirror_images_for_papers(src_img_dir: Path, paper_img_dir: Path) -> None:
    """Copy merged imgs/ into papers/imgs/ so split sections can render images."""
    if not src_img_dir.exists():
        print(f"[warn] source imgs missing: {src_img_dir}")
        return
    paper_img_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for img in src_img_dir.iterdir():
        if not img.is_file():
            continue
        target = paper_img_dir / img.name
        shutil.copy2(img, target)
        count += 1
    print(f"[imgs] mirrored {count} images to {paper_img_dir}")


def process_all(chunk_root: Path, output_root: Path) -> None:
    if not chunk_root.exists():
        raise FileNotFoundError(f"chunk root not found: {chunk_root}")
    groups = find_chunk_groups(chunk_root)
    if not groups:
        print("no chunk groups found")
        return
    for prefix, chunks in groups.items():
        out_dir = output_root / prefix
        concat_docs(chunks, out_dir / "doc.md")
        copy_images(chunks, out_dir / "imgs")
        mirror_images_for_papers(out_dir / "imgs", out_dir / "papers" / "imgs")
        postprocess_sections(out_dir / "doc.md", out_dir / "papers")


def postprocess_sections(merged_doc: Path, out_dir: Path) -> None:
    """Split merged doc by level-1 heading.

    The first section that passes both gates (## summary present AND len >= MIN_SECTION_LEN)
    is kept; every subsequent section is kept without further gating. Output filenames are
    derived from the level-1 heading text without numeric prefixes. """
    if not merged_doc.exists():
        print(f"[warn] merged doc not found: {merged_doc}")
        return
    text = merged_doc.read_text(encoding="utf-8", errors="ignore")
    matches = list(re.finditer(r"(?m)^# .+", text))
    if not matches:
        print(f"[warn] no level-1 headings found in {merged_doc}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    kept = 0
    skipped_short = 0
    skipped_no_summary = 0
    passed_gate = False

    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        if not section:
            continue

        title = m.group().lstrip("#").strip()
        slug_base = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower() or f"section_{idx+1:03d}"

        if not passed_gate:
            if len(section) < MIN_SECTION_LEN:
                skipped_short += 1
                continue
            if not re.search(r"(?im)^##\s*summary\b", section):
                skipped_no_summary += 1
                continue
            passed_gate = True

        slug = slug_base
        suffix = 1
        while (out_dir / f"{kept+1:03d}_{slug}.md").exists():
            slug = f"{slug_base}_{suffix}"
            suffix += 1

        (out_dir / f"{kept+1:03d}_{slug}.md").write_text(section, encoding="utf-8")
        kept += 1

    print(
        f"[split] {merged_doc} -> {kept} kept, {skipped_short} too short, {skipped_no_summary} without ##summary"
    )


if __name__ == "__main__":
    process_all(CHUNK_ROOT, OUTPUT_ROOT)
