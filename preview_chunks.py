"""
Quick preview of parent blocks and child chunks without building embeddings.
"""

import argparse
from rag_demo import MedicalRAGSystem


def preview(parents: int, children: int, data_dir: str, chunk_chars: int, snippet: int, full: bool) -> None:
    rag = MedicalRAGSystem(data_dir=data_dir, paragraph_chunk_chars=chunk_chars)
    docs = rag.load_documents()
    parents_nodes = rag._build_parent_nodes(docs)
    print(f"Found {len(parents_nodes)} parent blocks")

    for i, parent in enumerate(parents_nodes[:parents], start=1):
        header = parent.metadata.get("section_header", "")
        print("-" * 80)
        print(f"Parent {i}/{parents}: header='{header}' id={parent.node_id}")
        parent_text = (parent.text or "").strip()
        parent_display = parent_text if full else parent_text[:snippet]
        label = "full" if full else f"first {snippet} chars"
        print(f"Parent text {label}:\n{parent_display}\n")

        children_nodes = rag._split_node_into_segments(parent)
        print(f"Children count: {len(children_nodes)}")
        for j, child in enumerate(children_nodes[:children], start=1):
            meta = child.metadata or {}
            chunk_info = (
                f"p_idx={meta.get('section_paragraph_index')}, "
                f"chunk={meta.get('section_paragraph_chunk')}, "
                f"is_table={meta.get('is_table')}, "
                f"len={len((child.text or '').strip())}"
            )
            child_text = (child.text or "").strip()
            child_display = child_text if full else child_text[:snippet]
            label = "full" if full else f"first {snippet} chars"
            print(f"  Child {j}/{children} ({chunk_info}) {label}:")
            print(f"  {child_display}\n")
        if len(children_nodes) > children:
            print(f"  ... skipped {len(children_nodes) - children} more children for this parent")


def main():
    parser = argparse.ArgumentParser(description="Preview parent/child chunks without embeddings")
    parser.add_argument("--parents", type=int, default=3, help="Number of parent blocks to show")
    parser.add_argument("--children", type=int, default=3, help="Number of child chunks per parent to show")
    parser.add_argument("--data_dir", type=str, default="Volume 399, Issue 10337", help="Data directory")
    parser.add_argument("--chunk_chars", type=int, default=1200, help="Paragraph chunk size")
    parser.add_argument("--snippet", type=int, default=200, help="How many chars to display for each block")
    parser.add_argument("--full", action="store_true", help="Do not truncate; print full text for shown blocks")
    args = parser.parse_args()

    preview(
        parents=args.parents,
        children=args.children,
        data_dir=args.data_dir,
        chunk_chars=args.chunk_chars,
        snippet=args.snippet,
        full=args.full,
    )


if __name__ == "__main__":
    main()
