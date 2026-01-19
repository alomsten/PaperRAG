"""
配置文件
"""

# RAG系统配置
RAG_CONFIG = {
    # 数据目录
    "data_dir": "Volume 399, Issue 10337",
    
    # 索引持久化目录
    "persist_dir": "./storage",
    
    # LLM模型配置
    "llm": {
        "model_name": "gpt-4",
        "temperature": 0.1,
    },
    
    # 嵌入模型配置
    "embedding": {
        "model_name": "text-embedding-3-small",
        # 可选：使用更强大的嵌入模型
        # "model_name": "text-embedding-3-large",
    },
    
    # 查询引擎配置
    "query_engine": {
        # 返回最相似的文档数量
        "similarity_top_k": 5,
        
        # 响应模式: "compact", "tree_summarize", "simple_summarize"
        "response_mode": "compact",
    },
    
    # Markdown分块配置
    "node_parser": {
        # 使用markdown标题进行分块
        "type": "markdown",
    }
}

# 文档文件模式（首选doc.md，回退doc_*.md）
DOC_FILE_PATTERN = "doc.md"

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}
