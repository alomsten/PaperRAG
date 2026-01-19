"""Inspect vector store entries and print their text chunks."""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

VECTOR_STORE_PATH = Path("storage/default__vector_store.json")
DOCSTORE_PATH = Path("storage/docstore.json")


def extract_entries(data: Dict[str, Any]):
    # Try multiple known layouts
    if "simple_vector_store_data" in data:
        data = data["simple_vector_store_data"] or {}
    if "embedding_dict" in data:
        return data["embedding_dict"]
    if "nodes" in data:
        return data["nodes"]
    if "data" in data:
        return data["data"]
    return {}


def load_docstore() -> Dict[str, Any]:
    if not DOCSTORE_PATH.exists():
        return {}

    with DOCSTORE_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    candidates = (
        raw.get("docstore/data"),
        raw.get("data"),
        raw.get("docstore"),
    )

    store: Dict[str, Any] = {}
    for candidate in candidates:
        if isinstance(candidate, dict):
            for key, value in candidate.items():
                if key not in store:
                    if isinstance(value, dict) and "__data__" in value:
                        store[key] = value["__data__"]
                    else:
                        store[key] = value
    return store


def iter_entry_pairs(entries: Any) -> Iterable[Tuple[str, Any]]:
    if isinstance(entries, dict):
        for key, value in entries.items():
            yield str(key), value
        return

    if isinstance(entries, list):
        for idx, item in enumerate(entries, start=1):
            if isinstance(item, (list, tuple)) and len(item) == 2:
                key, value = item
            elif isinstance(item, dict):
                key = (
                    item.get("id")
                    or item.get("node_id")
                    or item.get("doc_id")
                    or item.get("ref_doc_id")
                    or f"idx-{idx}"
                )
                value = item
            else:
                key = f"idx-{idx}"
                value = item
            yield str(key), value


def extract_payload(
    key: str,
    value: Any,
    docstore: Dict[str, Any],
    metadata_dict: Dict[str, Any],
):
    text = None
    metadata = None

    if isinstance(value, dict):
        text = value.get("text")
        if text is None and "node" in value and isinstance(value["node"], dict):
            text = value["node"].get("text")
        metadata = value.get("metadata")
        if metadata is None and "node" in value and isinstance(value["node"], dict):
            metadata = value["node"].get("metadata")

    doc_entry = docstore.get(key)
    if isinstance(doc_entry, dict):
        if text is None:
            text = doc_entry.get("text")
        if metadata is None:
            metadata = doc_entry.get("metadata")

    if metadata is None and isinstance(metadata_dict, dict):
        meta_entry = metadata_dict.get(key)
        if isinstance(meta_entry, dict):
            metadata = meta_entry

    return text, normalize_metadata(metadata)


def normalize_metadata(metadata: Any) -> Any:
    if not isinstance(metadata, dict):
        return metadata

    normalized = dict(metadata)

    header = normalized.get("section_header")
    if not header or str(header).lower() == "none":
        raw_path = normalized.get("header_path") or normalized.get("section_path")
        if isinstance(raw_path, str):
            parts = [part.strip() for part in raw_path.split("/") if part.strip()]
            if parts:
                normalized["section_header"] = parts[-1]

    if "section_paragraph_chunk" in normalized and "section_segment_index" in normalized:
        try:
            chunk_idx = int(normalized["section_paragraph_chunk"])
            segment_idx = int(normalized["section_segment_index"])
            if chunk_idx != segment_idx:
                normalized.setdefault("_notes", {})[
                    "segment_index"
                ] = "Segment顺序与段内chunk不同步"
        except (TypeError, ValueError):
            pass

    return normalized


def main(limit: int = 10) -> None:
    if not VECTOR_STORE_PATH.exists():
        print(f"Vector store file not found: {VECTOR_STORE_PATH}")
        return

    with VECTOR_STORE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    entries = extract_entries(data)
    docstore = load_docstore()
    metadata_dict = data.get("metadata_dict") or {}

    try:
        total_entries = len(entries)
    except TypeError:
        entries = list(entries)  # type: ignore[arg-type]
        total_entries = len(entries)

    print(f"Loaded {total_entries} entries from {VECTOR_STORE_PATH}")

    for idx, (key, value) in enumerate(iter_entry_pairs(entries), start=1):
        if idx > limit:
            break
        text, metadata = extract_payload(key, value, docstore, metadata_dict)

        print("-" * 80)
        denominator = limit if limit else total_entries
        print(f"Entry {idx}/{denominator} | Vector ID: {key}")
        if text:
            snippet = text.strip()
            print(f"Text (first 400 chars):\n{snippet[:400]}\n")
            if len(snippet) > 400:
                print("...")
        else:
            print("[No text payload found]")
        if metadata:
            print("Metadata:")
            for m_key, m_value in metadata.items():
                print(f"  {m_key}: {m_value}")
        else:
            print("[No metadata]")


if __name__ == "__main__":
    main()
