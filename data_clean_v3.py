import argparse
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def first_heading(text: str) -> str:
    for line in text.splitlines():
        m = re.match(r"^#+\s+(.+)", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def slugify(text: str, fallback: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]+", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text or fallback


def merge_md_files(md_files: List[Path]) -> str:
    def dedupe_key(text: str) -> str:
        lines = []
        for ln in text.splitlines():
            ln = ln.strip()
            lines.append(ln)
            if len(lines) >= 2:
                break
        return "\n".join(lines)

    seen = set()
    parts = []
    for p in md_files:
        content = read_text(p).strip()
        if not content:
            continue
        key = dedupe_key(content)
        if key in seen:
            continue
        seen.add(key)
        parts.append(content)
    return "\n\n".join(parts).strip()


def split_articles(full_text: str) -> List[Tuple[str, str]]:
    """
    按一级标题切分，定位首个包含二级标题 "summary" 的文章，
    丢弃其前的内容，返回该文章及其后的所有文章。
    """

    def has_summary(text: str) -> bool:
        for ln in text.splitlines():
            if re.match(r"^##\s+summary\s*$", ln.strip(), re.IGNORECASE):
                return True
        return False

    sections: List[Tuple[str, str]] = []
    title: str | None = None
    buf: List[str] = []

    for line in full_text.splitlines():
        m = re.match(r"^#\s+(.+)", line.strip())
        if m:
            if title is not None and buf:
                content = "\n".join(buf).strip()
                sections.append((title, content))
            title = m.group(1).strip()
            buf = [line]
        else:
            if title is not None:
                buf.append(line)

    if title is not None and buf:
        content = "\n".join(buf).strip()
        sections.append((title, content))

    start_idx = None
    for i, (_, content) in enumerate(sections):
        if has_summary(content):
            start_idx = i
            break

    if start_idx is None:
        return []

    return sections[start_idx:]


def make_unique_slug(base: str, used: set[str]) -> str:
    slug = base
    idx = 1
    while slug in used:
        slug = f"{base}-{idx}"
        idx += 1
    used.add(slug)
    return slug


def copy_imgs(src_dirs: List[Path], dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in src_dirs:
        imgs = src / "imgs"
        if imgs.is_dir():
            for f in imgs.iterdir():
                if f.is_file():
                    target = dst_dir / f.name
                    try:
                        shutil.copy2(f, target)
                    except Exception:
                        pass


def save_doc(dst_dir: Path, base_name: str, content: str) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    (dst_dir / base_name).write_text(content, encoding="utf-8")


def process_chunk_sets(input_root: Path, output_root: Path):
    """处理根目录下名字包含 _chunk_ 的文件夹：先合并成整刊，再按文章拆分。"""
    # 分组：前缀 -> [chunk_dir]
    groups: Dict[str, List[Path]] = {}
    for d in input_root.iterdir():
        if d.is_dir() and "_chunk_" in d.name:
            prefix = re.sub(r"_chunk_\d+$", "", d.name)
            groups.setdefault(prefix, []).append(d)

    for prefix, dirs in groups.items():
        dirs.sort()
        dst_dir = output_root / prefix
        imgs_dst = dst_dir / "imgs"

        # 先合并 doc_*.md 成整刊 doc.md（跨 chunk 去重，保持页序）
        md_files: List[Path] = []
        for chunk_dir in dirs:
            md_files.extend(sorted(chunk_dir.glob("doc_*.md")))

        merged_issue = merge_md_files(md_files)
        if not merged_issue:
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)
        copy_imgs(dirs, imgs_dst)
        save_doc(dst_dir, "doc.md", merged_issue)

        # 再按文章切分并保存
        articles = split_articles(merged_issue)
        used_slugs: set[str] = set()
        for title, content in articles:
            base_slug = slugify(title, fallback="article")
            slug = make_unique_slug(base_slug, used_slugs)
            fname = f"{slug}.md"
            save_doc(dst_dir, fname, content)


def collect_numbered_docs(folder: Path) -> List[Path]:
    docs = []
    for p in folder.glob("doc_*.md"):
        m = re.search(r"(\d+)", p.stem)
        idx = int(m.group(1)) if m else 0
        docs.append((idx, p))
    docs.sort(key=lambda x: x[0])
    return [p for _, p in docs]


def process_volume_folder(volume_dir: Path, output_root: Path, min_count: int = 5):
    dst_dir = output_root / volume_dir.name
    imgs_dst = dst_dir / "imgs"

    # 先处理 chunk 子文件夹成组
    entries = [p for p in volume_dir.iterdir() if p.is_dir()]
    chunk_groups: Dict[str, List[Path]] = {}
    normal_dirs: List[Path] = []
    for d in entries:
        if "_chunk_" in d.name:
            key = re.sub(r"_chunk_\d+$", "", d.name)
            chunk_groups.setdefault(key, []).append(d)
        else:
            normal_dirs.append(d)

    # 处理 chunk 组：视为已是整篇文章，合并去重后按一级标题命名直接保存
    for key, dirs in chunk_groups.items():
        dirs.sort()
        md_files: List[Path] = []
        for d in dirs:
            md_files.extend(sorted(d.glob("doc*.md")))
        if not md_files:
            continue
        merged = merge_md_files(md_files)
        if not merged:
            continue
        copy_imgs(dirs, imgs_dst)
        title = first_heading(merged) or key
        fname = slugify(title, fallback=key) + ".md"
        save_doc(dst_dir, fname, merged)

    # 处理普通子文件夹（doc_0.md 等，页数<min_count则跳过）
    for sub in normal_dirs:
        md_files = collect_numbered_docs(sub)
        if len(md_files) < min_count:
            continue
        merged = merge_md_files(md_files)
        if not merged:
            continue
        copy_imgs([sub], imgs_dst)
        title = first_heading(merged) or sub.name
        fname = slugify(title, fallback=sub.name) + ".md"
        save_doc(dst_dir, fname, merged)


def process_input(input_root: Path, output_root: Path):
    process_chunk_sets(input_root, output_root)

    for d in input_root.iterdir():
        if not d.is_dir():
            continue
        if "_chunk_" in d.name:
            # 顶层 chunk 目录已在 process_chunk_sets 里处理
            continue
        # 顶层非 chunk 目录（含 Volume 与普通）统一走子目录处理逻辑
        process_volume_folder(d, output_root, min_count=5)


def main():
    parser = argparse.ArgumentParser(description="Clean and merge markdown data.")
    parser.add_argument("--input_root", default="input", help="原始数据根目录")
    parser.add_argument("--output_root", default="output", help="输出根目录")
    args = parser.parse_args()

    input_root = Path(args.input_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    process_input(input_root, output_root)
    print(f"Done. Output at {output_root}")


if __name__ == "__main__":
    main()
