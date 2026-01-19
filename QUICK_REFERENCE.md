# 快速参考指南

## ⚡ 5分钟快速开始

### 步骤1: 安装 (30秒)
```bash
pip install -r requirements.txt
```

### 步骤2: 配置 (30秒)
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env

# 编辑.env文件，填入API密钥
# OPENAI_API_KEY=sk-your-key-here
```

### 步骤3: 运行 (4分钟)
```bash
python quick_start.py
```

就这么简单！

---

## 📝 常用命令

### 测试安装
```bash
python test_setup.py
```

### 快速开始
```bash
python quick_start.py
```

### 运行示例
```bash
python rag_demo.py
python advanced_examples.py
```

### 重建索引
```python
from rag_demo import MedicalRAGSystem
rag = MedicalRAGSystem()
rag.create_index(force_rebuild=True)
```

---

## 🔧 常用代码片段

### 基础查询
```python
from rag_demo import MedicalRAGSystem

rag = MedicalRAGSystem()
rag.create_index()
rag.create_query_engine()
response = rag.query("你的问题")
print(response)
```

### 交互模式
```python
from rag_demo import MedicalRAGSystem

rag = MedicalRAGSystem()
rag.create_index()
rag.create_query_engine()
rag.chat()  # 开始交互
```

### 批量查询
```python
questions = ["问题1", "问题2", "问题3"]
for q in questions:
    rag.query(q)
```

### 自定义配置
```python
rag = MedicalRAGSystem(
    model_name="gpt-4-turbo-preview",
    embedding_model="text-embedding-3-large"
)
```

---

## 🎯 常见查询示例

```python
# 关于临床试验
rag.query("What is the main finding of the PROTECT trial?")

# 关于并发症
rag.query("What are perioperative complications?")

# 关于疾病预防
rag.query("Tell me about HIV prevention methods.")

# 关于COVID-19
rag.query("What COVID-19 topics are discussed?")

# 关于儿童健康
rag.query("Are there studies about children's health?")
```

---

## ⚙️ 参数调整

### 检索更多文档（更全面）
```python
rag.create_query_engine(similarity_top_k=10)
```

### 检索更少文档（更快）
```python
rag.create_query_engine(similarity_top_k=3)
```

### 使用更便宜的模型
```python
rag = MedicalRAGSystem(
    model_name="gpt-3.5-turbo",
    embedding_model="text-embedding-3-small"
)
```

### 使用更强大的模型
```python
rag = MedicalRAGSystem(
    model_name="gpt-4-turbo-preview",
    embedding_model="text-embedding-3-large"
)
```

---

## 🐛 快速故障排除

### 问题：找不到模块
```bash
pip install -r requirements.txt
```

### 问题：API错误
检查`.env`文件中的`OPENAI_API_KEY`是否正确

### 问题：找不到文档
确保`Volume 399, Issue 10337`目录存在且包含子文件夹

### 问题：索引损坏
```python
rag.create_index(force_rebuild=True)
```

---

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `rag_demo.py` | 主程序 - 核心RAG系统 |
| `quick_start.py` | 快速开始脚本 |
| `test_setup.py` | 测试安装配置 |
| `advanced_examples.py` | 高级示例 |
| `config.py` | 配置文件 |
| `requirements.txt` | 依赖列表 |
| `.env` | 环境变量（需自己创建） |
| `.env.example` | 环境变量模板 |
| `README.md` | 完整文档 |
| `PROJECT_SUMMARY.md` | 项目总结 |

---

## 💡 提示与技巧

1. **首次运行会比较慢**：需要构建索引，请耐心等待
2. **索引可重用**：构建一次，永久使用
3. **调整top_k**：更多=更全面，更少=更快
4. **查看来源**：每个回答都会显示参考的文档
5. **批量查询**：可以一次处理多个问题
6. **成本控制**：使用gpt-3.5-turbo可以节省成本

---

## 🔗 有用的链接

- [LlamaIndex文档](https://docs.llamaindex.ai/)
- [OpenAI API文档](https://platform.openai.com/docs)
- [问题反馈](README.md#故障排除)

---

**记住**: 第一次运行 `python quick_start.py` 即可！
