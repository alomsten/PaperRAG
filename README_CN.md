# RAG医学文献检索系统 - 中文简明指南

## 🌟 这是什么？

这是一个基于LlamaIndex构建的智能文献检索系统，可以帮你快速查询和理解"Volume 399, Issue 10337"中的医学文献。

### 核心特点
## 🚀 快速开始（3步）

### 第1步：安装依赖
```bash
pip install -r requirements.txt
```

或者使用自动安装脚本：
```bash
# Windows用户
install.bat

# Mac/Linux用户
chmod +x install.sh
./install.sh

```

### 第2步：配置API密钥
1. 复制`.env.example`为`.env`
2. 编辑`.env`文件，填入你的OpenAI API密钥：
   ```
   OPENAI_API_KEY=sk-你的密钥
   ```


### 第3步：运行
```bash
python quick_start.py
```

就这么简单！系统会自动：
1. 构建索引（首次需要3-5分钟）
2. 运行示例查询
3. 启动交互式问答

## 💬 如何使用

### 在代码中使用
```python
from rag_demo import MedicalRAGSystem

# 创建系统
rag = MedicalRAGSystem()

# 构建索引
rag.create_index()

# 创建查询引擎
rag.create_query_engine()

# 提问
response = rag.query("PROTECT试验的主要发现是什么？")
print(response)
```

### 交互式使用
```python
from rag_demo import MedicalRAGSystem

rag = MedicalRAGSystem()
rag.create_index()
rag.create_query_engine()

# 启动聊天模式
rag.chat()
```

然后就可以连续提问了！

## 📝 示例查询

```python
# 查询临床试验
rag.query("PROTECT试验关于术中加温的主要结论是什么？")

# 查询并发症
rag.query("围手术期有哪些心血管并发症？")

# 查询预防方法
rag.query("这些论文讨论了哪些HIV预防方法？")

# 查询特定主题
rag.query("有关于儿童健康的研究吗？")
```

## ⚙️ 常用配置

### 使用更便宜的模型
```python
rag = MedicalRAGSystem(
    model_name="gpt-3.5-turbo",  # 便宜
    embedding_model="text-embedding-3-small"
)
```

### 使用更强大的模型
```python
rag = MedicalRAGSystem(
    model_name="gpt-4-turbo-preview",  # 更准确
    embedding_model="text-embedding-3-large"
)
```

### 调整检索数量
```python
# 检索更多文档（更全面但更慢）
rag.create_query_engine(similarity_top_k=10)

# 检索更少文档（更快但可能不够全面）
rag.create_query_engine(similarity_top_k=3)
```

### 重建索引
```python
# 当文档有更新时
rag.create_index(force_rebuild=True)
```

## 🔧 故障排除

### 找不到模块
```bash
pip install -r requirements.txt
```

### API错误
检查`.env`文件中的`OPENAI_API_KEY`是否正确

### 找不到文档
确保`Volume 399, Issue 10337`目录存在

### 测试安装
```bash
python test_setup.py
```

## 📂 重要文件

| 文件 | 说明 |
|------|------|
| `rag_demo.py` | 主程序 |
| `quick_start.py` | 快速开始脚本 |
| `test_setup.py` | 安装测试 |
| `config.py` | 配置文件 |
| `requirements.txt` | 依赖列表 |

## 📚 完整文档

- [INDEX.md](INDEX.md) - 文档导航
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速参考
- [README.md](README.md) - 完整英文文档
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总结
- [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md) - 运行示例

## 💡 工作原理

1. **文档加载**: 优先使用每个子文件夹中的`doc.md`汇总文件（缺失时回退读取`doc_*.md`分片）
2. **智能分块**: 根据Markdown标题切分文档
3. **向量化**: 将文本转换为AI可理解的向量
4. **索引构建**: 创建高效的检索索引
5. **语义检索**: 理解问题，找到最相关内容
6. **生成回答**: 基于检索内容，生成准确答案

## ⚠️ 注意事项

1. **费用**: 使用OpenAI API会产生费用
   - 首次构建: ~$0.5-1
   - 每次查询: ~$0.05-0.1 (GPT-4) 或 ~$0.01 (GPT-3.5)

2. **时间**: 首次构建索引需要3-5分钟

3. **存储**: 索引文件约50-100MB

4. **网络**: 需要稳定的网络连接

## 🎯 性能数据

- **索引构建**: 3-5分钟（仅首次）
- **索引加载**: 1-2秒（后续使用）
- **单次查询**: 2-5秒
- **支持文档**: 100+篇

## 🆘 获取帮助

遇到问题？
1. 运行 `python test_setup.py` 诊断
2. 查看 [README.md](README.md) 故障排除部分
3. 阅读 [LlamaIndex文档](https://docs.llamaindex.ai/)

---

**现在就开始**: `python quick_start.py` 👈

**祝使用愉快！** 🎉
