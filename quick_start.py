"""
简化的使用示例 - 快速开始
"""

import os
from dotenv import load_dotenv
from rag_demo import MedicalRAGSystem

# 加载环境变量
load_dotenv()

# 确保API密钥已设置
if not os.getenv("OPENAI_API_KEY"):
    print("错误: 请在.env文件中设置OPENAI_API_KEY")
    print("1. 复制.env.example为.env")
    print("2. 编辑.env文件，填入你的OpenAI API密钥")
    exit(1)

def main():
    print("="*80)
    print("医学文献RAG检索系统 - 快速开始")
    print("="*80)
    print()
    
    # 初始化系统
    print("正在初始化系统...")
    rag_system = MedicalRAGSystem(
        # 从 output 下的所有 papers/ 目录读取 md
        data_dir="output",
        persist_dir="./storage",
        model_name="gpt-4",
        embedding_model="text-embedding-3-small"
    )
    
    # 构建或加载索引                                                                                                                                                                                                                                                                                                                                                                                                                                                    
    print("\n步骤1: 构建/加载索引")
    print("-"*80)
    rag_system.create_index(force_rebuild=True, build_keyword_index=True, reextract_doc_meta=True)
    
    # 创建查询引擎
    print("\n步骤2: 创建查询引擎")
    print("-"*80)
    rag_system.create_query_engine(similarity_top_k=5)
    
    # 示例查询
    print("\n步骤3: 运行示例查询")
    print("-"*80)
    
    questions = [
        "What are the main findings about intraoperative warming in the PROTECT trial?",
        "What is myocardial injury after non-cardiac surgery (MINS)?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n[示例 {i}]")
        rag_system.query(question)
    
    # 启动交互模式
    print("\n" + "="*80)
    print("现在可以开始交互式查询")
    print("="*80)
    rag_system.chat()

if __name__ == "__main__":
    main()
