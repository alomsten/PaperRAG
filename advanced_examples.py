"""
高级使用示例 - 展示更多功能
"""

import os
from dotenv import load_dotenv
from rag_demo import MedicalRAGSystem
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler

# 加载环境变量
load_dotenv()


def example_basic_usage():
    """基础使用示例"""
    print("\n" + "="*80)
    print("示例1: 基础使用")
    print("="*80 + "\n")
    
    rag_system = MedicalRAGSystem()
    rag_system.create_index()
    rag_system.create_query_engine()
    
    response = rag_system.query(
        "What are the main complications of perioperative hypothermia?"
    )
    
    return response


def example_custom_models():
    """自定义模型示例"""
    print("\n" + "="*80)
    print("示例2: 使用自定义模型")
    print("="*80 + "\n")
    
    rag_system = MedicalRAGSystem(
        model_name="gpt-4-turbo-preview",
        embedding_model="text-embedding-3-large"
    )
    
    rag_system.create_index()
    rag_system.create_query_engine()
    
    response = rag_system.query(
        "Summarize the key findings about cabotegravir for HIV prevention."
    )
    
    return response


def example_rebuild_index():
    """重建索引示例"""
    print("\n" + "="*80)
    print("示例3: 重建索引")
    print("="*80 + "\n")
    
    rag_system = MedicalRAGSystem()
    
    # 强制重建索引（当文档有更新时）
    rag_system.create_index(force_rebuild=True)
    rag_system.create_query_engine()
    
    print("索引已重建！")


def example_adjust_retrieval():
    """调整检索参数示例"""
    print("\n" + "="*80)
    print("示例4: 调整检索参数")
    print("="*80 + "\n")
    
    rag_system = MedicalRAGSystem()
    rag_system.create_index()
    
    # 返回更多相关文档以获得更全面的答案
    rag_system.create_query_engine(similarity_top_k=10)
    
    response = rag_system.query(
        "What are all the COVID-19 related topics discussed in these papers?"
    )
    
    return response


def example_debug_mode():
    """调试模式示例"""
    print("\n" + "="*80)
    print("示例5: 启用调试模式")
    print("="*80 + "\n")
    
    # 启用调试处理器
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])
    Settings.callback_manager = callback_manager
    
    rag_system = MedicalRAGSystem()
    rag_system.create_index()
    rag_system.create_query_engine(similarity_top_k=3)
    
    response = rag_system.query(
        "What is the mortality rate mentioned in perioperative studies?"
    )
    
    # 查看事件追踪
    print("\n调试信息:")
    print(f"LLM调用次数: {llama_debug.get_llm_token_counts()}")
    
    return response


def example_batch_queries():
    """批量查询示例"""
    print("\n" + "="*80)
    print("示例6: 批量查询")
    print("="*80 + "\n")
    
    rag_system = MedicalRAGSystem()
    rag_system.create_index()
    rag_system.create_query_engine()
    
    questions = [
        "What is the PROTECT trial about?",
        "What are the findings about HIV prevention?",
        "What COVID-19 topics are covered?",
        "What are the main surgical complications discussed?",
        "Are there any studies about children's health?",
    ]
    
    results = []
    for i, question in enumerate(questions, 1):
        print(f"\n[查询 {i}/{len(questions)}]")
        response = rag_system.query(question)
        results.append({
            "question": question,
            "answer": str(response)
        })
    
    return results


def example_filter_by_metadata():
    """元数据过滤示例（高级）"""
    print("\n" + "="*80)
    print("示例7: 使用元数据过滤")
    print("="*80 + "\n")
    
    rag_system = MedicalRAGSystem()
    rag_system.create_index()
    
    # 创建带过滤器的查询引擎
    from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
    
    # 这个示例展示如何使用元数据过滤（需要文档包含相应的元数据）
    rag_system.query_engine = rag_system.index.as_query_engine(
        similarity_top_k=5,
        # filters=MetadataFilters(
        #     filters=[
        #         MetadataFilter(key="file_type", value="clinical_trial"),
        #     ]
        # )
    )
    
    response = rag_system.query(
        "What are the clinical trial results?"
    )
    
    return response


def main():
    """运行所有示例"""
    
    # 确保API密钥已设置
    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请在.env文件中设置OPENAI_API_KEY")
        return
    
    print("="*80)
    print("RAG系统高级使用示例")
    print("="*80)
    
    # 运行示例（可以注释掉不需要的）
    
    # 基础使用
    # example_basic_usage()
    
    # 自定义模型
    # example_custom_models()
    
    # 重建索引
    # example_rebuild_index()
    
    # 调整检索参数
    example_adjust_retrieval()
    
    # 调试模式
    # example_debug_mode()
    
    # 批量查询
    # example_batch_queries()
    
    # 元数据过滤
    # example_filter_by_metadata()
    
    print("\n" + "="*80)
    print("示例运行完成！")
    print("="*80)


if __name__ == "__main__":
    main()
