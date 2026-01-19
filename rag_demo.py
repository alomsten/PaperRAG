"""
基于LlamaIndex的RAG系统
用于检索Volume 399, Issue 10337中的科技文献markdown文件
使用基于markdown标题的分块策略
"""

import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from rank_bm25 import BM25Okapi


class RetrievalHit:
    """统一的检索结果封装，包含向量分、关键词分和融合分。"""

    def __init__(self, node: TextNode, vec_score: float = 0.0, kw_score: float = 0.0, kw_raw: float = 0.0):
        self.node = node
        self.vec_score = vec_score or 0.0
        self.kw_score = kw_score or 0.0  # 已平滑后的关键词分
        self.kw_raw = kw_raw or 0.0      # 未平滑的原始关键词累计（命中/回退得分）
        self.score = 0.0                 # 融合后的总分


class BM25KeywordIndexer:
    """本地 BM25 关键词/词袋检索，无需 LLM 与网络。"""

    def __init__(
        self,
        nodes: Sequence[TextNode],
        token_pattern: str = r"[a-zA-Z]{2,}",
        boost_header: bool = True,
    ) -> None:
        self.token_pattern = token_pattern
        self.boost_header = boost_header
        self.node_lookup: Dict[str, TextNode] = {n.node_id: n for n in nodes}
        self.node_ids: List[str] = []
        self.tokenized_docs: List[List[str]] = []

        for node in nodes:
            tokens = self._tokenize_node(node)
            if not tokens:
                continue
            self.node_ids.append(node.node_id)
            self.tokenized_docs.append(tokens)

        self.bm25 = BM25Okapi(self.tokenized_docs) if self.tokenized_docs else None

    @classmethod
    def from_disk(cls, data: Dict[str, Any], nodes: Sequence[TextNode]) -> "BM25KeywordIndexer":
        # 若存在磁盘数据可用则加载，否则直接重建（重建成本极低且完全本地）。
        token_pattern = data.get("token_pattern", r"[a-zA-Z]{2,}") if isinstance(data, dict) else r"[a-zA-Z]{2,}"
        instance = cls(nodes, token_pattern=token_pattern)
        return instance

    def _tokenize_text(self, text: str) -> List[str]:
        tokens = re.findall(self.token_pattern, text.lower())
        if not tokens:
            tokens = re.findall(r"\w{2,}", text.lower())
        return tokens

    def _tokenize_node(self, node: TextNode) -> List[str]:
        header = node.metadata.get("section_header", "") if node.metadata else ""
        text = node.text or ""
        if self.boost_header and header:
            combined = f"{header} {header} {text}"
        else:
            combined = f"{header} {text}" if header else text
        return self._tokenize_text(combined)

    def retrieve(self, query: str, top_k: int = 10) -> List[RetrievalHit]:
        if not self.bm25 or not self.node_ids:
            return []

        q_tokens = self._tokenize_text(query)
        if not q_tokens:
            return []

        scores = self.bm25.get_scores(q_tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        hits: List[RetrievalHit] = []
        for idx, raw_score in ranked[:top_k]:
            if raw_score <= 0:
                continue
            node_id = self.node_ids[idx]
            node = self.node_lookup.get(node_id)
            if not node:
                continue
            kw_norm = math.log1p(raw_score)
            hits.append(RetrievalHit(node=node, kw_score=kw_norm, kw_raw=float(raw_score)))

        return hits


class MedicalRAGSystem:
    """医学文献RAG检索系统"""
    
    def __init__(
        self,
        data_dir: str = "Volume 399, Issue 10337",
        persist_dir: str = "./storage",
        model_name: str = "gpt-4",
        embedding_model: str = "text-embedding-3-small",
        paragraph_chunk_chars: int = 1200,
        max_embed_chars: int = 6000,
    ):
        """
        初始化RAG系统
        
        Args:
            data_dir: 文档目录路径
            persist_dir: 索引持久化目录
            model_name: LLM模型名称
            embedding_model: 嵌入模型名称
        """
        # 加载环境变量（如果存在 .env 文件）
        load_dotenv()

        self.data_dir = data_dir
        self.persist_dir = persist_dir

        # 解析环境变量覆盖
        env_model_name = os.getenv("LLM_MODEL_ID") or os.getenv("OPENAI_MODEL_ID")
        env_embedding_model = (
            os.getenv("EMBEDDING_MODEL_ID")
            or os.getenv("OPENAI_EMBEDDING_MODEL")
        )
        self.model_name = env_model_name or model_name
        self.embedding_model = env_embedding_model or embedding_model

        chunk_chars_env = (
            os.getenv("PARAGRAPH_CHUNK_CHARS")
            or os.getenv("PARAGRAPH_CHUNK_SIZE")
        )
        try:
            self.paragraph_chunk_chars = (
                int(chunk_chars_env) if chunk_chars_env else paragraph_chunk_chars
            )
        except ValueError:
            self.paragraph_chunk_chars = paragraph_chunk_chars

        self.max_embed_chars = max_embed_chars

        # 处理API代理配置
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        api_base = os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL")
        timeout = os.getenv("OPENAI_TIMEOUT") or os.getenv("LLM_TIMEOUT")
        timeout_value = float(timeout) if timeout else None

        llm_kwargs = {
            "model": self.model_name,
            "temperature": 0.1,
        }
        embed_kwargs = {
            "model": self.embedding_model,
        }

        if api_key:
            llm_kwargs["api_key"] = api_key
            embed_kwargs["api_key"] = api_key
        if api_base:
            llm_kwargs["api_base"] = api_base
            embed_kwargs["api_base"] = api_base
        if timeout_value is not None:
            llm_kwargs["timeout"] = timeout_value
            embed_kwargs["timeout"] = timeout_value

        # 配置LlamaIndex全局设置
        Settings.llm = OpenAI(**llm_kwargs)
        Settings.embed_model = OpenAIEmbedding(**embed_kwargs)

        self.index = None
        self.query_engine = None
        self.vector_index = None
        self.keyword_index = None
        self.parent_text_map = {}
        self.keyword_index = None
        self.doc_metadata: Dict[str, Dict[str, Any]] = {}

    def _persist_keyword_index(self):
        if not self.keyword_index:
            return
        target = Path(self.persist_dir) / "keyword_index.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        tokenized_docs = getattr(self.keyword_index, "tokenized_docs", [])
        node_ids = getattr(self.keyword_index, "node_ids", [])
        data = {
            "type": "bm25",
            "token_pattern": getattr(self.keyword_index, "token_pattern", r"[a-zA-Z]{2,}"),
            "node_ids": node_ids,
            "tokenized_docs": tokenized_docs,
        }
        with target.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def _persist_parent_map(self):
        if not self.parent_text_map:
            return
        target = Path(self.persist_dir) / "parent_text_map.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            json.dump(self.parent_text_map, f, ensure_ascii=False)

    def _persist_doc_metadata(self):
        if not self.doc_metadata:
            return
        target = Path(self.persist_dir) / "doc_metadata.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            json.dump(self.doc_metadata, f, ensure_ascii=False)

    def _load_doc_metadata(self) -> Dict[str, Dict[str, Any]]:
        meta_path = Path(self.persist_dir) / "doc_metadata.json"
        if meta_path.exists():
            try:
                with meta_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {}

    def _build_parent_nodes(self, documents: List):
        """将一个文档切分为：标题行 + 直到下一个标题前的正文，作为父节点"""
        parent_nodes: List[TextNode] = []
        heading_re = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)

        for doc in documents:
            text = (doc.text or "").replace("\r\n", "\n").replace("\r", "\n")
            metadata = dict(doc.metadata or {})
            file_path = metadata.get("file_path") or metadata.get("filename") or metadata.get("file_name")
            file_name = Path(file_path).name if file_path else metadata.get("file_name", "")
            folder_name = Path(file_path).parent.name if file_path else "unknown_folder"
            doc_stem = Path(file_name).stem if file_name else "doc"
            doc_id = f"{folder_name}__{doc_stem}"
            base_id = f"{doc_id}"

            matches = list(heading_re.finditer(text))
            # 如果没有标题，就把全文当成一个父块
            if not matches:
                node_id = f"{base_id}_h0"
                parent_nodes.append(
                    TextNode(
                        text=text.strip(),
                        metadata={**metadata, "section_header": "", "doc_id": doc_id, "doc_title": ""},
                        id_=node_id,
                    )
                )
                continue

            # 处理前言（第一标题前）
            first_start = matches[0].start()
            if first_start > 0:
                preface = text[:first_start].strip()
                if preface:
                    node_id = f"{base_id}_preface"
                    parent_nodes.append(
                        TextNode(
                            text=preface,
                            metadata={**metadata, "section_header": "", "doc_id": doc_id, "doc_title": ""},
                            id_=node_id,
                        )
                    )

            # 处理每个标题块
            for idx, m in enumerate(matches):
                start = m.start()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
                block = text[start:end].strip()
                heading_text = m.group(2).strip()
                node_id = f"{base_id}_h{idx+1}"
                parent_nodes.append(
                    TextNode(
                        text=block,
                        metadata={**metadata, "section_header": heading_text, "doc_id": doc_id, "doc_title": heading_text},
                        id_=node_id,
                    )
                )

        return parent_nodes

    def _chunk_paragraph(self, paragraph: str) -> List[str]:
        """将段落拆分为不打断句子的子块，优先在句末边界分包"""
        def _normalize(text: str) -> str:
            # 统一行结束符并压缩多余空白
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            return text.strip()

        limit = max(self.paragraph_chunk_chars, 200)
        paragraph = _normalize(paragraph)
        if not paragraph:
            return []

        # 句子切分：兼顾中英文句号/问号/感叹号，保留分隔符
        sentence_pattern = re.compile(r"(?<=[。！？!?.])\s+")
        sentences = [s.strip() for s in sentence_pattern.split(paragraph) if s.strip()]

        # 如果只有一条且长度已在限制内，直接返回
        if len(sentences) == 1 and len(sentences[0]) <= limit:
            return [sentences[0]]

        chunks: List[str] = []
        buffer = ""

        for sentence in sentences:
            # 若当前句子本身超长，单独成块以避免硬切句子
            if len(sentence) > limit:
                if buffer:
                    chunks.append(buffer.strip())
                    buffer = ""
                chunks.append(sentence)
                continue

            # 尝试将句子放入当前缓冲
            prospective = (buffer + " " + sentence).strip() if buffer else sentence
            if len(prospective) <= limit:
                buffer = prospective
            else:
                if buffer:
                    chunks.append(buffer.strip())
                buffer = sentence

        if buffer:
            chunks.append(buffer.strip())

        return chunks

    def _truncate_for_embedding(self, text: str) -> str:
        """限制单块文本长度，避免超出嵌入模型上下文。"""
        limit = max(self.max_embed_chars, 500)
        if len(text) <= limit:
            return text
        return text[:limit]

    def _apply_doc_meta_to_parents(self, parent_nodes: List[TextNode]) -> None:
        """将文档级元数据回填到父节点上，便于子块继承。"""
        if not self.doc_metadata:
            return
        for node in parent_nodes:
            meta = dict(node.metadata or {})
            doc_id = meta.get("doc_id")
            if not doc_id:
                continue
            doc_info = self.doc_metadata.get(doc_id) or {}
            if not doc_info:
                continue
            meta.update(
                {
                    "doc_id": doc_id,
                    "doc_title": doc_info.get("title", meta.get("doc_title", "")),
                    "doc_doi": doc_info.get("doi"),
                    "doc_authors": doc_info.get("authors", []),
                    "doc_authors_str": ", ".join(doc_info.get("authors", [])),
                    "doc_file_path": doc_info.get("file_path"),
                }
            )
            node.metadata = meta

    def _llm_extract_fields(self, text: str, need_doi: bool, need_authors: bool) -> Dict[str, Any]:
        fields = []
        if need_doi:
            fields.append("doi")
        if need_authors:
            fields.append("authors")

        prompt_fields = ", ".join(fields)
        prompt = f"""
                你是信息抽取助手。请仅从下方正文中抽取指定字段，输出严格的JSON格式。
                不要添加解释或额外文本。
                若未找到字段，doi 请置为 null，authors 请置为 []。

                仅抽取: {prompt_fields}

                输出格式示例:
                {{
                    "doi": <string|null>,
                    "authors": [<string>, ...]
                }}

                正文:
                {text[:4000]}
                """
        try:
            resp = Settings.llm.complete(prompt)
            raw = resp.text if hasattr(resp, "text") else str(resp)
            print(f"DEBUG LLM Output: {raw}")

            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                raw_json = match.group(0)
                data = json.loads(raw_json)
                return {
                    "doi": data.get("doi"),
                    "authors": data.get("authors") or [],
                }

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"其他错误: {e}")

        return {"doi": None, "authors": []}


    def _extract_doc_metadata(self, parent_nodes: List[TextNode], reextract: bool = False) -> Dict[str, Dict[str, Any]]:
        """基于父块顺序调用 LLM 抽取文档级 DOI 与作者信息。"""

        if not reextract:
            cached = self._load_doc_metadata()
            if cached:
                self.doc_metadata = cached
                self._apply_doc_meta_to_parents(parent_nodes)
                return cached

        doc_groups: Dict[str, List[TextNode]] = defaultdict(list)
        for node in parent_nodes:
            doc_id = node.metadata.get("doc_id") or "unknown_doc"
            doc_groups[doc_id].append(node)

        doi_pattern = re.compile(r"10\.\d{4,9}/\S+", re.IGNORECASE)
        extracted: Dict[str, Dict[str, Any]] = {}

        for doc_id, nodes in doc_groups.items():
            doi = None
            authors: List[str] = []
            title = nodes[0].metadata.get("doc_title", "") if nodes else ""
            file_path = nodes[0].metadata.get("file_path") or nodes[0].metadata.get("filename") or nodes[0].metadata.get("file_name")
            folder_name = Path(file_path).parent.name if file_path else ""

            for parent in nodes:
                text = parent.text or ""
                if need_doi := doi is None:
                    m = doi_pattern.search(text)
                    if m:
                        doi = m.group(0).strip().rstrip(".,)")
                need_authors = len(authors) == 0

                if not need_doi and not need_authors:
                    break

                fields = self._llm_extract_fields(text, need_doi=need_doi, need_authors=need_authors)
                if need_doi and fields.get("doi"):
                    doi = fields["doi"].strip()
                if need_authors and fields.get("authors"):
                    authors = [a.strip() for a in fields["authors"] if a and isinstance(a, str)]

                if doi and authors:
                    break

            extracted[doc_id] = {
                "doc_id": doc_id,
                "title": title,
                "doi": doi,
                "authors": authors,
                "file_path": file_path,
                "folder": folder_name,
            }

        self.doc_metadata = extracted
        self._apply_doc_meta_to_parents(parent_nodes)
        self._persist_doc_metadata()
        return extracted

    def _infer_doc_id(self, node: TextNode) -> str:
        meta = node.metadata or {}
        doc_id = meta.get("doc_id")
        if doc_id:
            return doc_id
        base = meta.get("parent_node_id") or node.node_id
        doc_id = re.sub(r"_(h\d+|preface|tbl\d+|p\d+_\d+)$", "", base)
        return doc_id

    def _enrich_node_metadata(self, node: TextNode) -> None:
        """为节点补充 doc 级元数据，便于检索后展示。"""
        meta = dict(node.metadata or {})
        doc_id = self._infer_doc_id(node)
        meta.setdefault("doc_id", doc_id)
        doc_info = self.doc_metadata.get(doc_id) if doc_id else None
        if doc_info:
            meta.setdefault("doc_title", doc_info.get("title"))
            meta.setdefault("doc_doi", doc_info.get("doi"))
            meta.setdefault("doc_authors", doc_info.get("authors", []))
            meta.setdefault("doc_authors_str", ", ".join(doc_info.get("authors", [])))
            meta.setdefault("doc_file_path", doc_info.get("file_path"))
        node.metadata = meta

    def get_doc_info_for_node(self, node: TextNode) -> Dict[str, Any]:
        doc_id = self._infer_doc_id(node)
        return self.doc_metadata.get(doc_id, {})

    def _split_node_into_segments(self, node: TextNode) -> List[TextNode]:
        """将标题级节点细分为段落/表格等子块，并附加溯源元信息"""
        base_metadata = dict(node.metadata)
        header = (
            base_metadata.get("header")
            or base_metadata.get("section")
            or base_metadata.get("title")
            or base_metadata.get("heading")
            or ""
        )
        source_path = (
            base_metadata.get("file_path")
            or base_metadata.get("file_name")
            or base_metadata.get("filename")
            or base_metadata.get("id")
        )
        folder_name = None
        if source_path:
            folder_name = Path(str(source_path)).parent.name

        table_pattern = re.compile(r"(<table\b[\s\S]*?</table>)", re.IGNORECASE)
        raw_segments = table_pattern.split(node.text or "")

        enhanced_nodes: List[TextNode] = []
        paragraph_index = 0
        segment_counter = 0

        for raw_segment in raw_segments:
            if not raw_segment or not raw_segment.strip():
                continue

            is_table = bool(table_pattern.fullmatch(raw_segment.strip()))

            if is_table:
                paragraph_index += 1
                segment_counter += 1
                metadata = dict(base_metadata)
                metadata.update(
                    {
                        "source_folder": folder_name,
                        "section_header": header,
                        "section_paragraph_index": paragraph_index,
                        "section_paragraph_chunk": 1,
                        "section_segment_index": segment_counter,
                        "segment_type": "table",
                        "is_table": True,
                        "parent_node_id": node.node_id,
                    }
                )
                enhanced_nodes.append(
                    TextNode(
                        text=self._truncate_for_embedding(raw_segment.strip()),
                        metadata=metadata,
                        id_=f"{node.node_id}_tbl{paragraph_index}",
                    )
                )
                continue

            cleaned_segment = raw_segment.replace("\r\n", "\n").replace("\r", "\n")
            paragraphs = [
                paragraph.strip()
                for paragraph in re.split(r"\n\s*\n", cleaned_segment)
                if paragraph.strip()
            ]

            if not paragraphs:
                continue

            for paragraph in paragraphs:
                paragraph_index += 1
                chunks = self._chunk_paragraph(paragraph)
                if not chunks:
                    continue
                for chunk_order, chunk_text in enumerate(chunks, start=1):
                    segment_counter += 1
                    chunk_text = self._truncate_for_embedding(chunk_text)
                    metadata = dict(base_metadata)
                    metadata.update(
                        {
                            "source_folder": folder_name,
                            "section_header": header,
                            "section_paragraph_index": paragraph_index,
                            "section_paragraph_chunk": chunk_order,
                            "section_segment_index": segment_counter,
                            "segment_type": "text",
                            "is_table": False,
                            "parent_node_id": node.node_id,
                        }
                    )
                    enhanced_nodes.append(
                        TextNode(
                            text=chunk_text,
                            metadata=metadata,
                            id_=f"{node.node_id}_p{paragraph_index}_{chunk_order}",
                        )
                    )

        return enhanced_nodes
        
    def collect_doc_files(self) -> List[str]:
        """递归收集目标目录下的所有 Markdown 文件。"""

        base_path = Path(self.data_dir)
        if not base_path.exists():
            raise FileNotFoundError(f"目录不存在: {self.data_dir}")

        # 递归查找所有 .md 文件（不再限定 doc.md/doc_*.md）
        doc_files = sorted(str(p) for p in base_path.rglob("*.md") if p.is_file())

        print(f"找到 {len(doc_files)} 个文档文件")
        return doc_files
    
    def load_documents(self):
        """加载文档并创建索引"""
        doc_files = self.collect_doc_files()
        
        if not doc_files:
            raise ValueError("未找到任何doc.md或doc_*.md文件")
        
        # 使用SimpleDirectoryReader加载指定的文件
        documents = []
        for file_path in doc_files:
            reader = SimpleDirectoryReader(
                input_files=[file_path],
                filename_as_id=True
            )
            docs = reader.load_data()
            documents.extend(docs)
        
        print(f"成功加载 {len(documents)} 个文档")
        return documents
    
    def create_index(
        self,
        force_rebuild: bool = False,
        build_keyword_index: bool = True,
        reextract_doc_meta: bool = False,
    ):
        """
        创建或加载向量索引
        
        Args:
            force_rebuild: 是否强制重建索引
            build_keyword_index: 是否构建关键词检索索引（BM25）。若为 False，仅构建向量索引。
            reextract_doc_meta: 是否强制重新抽取文档级 DOI/作者元信息。
        """
        # 检查是否已存在索引
        if not force_rebuild and os.path.exists(self.persist_dir):
            try:
                print("正在加载已存在的向量索引...")
                storage_context = StorageContext.from_defaults(
                    persist_dir=self.persist_dir
                )
                self.index = load_index_from_storage(storage_context)
                # 旧索引只包含向量，兼容老路径
                self.vector_index = self.index
                print("向量索引加载成功！正在补建父块映射...")

                # 补建父块映射、文档元信息与关键词倒排（不重算 embedding）
                documents = self.load_documents()
                parent_nodes = self._build_parent_nodes(documents)
                self.parent_text_map = {node.node_id: node.text for node in parent_nodes}
                self._extract_doc_metadata(parent_nodes, reextract=reextract_doc_meta)
                enhanced_nodes: List[TextNode] = []
                for node in parent_nodes:
                    enhanced_nodes.extend(self._split_node_into_segments(node))

                nodes = enhanced_nodes
                if build_keyword_index:
                    kw_file = Path(self.persist_dir) / "keyword_index.json"
                    if kw_file.exists():
                        try:
                            with kw_file.open("r", encoding="utf-8") as f:
                                kw_data = json.load(f)
                            self.keyword_index = BM25KeywordIndexer.from_disk(kw_data, nodes)
                            print("关键词索引已从磁盘加载（BM25，本地检索）")
                        except Exception as e:
                            print(f"加载关键词索引失败，将重新构建: {e}")
                            self.keyword_index = BM25KeywordIndexer(nodes)
                            self._persist_keyword_index()
                    else:
                        print("未找到关键词索引文件，将重新构建关键词索引...")
                        self.keyword_index = BM25KeywordIndexer(nodes)
                        self._persist_keyword_index()
                else:
                    print("已跳过关键词索引加载/重建（build_keyword_index=False）")

                return
            except Exception as e:
                print(f"加载索引失败: {e}")
                print("将重新构建索引...")
        
        # 加载文档
        print("正在加载文档...")
        documents = self.load_documents()
        
        # 使用自定义标题分块：标题到下一个标题之间组成一个父块，包含标题自身
        print("正在按标题范围生成父文档块...")
        parent_nodes = self._build_parent_nodes(documents)
        print(f"文档被分为 {len(parent_nodes)} 个标题级语义块")

        print("正在抽取文档级 DOI 和作者信息（按父块顺序，缺项才会继续抽取）...")
        self._extract_doc_metadata(parent_nodes, reextract=reextract_doc_meta)

        # 保留父节点文本用于父文档返回
        self.parent_text_map = {node.node_id: node.text for node in parent_nodes}

        # 将每个标题块按段落进一步切分，并附加元信息
        enhanced_nodes: List[TextNode] = []
        for node in parent_nodes:
            enhanced_nodes.extend(self._split_node_into_segments(node))

        nodes = enhanced_nodes
        print(f"段落级语义块总计 {len(nodes)} 个")
        
        # 创建向量索引
        print("正在创建向量索引...")
        self.vector_index = VectorStoreIndex(nodes)

        # 使用并发 LLM 提取关键词，构建本地倒排索引
        if build_keyword_index:
            print("正在创建关键词索引（本地 BM25，无需 LLM）...")
            self.keyword_index = BM25KeywordIndexer(nodes)

        # 兼容旧属性
        self.index = self.vector_index
        
        # 持久化索引
        print(f"正在保存索引到 {self.persist_dir}...")
        self.vector_index.storage_context.persist(persist_dir=self.persist_dir)
        if build_keyword_index:
            self._persist_keyword_index()
        self._persist_parent_map()
        print("索引创建并保存成功！")
    
    def create_query_engine(self, similarity_top_k: int = 5):
        """
        创建查询引擎
        
        Args:
            similarity_top_k: 返回的最相似文档数量
        """
        if self.index is None:
            raise ValueError("索引尚未创建，请先调用create_index()")
        
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=similarity_top_k,
            response_mode="compact"
        )
        print(f"查询引擎已创建 (top_k={similarity_top_k})")

    # === 新的企业级管道：双检索 + 简单重排 ===
    def dual_retrieve_hits(
        self,
        question: str,
        top_k_vector: int = 20,
        top_k_keyword: int = 20,
        merge_top_k: int = 5,
        alpha: float = 0.85,
        beta: float = 0.15,
        use_keyword: bool = True,
    ) -> List[RetrievalHit]:
        """双检索融合（加权和），返回带详细分数的命中列表。"""

        if self.vector_index is None:
            raise ValueError("索引尚未创建，请先调用create_index()")
        if use_keyword and self.keyword_index is None:
            raise ValueError("关键词索引尚未创建，请先调用create_index(build_keyword_index=True)")

        vec_nodes = self.vector_index.as_retriever(similarity_top_k=top_k_vector).retrieve(question)
        kw_nodes: List[RetrievalHit] = []
        if use_keyword and top_k_keyword > 0:
            kw_nodes = self.keyword_index.retrieve(question, top_k=top_k_keyword)

        merged: Dict[str, RetrievalHit] = {}

        for n in vec_nodes:
            nid = n.node.node_id
            hit = merged.get(nid) or RetrievalHit(node=n.node)
            hit.vec_score = max(hit.vec_score, n.score or 0.0)
            merged[nid] = hit

        for n in kw_nodes:
            nid = n.node.node_id
            hit = merged.get(nid) or RetrievalHit(node=n.node)
            hit.kw_score = max(hit.kw_score, n.kw_score)
            hit.kw_raw = max(hit.kw_raw, n.kw_raw)
            merged[nid] = hit

        # 计算融合分数
        for hit in merged.values():
            self._enrich_node_metadata(hit.node)
            hit.score = alpha * hit.vec_score + beta * hit.kw_score

        sorted_hits = sorted(merged.values(), key=lambda x: x.score, reverse=True)[:merge_top_k]
        return sorted_hits

    def dual_retrieve(self, question: str, top_k_vector: int = 20, top_k_keyword: int = 20, merge_top_k: int = 5):
        hits = self.dual_retrieve_hits(
            question,
            top_k_vector=top_k_vector,
            top_k_keyword=top_k_keyword,
            merge_top_k=merge_top_k,
        )
        return [h.node for h in hits]

    def rerank(self, question: str, nodes: List[TextNode], top_k: int = 5) -> List[TextNode]:
        # 简单重排：再次用向量检索打分；可后续换成跨编码器
        if not nodes:
            return []
        retriever = self.vector_index.as_retriever(similarity_top_k=max(top_k, len(nodes)))
        rescored = retriever._retrieve(query=question, nodes=nodes) if hasattr(retriever, "_retrieve") else []
        if rescored:
            rescored = sorted(rescored, key=lambda x: x.score or 0, reverse=True)[:top_k]
            return [r.node for r in rescored]
        return nodes[:top_k]

    def build_context_from_parents(self, nodes: List[TextNode]) -> str:
        seen = set()
        parts = []
        for n in nodes:
            pid = n.metadata.get("parent_node_id") or n.metadata.get("node_id")
            if pid and pid in seen:
                continue
            seen.add(pid)
            parent_text = self.parent_text_map.get(pid, "")
            if parent_text:
                parts.append(parent_text)
            else:
                parts.append(n.text)
        return "\n\n".join(parts)

    def query_enterprise(self, question: str) -> str:
        """双路检索（无重排）+父文档聚合的回答"""
        hits = self.dual_retrieve_hits(question, top_k_vector=20, top_k_keyword=20, merge_top_k=5)
        context = self.build_context_from_parents([h.node for h in hits])
        prompt = (
            "你是医学论文助手。请基于下列上下文回答用户问题，"
            "如果无法确定答案请说明未知。\n\n"
            f"上下文:\n{context}\n\n问题: {question}\n回答:"
        )
        response = Settings.llm.complete(prompt)
        return response.text if hasattr(response, "text") else str(response)
    
    def query(self, question: str) -> str:
        """
        查询RAG系统
        
        Args:
            question: 用户问题
            
        Returns:
            系统回答
        """
        if self.query_engine is None:
            raise ValueError("查询引擎尚未创建，请先调用create_query_engine()")
        
        print(f"\n问题: {question}")
        print("-" * 80)
        
        response = self.query_engine.query(question)
        
        print(f"回答: {response}")
        print("-" * 80)
        
        # 显示来源文档
        if hasattr(response, 'source_nodes'):
            print(f"\n参考了 {len(response.source_nodes)} 个文档片段:")
            for i, node in enumerate(response.source_nodes, 1):
                score = node.score if hasattr(node, 'score') else 'N/A'
                file_name = node.node.metadata.get('file_name', 'Unknown')
                print(f"  {i}. {file_name} (相似度: {score:.4f})" if isinstance(score, float) else f"  {i}. {file_name}")
        
        return str(response)
    
    def chat(self):
        """交互式聊天模式"""
        if self.query_engine is None:
            raise ValueError("查询引擎尚未创建，请先调用create_query_engine()")
        
        print("\n=== 医学文献RAG系统交互模式 ===")
        print("输入问题进行查询，输入 'quit' 或 'exit' 退出\n")
        
        while True:
            try:
                question = input("您的问题: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("再见！")
                    break
                
                if not question:
                    continue
                
                self.query(question)
                print()
                
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"错误: {e}")


def main():
    """主函数示例"""
    # 创建RAG系统实例
    rag_system = MedicalRAGSystem(
        data_dir="Volume 399, Issue 10337",
        persist_dir="./storage",
        model_name="gpt-4",
        embedding_model="text-embedding-3-small"
    )
    
    # 创建或加载索引
    # 首次运行时会构建索引，之后会自动加载已有索引
    # 如需重建索引，设置 force_rebuild=True
    rag_system.create_index(force_rebuild=False)
    
    # 创建查询引擎
    rag_system.create_query_engine(similarity_top_k=5)
    
    # 示例查询
    print("\n" + "="*80)
    print("示例查询")
    print("="*80)
    
    example_questions = [
        "What is the main finding of the PROTECT trial about intraoperative warming?",
        "What are the effects of hypothermia during surgery?",
        "Tell me about myocardial injury after non-cardiac surgery (MINS)."
    ]
    
    for question in example_questions:
        rag_system.query(question)
        print("\n")
    
    # 启动交互模式（可选）
    # rag_system.chat()


if __name__ == "__main__":
    main()
