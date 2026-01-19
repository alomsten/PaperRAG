"""
Gradio UI for MedicalRAGSystem: ask a question, show retrieved child chunks,
corresponding parent blocks, and the final LLM answer.
"""

import os
import json
from typing import List, Dict

import gradio as gr
from rag_demo import MedicalRAGSystem, TextNode, Settings, RetrievalHit

# Optional: set defaults via env
DATA_DIR = os.getenv("RAG_DATA_DIR", "output")
PERSIST_DIR = os.getenv("RAG_PERSIST_DIR", "./storage")
CHUNK_CHARS = int(os.getenv("PARAGRAPH_CHUNK_CHARS", "1200"))
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))


def ensure_parent_map(rag: MedicalRAGSystem) -> None:
    """Rebuild parent_text_map if missing (cheap: no embeddings)."""
    if rag.parent_text_map:
        return
    docs = rag.load_documents()
    parents = rag._build_parent_nodes(docs)
    rag.parent_text_map = {node.node_id: node.text for node in parents}


def format_children(children: List[RetrievalHit], limit_chars: int = 400) -> str:
    lines: List[str] = []
    for idx, hit in enumerate(children, start=1):
        node: TextNode = hit.node
        meta: Dict = node.metadata or {}
        score = hit.score if hit.score is not None else 0.0
        vec_score = getattr(hit, "vec_score", 0.0) or 0.0
        kw_score = getattr(hit, "kw_score", 0.0) or 0.0
        parent_id = meta.get("parent_node_id") or node.node_id
        header = meta.get("section_header") or ""
        src = meta.get("file_name") or meta.get("filename") or ""
        doc_title = meta.get("doc_title") or ""
        doc_doi = meta.get("doc_doi") or ""
        doc_authors = meta.get("doc_authors") or []
        authors_str = ", ".join(doc_authors) if doc_authors else ""
        snippet = (node.text or "").strip()
        label_parts = [
            f"**#{idx}** score={score:.4f} (vec={vec_score:.4f}, kw={kw_score:.4f})",
            f"title={doc_title}" if doc_title else "title=?",
            f"doi={doc_doi}" if doc_doi else "doi=?",
            f"authors={authors_str}" if authors_str else "authors=?",
            f"parent={parent_id}",
            f"header={header}",
            f"source={src}",
        ]
        label = " | ".join(label_parts)
        body = snippet if len(snippet) <= limit_chars else snippet[:limit_chars] + "..."
        lines.append(f"{label}\n\n{body}")
    return "\n\n---\n\n".join(lines) if lines else "(no hits)"


def format_parents(parent_map: Dict[str, str], limit_chars: int = 1200) -> str:
    lines: List[str] = []
    for idx, (pid, ptext) in enumerate(parent_map.items(), start=1):
        text = (ptext or "").strip()
        body = text if len(text) <= limit_chars else text[:limit_chars] + "..."
        lines.append(f"**Parent {idx}** ({pid})\n\n{body}")
    return "\n\n---\n\n".join(lines) if lines else "(no parents)"


def answer_question(question: str, top_k: int, disable_kw: bool) -> tuple[str, str, str, str]:
    question = (question or "").strip()
    if not question:
        return "请先输入问题。", "", ""

    use_kw = not disable_kw
    kw_topk = 0 if disable_kw else top_k
    beta = 0.0 if disable_kw else 0.15

    try:
        children_hits = rag_system.dual_retrieve_hits(
            question,
            top_k_vector=top_k,
            top_k_keyword=kw_topk,
            merge_top_k=top_k,
            beta=beta,
            use_keyword=use_kw,
        )
    except Exception as exc:  # noqa: BLE001
        return f"检索出错: {exc}", "", "", ""

    # Build parent map
    parent_map: Dict[str, str] = {}
    for hit in children_hits:
        node: TextNode = hit.node
        meta: Dict = node.metadata or {}
        parent_id = meta.get("parent_node_id") or node.node_id
        if parent_id not in parent_map:
            parent_map[parent_id] = rag_system.parent_text_map.get(parent_id, node.text or "")

    # Build reference labels for parents
    parent_infos = []
    for idx, (pid, ptext) in enumerate(parent_map.items(), start=1):
        ref_label = f"P{idx}"
        # pick any hit whose parent matches
        meta = {}
        for h in children_hits:
            m = h.node.metadata or {}
            if (m.get("parent_node_id") or h.node.node_id) == pid:
                meta = m
                break
        parent_infos.append(
            {
                "label": ref_label,
                "parent_id": pid,
                "title": meta.get("doc_title") or meta.get("section_header") or "",
                "doi": meta.get("doc_doi") or "",
                "authors": ", ".join(meta.get("doc_authors") or []),
                "text": (ptext or "").strip(),
            }
        )

    # Build context with reference labels
    context_parts = []
    for p in parent_infos:
        context_parts.append(f"[{p['label']}]\n{p['text']}")
    context = "\n\n---\n\n".join(context_parts)

    prompt = (
        "你是医学论文助手。请基于下列上下文回答用户问题，"
        "如果无法确定答案请说明未知。\n\n"
        "回答时，请在每句话或每个要点末尾附上来源标记 [P#]。"
        "上下文中每个段落前都有对应的引用标签（如 [P1]、[P2]），请根据实际使用的段落标注引用。"
        "如果一句话使用了多个段落，可连续标记如 [P1][P2]。\n\n"
        f"上下文:\n{context}\n\n问题: {question}\n\n回答:"
    )

    try:
        llm_resp = Settings.llm.complete(prompt)
        answer_text = llm_resp.text if hasattr(llm_resp, "text") else str(llm_resp)
    except Exception as exc:  # noqa: BLE001
        answer_text = f"LLM 调用失败: {exc}"

    # Wrap reference markers for front-end click handling
    import re

    def wrap_refs(text: str) -> str:
        return re.sub(r"\[(P\d+)\]", r'<span class="ref-tag" data-ref="\1">[\1]</span>', text)

    answer_marked = wrap_refs(answer_text)

    # Build source table HTML + JS for click-to-view details
    rows = []
    for p in parent_infos:
        rows.append(
            f"<tr><td>{p['label']}</td><td>{p['title']}</td><td>{p['doi']}</td><td>{p['authors']}</td></tr>"
        )
    ref_meta = json.dumps(parent_infos, ensure_ascii=False)
    source_table = (
        "<table class='src-table'><thead><tr><th>引用</th><th>标题</th><th>DOI</th><th>作者</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        + f"<script>window.REF_META={ref_meta};function renderRefDetail(label){{const box=document.getElementById('ref-detail-box');if(!box)return;const m=(window.REF_META||[]).find(x=>x.label===label);if(!m){{box.innerHTML='未找到引用 '+label;return;}}box.innerHTML=`<b>${{m.label}}</b> · ${{m.title||'无标题'}}<br>DOI: ${{m.doi||'—'}}<br>作者: ${{m.authors||'—'}}`;}}document.addEventListener('click',e=>{{if(e.target.classList.contains('ref-tag')){{const lb=e.target.getAttribute('data-ref');renderRefDetail(lb);}}}});</script>"
    )

    children_md = format_children(children_hits)
    parents_md = format_parents(parent_map)
    return answer_marked, children_md, parents_md, source_table


# Initialize system
rag_system = MedicalRAGSystem(
    data_dir=DATA_DIR,
    persist_dir=PERSIST_DIR,
    paragraph_chunk_chars=CHUNK_CHARS,
)

# Try to load existing index; avoid rebuild unless needed.
try:
    rag_system.create_index(force_rebuild=False)
except Exception:
    # Fallback to rebuild if loading fails
    rag_system.create_index(force_rebuild=True)

ensure_parent_map(rag_system)

# 创建现代蓝色科技主题（强制亮色模式）
modern_blue_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
).set(
    body_background_fill="linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%)",
    body_text_color="#1e293b",
    button_primary_background_fill="#3b82f6",
    button_primary_background_fill_hover="#2563eb",
    button_primary_text_color="white",
    border_color_primary="#bfdbfe",
    input_background_fill="white",
    input_border_color="#bfdbfe",
    block_background_fill="white",
    block_border_color="#e0e7ff",
    block_label_text_color="#1e40af",
)

with gr.Blocks(
    title="Medical RAG QA - 医学文献智能问答系统",
    theme=modern_blue_theme,
) as demo:
    gr.HTML("""
        <div style="text-align: center; padding: 20px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; font-size: 2.5em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                🔬 医学文献智能问答系统
            </h1>
            <p style="color: #e8f4ff; margin-top: 10px; font-size: 1.1em;">基于 RAG 技术的文献检索与分析平台</p>
        </div>
    """)

    with gr.Row():
        # 左侧边栏 - 参数设置区
        with gr.Column(scale=1, elem_classes=["sidebar"]):
            gr.Markdown("### ⚙️ 检索设置", elem_classes=["sidebar-title"])
            
            question_box = gr.Textbox(
                label="📝 输入问题",
                placeholder="请输入您的医学文献检索问题...",
                lines=5,
                elem_classes=["question-input"]
            )
            
            topk_slider = gr.Slider(
                1, 20,
                value=DEFAULT_TOP_K,
                step=1,
                label="🎯 检索数量 (Top K)",
                info="返回最相关的 K 个文献片段"
            )
            
            disable_kw = gr.Checkbox(
                value=False,
                label="🔍 纯向量检索模式",
                info="禁用 BM25 关键词匹配，仅使用语义向量检索"
            )
            
            ask_btn = gr.Button(
                "🚀 开始检索",
                variant="primary",
                size="lg",
                elem_classes=["search-button"]
            )
            
            gr.Markdown("""
                ---
                #### 💡 使用提示
                - 尽量使用完整的问题描述
                - 可使用医学专业术语
                - 支持中英文混合检索
            """, elem_classes=["tips-box"])

        # 右侧主展示区
        with gr.Column(scale=3, elem_classes=["main-content"]):
            # 上排：回答与引用
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### 📄 智能回答", elem_classes=["section-title"])
                    answer_out = gr.HTML(elem_classes=["answer-box", "content-box"])
                
                with gr.Column(scale=1):
                    gr.Markdown("### 📚 引用来源", elem_classes=["section-title"])
                    gr.Markdown("_点击回答中的 [P#] 标记查看详细信息_", elem_classes=["hint-text"])
                    source_table = gr.HTML(elem_classes=["source-box", "content-box"])
            
            # 下排：检索详情
            gr.Markdown("### 🔎 检索详情", elem_classes=["section-title"])
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 命中片段", elem_classes=["subsection-title"])
                    children_out = gr.Markdown(elem_classes=["children-box", "content-box"])
                
                with gr.Column(scale=1):
                    gr.Markdown("#### 完整上下文", elem_classes=["subsection-title"])
                    parents_out = gr.Markdown(elem_classes=["parents-box", "content-box"])

    ask_btn.click(
        answer_question,
        inputs=[question_box, topk_slider, disable_kw],
        outputs=[answer_out, children_out, parents_out, source_table],
    )

if __name__ == "__main__":
    css_rules = """
    /* 全局样式 - 强制亮色模式 */
    :root {
        color-scheme: light !important;
    }
    
    body, .gradio-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        color: #1e293b !important;
    }
    
    /* 确保所有文本默认可见 */
    * {
        color: #1e293b !important;
    }
    
    /* 标签和提示文字 */
    label, .label, .gr-block-label, .gr-form-label,
    .gr-info, .info, span, p, div {
        color: #1e293b !important;
    }
    
    /* 侧边栏样式 */
    .sidebar {
        background: white !important;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e0e7ff;
    }
    
    .sidebar label,
    .sidebar .gr-block-label,
    .sidebar p,
    .sidebar span {
        color: #1e293b !important;
    }
    
    .sidebar-title {
        color: #1e40af;
        font-weight: 700;
        font-size: 1.25em;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid #3b82f6;
    }
    
    .question-input textarea {
        border: 2px solid #bfdbfe !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
        color: #1e293b !important;
        background: #eff6ff !important;
    }
    
    .question-input textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        background: #dbeafe !important;
    }
    
    /* 输入框下的提示文字 */
    .question-input .gr-info,
    .question-input + .gr-info,
    .gr-form .gr-info {
        color: #64748b !important;
    }
    
    .search-button {
        margin-top: 20px;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 1.1em !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .search-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px -1px rgba(59, 130, 246, 0.5) !important;
    }
    
    .tips-box {
        background: #eff6ff !important;
        padding: 16px;
        border-radius: 12px;
        margin-top: 20px;
        border-left: 4px solid #3b82f6;
        font-size: 0.9em;
        color: #1e40af;
    }
    
    /* 主内容区样式 */
    .main-content {
        padding-left: 20px;
    }
    
    .section-title {
        color: #1e40af;
        font-weight: 700;
        font-size: 1.4em;
        margin-bottom: 16px;
        padding-left: 8px;
        border-left: 4px solid #3b82f6;
    }
    
    .subsection-title {
        color: #3b82f6;
        font-weight: 600;
        font-size: 1.1em;
        margin-bottom: 12px;
    }
    
    .hint-text {
        color: #64748b;
        font-size: 0.9em;
        font-style: italic;
        margin-bottom: 12px;
    }
    
    .content-box {
        background: white !important;
        border: 2px solid #bfdbfe;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
        transition: border-color 0.3s ease;
    }
    
    .answer-box.content-box {
        min-height: 500px;
        max-height: 700px;
    }
    
    /* 内容框文本样式 - 精确控制 */
    .content-box .markdown-body,
    .content-box .prose,
    .content-box p,
    .content-box div:not(.ref-tag),
    .content-box span:not(.ref-tag),
    .content-box h1,
    .content-box h2,
    .content-box h3,
    .content-box h4,
    .content-box h5,
    .content-box h6,
    .content-box li,
    .content-box strong,
    .content-box b,
    .content-box em,
    .content-box i {
        color: #1e293b !important;
        background: transparent !important;
    }
    
    .content-box:hover {
        border-color: #93c5fd;
    }
    
    .answer-box {
        font-size: 1.05em;
        line-height: 1.8;
    }
    
    .answer-box p,
    .answer-box div:not(.ref-tag),
    .answer-box span:not(.ref-tag) {
        color: #1e293b !important;
    }
    
    .source-box {
        max-height: 300px;
    }
    
    .source-box p,
    .source-box div {
        color: #1e293b !important;
    }
    
    .detail-box {
        max-height: 180px;
        margin-top: 12px;
    }
    
    .detail-box p,
    .detail-box div {
        color: #1e293b !important;
    }
    
    .ref-placeholder {
        color: #64748b !important;
        text-align: center;
        padding: 40px 20px;
        font-size: 0.95em;
        line-height: 1.6;
    }
    
    .children-box,
    .parents-box {
        max-height: 400px;
        font-size: 0.95em;
    }
    
    .children-box p,
    .children-box div,
    .children-box span,
    .children-box strong,
    .children-box b,
    .children-box em,
    .children-box code,
    .parents-box p,
    .parents-box div,
    .parents-box span,
    .parents-box strong,
    .parents-box b,
    .parents-box em,
    .parents-box code {
        color: #1e293b !important;
    }
    
    /* 引用标签样式 */
    .ref-tag {
        color: #2563eb;
        cursor: pointer;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        background: #dbeafe;
        transition: all 0.2s ease;
        display: inline-block;
        margin: 0 2px;
    }
    
    .ref-tag:hover {
        background: #3b82f6;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }
    
    /* 引用表格样式 */
    .src-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9em;
        background: white !important;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .src-table th, .src-table td {
        border: 1px solid #e0e7ff;
        padding: 10px 12px;
        text-align: left;
        color: #1e293b !important;
        background: white !important;
    }
    
    .src-table th {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85em;
        letter-spacing: 0.5px;
    }
    
    .src-table tbody tr {
        transition: background-color 0.2s ease;
        background: white !important;
    }
    
    .src-table tbody tr td {
        color: #1e293b !important;
        background: white !important;
    }
    
    .src-table tbody tr:nth-child(even) {
        background: #f8fafc !important;
    }
    
    .src-table tbody tr:nth-child(even) td {
        background: #f8fafc !important;
        color: #1e293b !important;
    }
    
    .src-table tbody tr:hover {
        background: #eff6ff !important;
    }
    
    .src-table tbody tr:hover td {
        background: #eff6ff !important;
        color: #1e293b !important;
    }
    
    /* 滚动条美化 */
    .content-box::-webkit-scrollbar {
        width: 8px;
    }
    
    .content-box::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    .content-box::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    .content-box::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    
    /* 输入框和滑块美化 */
    .gr-box input, .gr-box textarea, .gr-box select {
        border-radius: 8px !important;
        border: 2px solid #e0e7ff !important;
        background: white !important;
        color: #1e293b !important;
    }
    
    .gr-box input:focus, .gr-box textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        background: white !important;
    }
    
    /* 确保所有输入元素文字可见 */
    input, textarea, select, .gr-text-input, .gr-textbox {
        color: #1e293b !important;
        background: white !important;
    }
    
    /* Checkbox 样式 */
    input[type="checkbox"] {
        accent-color: #3b82f6 !important;
        transform: scale(1.3);
        cursor: pointer;
        width: 18px;
        height: 18px;
    }
    
    input[type="checkbox"]:checked {
        background-color: #3b82f6 !important;
        border-color: #3b82f6 !important;
    }
    
    .gr-checkbox {
        accent-color: #3b82f6 !important;
    }
    
    /* 响应式调整 */
    @media (max-width: 1024px) {
        .sidebar {
            margin-bottom: 20px;
        }
        
        .main-content {
            padding-left: 0;
        }
    }
    """
    
    port = int(os.getenv("GRADIO_SERVER_PORT", os.getenv("PORT", "7860")))
    host = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    demo.launch(
        server_name=host,
        server_port=port,
        css=css_rules,
    )
