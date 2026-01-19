# RAG医学文献检索系统

基于LlamaIndex构建的科技文献检索系统，专门用于检索和问答Volume 399, Issue 10337中的医学文献。

## 🌟 功能特点

- ✅ **智能文档收集**：优先使用各子文件夹中的`doc.md`汇总文件（缺失时回退到`doc_*.md`）
- ✅ **精细化分块**：先按Markdown标题、再按段落拆分，自动保持表格完整并标注来源元信息
- ✅ **结构化分块**：基于Markdown标题进行智能分块，保持文档结构性
- ✅ **向量检索**：使用OpenAI嵌入模型构建高质量向量索引
- ✅ **索引持久化**：支持索引保存，避免重复构建节省时间和成本
- ✅ **多种交互模式**：提供交互式查询和批量查询两种模式
- ✅ **来源追踪**：显示查询来源和相似度得分，确保答案可信
- ✅ **易于配置**：支持自定义模型、检索参数等

## 📋 安装步骤

### 1️⃣ 克隆或下载项目

确保你的工作目录包含所有必要文件。

### 2️⃣ 安装Python依赖

```bash
pip install -r requirements.txt
```

推荐使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活虚拟环境（Linux/Mac）
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3️⃣ 配置API密钥

创建`.env`文件并添加你的OpenAI API密钥：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑`.env`文件，填入你的API密钥：

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

如需使用国内中转或自建的兼容接口，可一并设置：

```env
OPENAI_BASE_URL=https://hk.n1n.ai/v1  # 示例：自定义Base URL
LLM_MODEL_ID=gemini-3-flash-preview   # 覆盖默认LLM模型
LLM_TIMEOUT=60                        # 可选：请求超时时间（秒）
```

如果已有其他软件使用`LLM_API_KEY`等变量，可以继续沿用，系统会自动识别：

```env
LLM_API_KEY=sk-your-actual-api-key-here
LLM_BASE_URL=https://hk.n1n.ai/v1
```

### 4️⃣ 验证安装

运行测试脚本验证一切正常：

```bash
python test_setup.py
```

## 🚀 快速开始

### 方法1：使用快速开始脚本

```bash
python quick_start.py
```

这个脚本会：
1. 自动构建或加载索引
2. 运行几个示例查询
3. 启动交互式聊天模式

### 方法2：在代码中使用

```python
from rag_demo import MedicalRAGSystem

# 创建RAG系统
rag_system = MedicalRAGSystem(
    data_dir="Volume 399, Issue 10337",
    persist_dir="./storage"
)

# 构建索引（首次运行）
rag_system.create_index()

# 创建查询引擎
rag_system.create_query_engine(similarity_top_k=5)

# 进行查询
response = rag_system.query("What is the PROTECT trial about?")
print(response)
```

### 方法3：交互式聊天模式

```python
from rag_demo import MedicalRAGSystem

rag_system = MedicalRAGSystem()
rag_system.create_index()
rag_system.create_query_engine()

# 启动交互式聊天
rag_system.chat()
```

## ⚙️ 高级配置

### 自定义LLM模型

```python
rag_system = MedicalRAGSystem(
    data_dir="Volume 399, Issue 10337",
    persist_dir="./storage",
    model_name="gpt-4-turbo-preview",  # 使用GPT-4 Turbo
    embedding_model="text-embedding-3-large"  # 使用更强大的嵌入模型
)
```

可用的模型选项：
- **LLM模型**: `gpt-4`, `gpt-4-turbo-preview`, `gpt-3.5-turbo`
- **嵌入模型**: `text-embedding-3-small`, `text-embedding-3-large`, `text-embedding-ada-002`

### 重建索引

如果文档有更新，需要重建索引：

```python
rag_system.create_index(force_rebuild=True)
```

### 控制段落分块大小

科学文献往往段落较长，默认会将每个标题下的段落按约1200字符拆分，同时保留完整表格并打上元信息。如果需要更长或更短的块，可以通过参数或环境变量调整：

```python
rag_system = MedicalRAGSystem(
    paragraph_chunk_chars=1500  # 自定义段落最大字符数
)
```

或在 `.env` 中设置：

```env
PARAGRAPH_CHUNK_CHARS=1500
```

### 调整检索参数

```python
# 返回更多相关文档片段（默认是5个）
rag_system.create_query_engine(similarity_top_k=10)

# 较少的文档片段（更快，但可能不够全面）
rag_system.create_query_engine(similarity_top_k=3)
```

### 使用配置文件

编辑`config.py`来集中管理配置：

```python
from config import RAG_CONFIG

rag_system = MedicalRAGSystem(**RAG_CONFIG)
```

## 📂 项目结构

```
RAGdemo/
├── rag_demo.py              # 主程序（RAG系统核心）
├── quick_start.py           # 快速开始脚本
├── advanced_examples.py     # 高级使用示例
├── test_setup.py           # 安装测试脚本
├── config.py               # 配置文件
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量示例
├── .env                   # 环境变量配置（需自己创建）
├── .gitignore             # Git忽略文件
├── README.md              # 本文件
├── storage/               # 索引存储目录（自动创建）
└── Volume 399, Issue 10337/  # 文档目录
    ├── 文献1/
    │   ├── doc_0.md
    │   ├── doc_1.md
    │   └── ...
    ├── 文献2/
    │   ├── doc_0.md
    │   └── ...
    └── ...
```

## 🔍 工作原理

### 1. 📥 文档加载
系统遍历`Volume 399, Issue 10337`目录下的所有子文件夹，优先收集`doc.md`汇总文件；若缺失则回退读取该文件夹中的`doc_*.md`分片。

### 2. ✂️ 智能分块
使用`MarkdownNodeParser`基于markdown标题（#, ##, ###等）自动分块，保持内容的语义完整性。这对于结构化的科技文献特别有效，因为：
- 保留文档的层次结构
- 每个分块有明确的主题（由标题定义）
- 避免在句子中间切断

### 3. 🔢 向量化
使用OpenAI的嵌入模型（text-embedding-3-small或large）将文档块转换为高维向量表示。

### 4. 💾 索引构建
创建向量索引（VectorStoreIndex）并持久化到磁盘，后续运行可直接加载，无需重复构建。

### 5. 🎯 检索与生成
- 用户查询被转换为向量
- 系统找出最相关的K个文档块（基于余弦相似度）
- 将相关文档块和用户问题一起发送给LLM
- LLM基于检索到的上下文生成准确回答

## 💡 使用示例

### 查询临床试验

```python
rag_system.query("What is the main finding of the PROTECT trial about intraoperative warming?")
```

**示例输出:**
```
问题: What is the main finding of the PROTECT trial about intraoperative warming?
--------------------------------------------------------------------------------
回答: The PROTECT trial found that aggressive intraoperative warming to 37°C 
did not significantly reduce major perioperative complications compared to 
routine thermal management targeting 35°C. The 30-day composite outcome of 
myocardial injury, cardiac arrest, and mortality was similar between groups 
(9.9% vs 9.6%, p=0.69).
--------------------------------------------------------------------------------

参考了 5 个文档片段:
  1. doc_0.md (相似度: 0.8756)
  2. doc_1.md (相似度: 0.8234)
  ...
```

### 更多示例查询

```python
# 关于手术并发症
rag_system.query("What are the cardiovascular complications in perioperative period?")

# 关于疾病预防
rag_system.query("Tell me about HIV prevention methods discussed in these papers.")

# 关于COVID-19
rag_system.query("What COVID-19 topics are covered in Volume 399 Issue 10337?")

# 关于儿童健康
rag_system.query("Are there studies about children's health and development?")
```

### 批量查询示例

```python
questions = [
    "What is myocardial injury after non-cardiac surgery (MINS)?",
    "What are the findings about cabotegravir for HIV prevention?",
    "What topics about global health are discussed?",
]

for question in questions:
    response = rag_system.query(question)
    print(f"\nQ: {question}")
    print(f"A: {response}\n")
```

## ⚠️ 注意事项

1. **💰 API费用**：使用OpenAI API会产生费用
   - 首次构建索引会调用嵌入API（按token计费）
   - 每次查询会调用LLM API
   - 建议先用少量数据测试
   - 索引持久化后可重复使用，无需重复构建

2. **⏱️ 首次构建时间**：首次构建索引可能需要几分钟
   - 取决于文档数量（当前约100+个文档）
   - 取决于网络速度
   - 进度会实时显示

3. **🔑 环境变量**：确保`.env`文件配置正确
   - API密钥必须有效
   - 需要有足够的API额度

4. **🐍 Python版本**：建议使用Python 3.9或更高版本

5. **💾 存储空间**：索引文件会占用一定磁盘空间（通常几十MB）

## 🔧 故障排除

### ❌ 问题1：找不到文档

**错误信息:** `未找到任何doc.md或doc_*.md文件`

**解决方法:**
- 确保`Volume 399, Issue 10337`目录存在
- 确保目录结构正确（包含子文件夹和markdown文件）
- 运行`python test_setup.py`检查配置

### ❌ 问题2：API错误

**错误信息:** `AuthenticationError` 或 `API key not found`

**解决方法:**
1. 检查`.env`文件是否存在
2. 检查`OPENAI_API_KEY`是否正确配置
3. 确认API密钥格式正确（以`sk-`开头）
4. 检查API额度是否充足

### ❌ 问题3：导入错误

**错误信息:** `ModuleNotFoundError: No module named 'llama_index'`

**解决方法:**
```bash
pip install -r requirements.txt
```

### ❌ 问题4：内存不足

**解决方法:**
- 减少`similarity_top_k`参数
- 分批处理文档
- 使用更大的机器或云服务器

### ❌ 问题5：索引加载失败

**解决方法:**
```python
# 强制重建索引
rag_system.create_index(force_rebuild=True)
```

## 📚 相关资源

- [LlamaIndex文档](https://docs.llamaindex.ai/)
- [OpenAI API文档](https://platform.openai.com/docs)
- [Markdown语法指南](https://www.markdownguide.org/)

## 📝 更新日志

### v1.0.0 (2026-01-09)
- ✨ 初始版本
- ✅ 支持基于markdown标题的智能分块
- ✅ 支持索引持久化
- ✅ 提供交互式和批量查询模式
- ✅ 完整的文档和示例

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

MIT License

---

**祝使用愉快！如有问题，请运行`python test_setup.py`进行诊断。**
