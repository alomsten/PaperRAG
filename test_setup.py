"""
测试脚本 - 验证系统是否正确安装和配置
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"  ❌ Python版本过低: {version.major}.{version.minor}")
        print(f"  需要Python 3.9或更高版本")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    
    required_packages = [
        "llama_index",
        "openai",
        "dotenv",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ❌ {package} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n请运行以下命令安装缺失的包:")
        print(f"  pip install -r requirements.txt")
        return False
    
    return True


def check_env_file():
    """检查环境变量配置"""
    print("\n检查环境变量配置...")
    
    if not Path(".env").exists():
        print("  ❌ .env文件不存在")
        print("  请复制.env.example为.env并配置API密钥")
        return False
    
    print("  ✓ .env文件存在")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("  ❌ OPENAI_API_KEY未设置")
        print("  请在.env文件中设置你的OpenAI API密钥")
        return False
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key.startswith("sk-") and len(api_key) > 20:
        print(f"  ✓ OPENAI_API_KEY已配置 (sk-...{api_key[-4:]})")
    else:
        print("  ⚠ OPENAI_API_KEY格式可能不正确")
        return False
    
    return True


def check_data_directory():
    """检查数据目录"""
    print("\n检查数据目录...")
    
    data_dir = Path("Volume 399, Issue 10337")
    
    if not data_dir.exists():
        print(f"  ❌ 数据目录不存在: {data_dir}")
        return False
    
    print(f"  ✓ 数据目录存在: {data_dir}")
    
    # 检查是否有子文件夹和文档
    subfolders = [f for f in data_dir.iterdir() if f.is_dir()]
    if not subfolders:
        print("  ❌ 数据目录中没有子文件夹")
        return False
    
    print(f"  ✓ 找到 {len(subfolders)} 个子文件夹")
    
    primary_docs = []
    fallback_docs = []
    for subfolder in subfolders:
        doc_md = subfolder / "doc.md"
        if doc_md.exists():
            primary_docs.append(doc_md)
        else:
            alt_docs = list(subfolder.glob("doc_*.md"))
            fallback_docs.extend(alt_docs)
    
    if not primary_docs and not fallback_docs:
        print("  ❌ 未找到任何doc.md或doc_*.md文件")
        return False
    
    if primary_docs:
        print(f"  ✓ 找到 {len(primary_docs)} 个doc.md文件")
    if fallback_docs:
        print(f"  ⚠ 未提供doc.md的文件夹中共找到 {len(fallback_docs)} 个doc_*.md文件")
    
    return True


def test_basic_import():
    """测试基本导入"""
    print("\n测试基本导入...")
    
    try:
        from rag_demo import MedicalRAGSystem
        print("  ✓ 成功导入MedicalRAGSystem")
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False


def run_simple_test():
    """运行简单测试"""
    print("\n运行简单测试...")
    print("  (这可能需要几分钟，因为需要构建索引)")
    
    try:
        from rag_demo import MedicalRAGSystem
        
        # 创建一个测试实例
        rag = MedicalRAGSystem(
            data_dir="Volume 399, Issue 10337",
            persist_dir="./storage_test"
        )
        
        print("  正在收集文档...")
        doc_files = rag.collect_doc_files()
        print(f"  ✓ 找到 {len(doc_files)} 个文档文件")
        
        # 不运行完整的索引构建，以节省时间和API调用
        print("  ✓ 基本功能测试通过")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("="*80)
    print("RAG系统测试")
    print("="*80)
    
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("环境变量", check_env_file),
        ("数据目录", check_data_directory),
        ("基本导入", test_basic_import),
    ]
    
    results = []
    for name, check_func in checks:
        result = check_func()
        results.append((name, result))
        if not result:
            print(f"\n⚠ {name}检查失败，请修复后继续")
    
    print("\n" + "="*80)
    print("测试摘要")
    print("="*80)
    
    for name, result in results:
        status = "✓" if result else "❌"
        print(f"{status} {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ 所有检查通过！系统已准备就绪。")
        print("\n现在可以运行:")
        print("  python quick_start.py    # 快速开始")
        print("  python rag_demo.py       # 运行主程序")
        print("  python advanced_examples.py  # 高级示例")
        
        # 可选：运行完整测试
        response = input("\n是否运行完整功能测试？(这会消耗API调用) [y/N]: ")
        if response.lower() == 'y':
            run_simple_test()
    else:
        print("\n❌ 部分检查未通过，请按照提示修复问题。")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
