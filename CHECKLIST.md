# ✅ 安装检查清单

使用这个清单确保系统正确安装和配置。

## 📋 安装前检查

- [ ] Python版本 ≥ 3.9
  ```bash
  python --version
  ```

- [ ] 有OpenAI API密钥
  - 访问 https://platform.openai.com/api-keys
  - 确保账户有足够余额

- [ ] `Volume 399, Issue 10337`目录存在
  - 包含多个子文件夹
  - 每个子文件夹提供`doc.md`汇总文件（若无则至少有`doc_*.md`分片）

## 📦 安装步骤检查

- [ ] 下载/克隆了所有项目文件
  - `rag_demo.py`
  - `requirements.txt`
  - `.env.example`
  - 其他脚本和文档

- [ ] 安装了Python依赖
  ```bash
  pip install -r requirements.txt
  ```

- [ ] 创建了`.env`文件
  ```bash
  # Windows
  copy .env.example .env
  
  # Linux/Mac
  cp .env.example .env
  ```

- [ ] 在`.env`中配置了API密钥
  - 打开`.env`文件
  - 将`your_api_key_here`替换为实际密钥
  - 格式: `OPENAI_API_KEY=sk-...`

## ✅ 验证安装

- [ ] 运行测试脚本
  ```bash
  python test_setup.py
  ```

- [ ] 所有测试项显示 ✓
  - ✓ Python版本
  - ✓ 依赖包
  - ✓ 环境变量
  - ✓ 数据目录
  - ✓ 基本导入

## 🚀 首次运行检查

- [ ] 运行快速开始脚本
  ```bash
  python quick_start.py
  ```

- [ ] 索引成功构建
  - 显示"找到 X 个文档文件"
  - 显示"文档被分为 X 个语义块"
  - 显示"索引创建并保存成功"

- [ ] 示例查询成功运行
  - 显示问题和回答
  - 显示参考文档
  - 显示相似度得分

- [ ] 交互模式可以使用
  - 可以输入问题
  - 得到合理的回答
  - 可以正常退出

## 🔍 功能测试检查

- [ ] 基础查询正常
  ```python
  from rag_demo import MedicalRAGSystem
  rag = MedicalRAGSystem()
  rag.create_index()
  rag.create_query_engine()
  response = rag.query("测试问题")
  ```

- [ ] 索引持久化正常
  - 第一次运行后，`storage`目录被创建
  - 第二次运行时，索引快速加载（1-2秒）
  - 不需要重新构建

- [ ] 交互模式正常
  ```python
  rag.chat()  # 可以连续提问
  ```

- [ ] 批量查询正常
  ```python
  for q in questions:
      rag.query(q)
  ```

## ⚙️ 配置检查

- [ ] 可以修改模型
  ```python
  rag = MedicalRAGSystem(
      model_name="gpt-3.5-turbo"
  )
  ```

- [ ] 可以调整检索参数
  ```python
  rag.create_query_engine(similarity_top_k=10)
  ```

- [ ] 可以重建索引
  ```python
  rag.create_index(force_rebuild=True)
  ```

## 📊 性能检查

- [ ] 首次构建索引时间合理（3-5分钟）

- [ ] 后续加载索引快速（1-2秒）

- [ ] 单次查询响应快速（2-5秒）

- [ ] 内存使用正常（不超过2GB）

## 💰 成本检查

- [ ] 理解API计费方式
  - 嵌入API：按token计费
  - LLM API：按token计费

- [ ] 首次构建成本可接受（~$0.5-1）

- [ ] 单次查询成本可接受（~$0.05-0.1）

- [ ] 考虑使用更便宜的模型（gpt-3.5-turbo）

## 📁 文件系统检查

- [ ] 项目目录结构正确
  ```
  RAGdemo/
  ├── rag_demo.py
  ├── quick_start.py
  ├── requirements.txt
  ├── .env
  ├── storage/          # 自动创建
  └── Volume 399, Issue 10337/
  ```

- [ ] `.env`文件未被Git追踪
  - `.gitignore`中包含`.env`

- [ ] `storage`目录包含索引文件
  - `docstore.json`
  - `index_store.json`
  - `vector_store.json`
  - 等

## 🔒 安全检查

- [ ] API密钥安全存储
  - 在`.env`文件中
  - 不在代码中硬编码
  - 不提交到Git

- [ ] `.gitignore`配置正确
  - 忽略`.env`
  - 忽略`storage/`
  - 忽略`__pycache__/`

## 📚 文档检查

- [ ] 阅读了快速参考
  - [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

- [ ] 了解了基本用法
  - [README.md](README.md)

- [ ] 查看了示例输出
  - [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)

## 🎓 学习检查

- [ ] 理解了RAG工作原理
  - 文档加载
  - 向量化
  - 检索
  - 生成

- [ ] 知道如何自定义配置
  - 修改模型
  - 调整参数
  - 重建索引

- [ ] 知道如何排查问题
  - 运行`test_setup.py`
  - 查看文档
  - 检查日志

## ✨ 准备就绪！

如果以上所有项都已完成：

✅ **恭喜！系统已完全配置好，可以开始使用了！**

### 下一步：

1. **日常使用**: `python quick_start.py`

2. **探索功能**: `python advanced_examples.py`

3. **集成到项目**: 在你的代码中导入使用
   ```python
   from rag_demo import MedicalRAGSystem
   ```

4. **自定义扩展**: 根据需求修改配置和功能

---

## 🆘 如果有任何项未通过

1. 重新阅读相关文档
2. 运行 `python test_setup.py` 诊断
3. 查看 [README.md#故障排除](README.md#-故障排除)
4. 检查 [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

**记得保存这个检查清单，每次设置新环境时都可以使用！**
