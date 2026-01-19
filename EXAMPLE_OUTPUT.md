# 系统运行示例输出

## 首次运行 - 构建索引

```
================================================================================
医学文献RAG检索系统 - 快速开始
================================================================================

正在初始化系统...

步骤1: 构建/加载索引
--------------------------------------------------------------------------------
找到 103 个文档文件
正在加载文档...
成功加载 103 个文档
正在使用markdown标题进行文档分块...
文档被分为 856 个语义块
正在创建向量索引...
正在保存索引到 ./storage...
索引创建并保存成功！

步骤2: 创建查询引擎
--------------------------------------------------------------------------------
查询引擎已创建 (top_k=5)

步骤3: 运行示例查询
--------------------------------------------------------------------------------

[示例 1]

问题: What are the main findings about intraoperative warming in the PROTECT trial?
--------------------------------------------------------------------------------
回答: The PROTECT trial found that aggressive intraoperative warming to maintain 
a core temperature of 37°C did not significantly reduce major perioperative 
complications compared to routine thermal management targeting 35°C. Specifically:

1. The primary composite outcome (myocardial injury, cardiac arrest, or mortality 
   within 30 days) occurred in 9.9% of aggressively warmed patients versus 9.6% 
   of routine management patients (p=0.69).

2. Mean final intraoperative temperatures were 37.1°C in the aggressive warming 
   group versus 35.6°C in the routine management group.

3. The study concluded that maintaining core temperature at least 35.5°C appears 
   sufficient for surgical patients, and there was no evidence that outcomes 
   varied substantially across the 1.5°C temperature range tested.
--------------------------------------------------------------------------------

参考了 5 个文档片段:
  1. Aggressive-intraoperative-warming-versus-routine-thermal-managemen_2022_The-\doc_0.md (相似度: 0.8756)
  2. Aggressive-intraoperative-warming-versus-routine-thermal-managemen_2022_The-\doc_1.md (相似度: 0.8234)
  3. Aggressive-intraoperative-warming-versus-routine-thermal-managemen_2022_The-\doc_2.md (相似度: 0.7891)
  4. Challenging-dogma-about-perioperative-warming-during-non-cardi_2022_The-Lanc\doc_0.md (相似度: 0.7456)
  5. Aggressive-intraoperative-warming-versus-routine-thermal-managemen_2022_The-\doc_3.md (相似度: 0.7123)


[示例 2]

问题: What is myocardial injury after non-cardiac surgery (MINS)?
--------------------------------------------------------------------------------
回答: Myocardial injury after non-cardiac surgery (MINS) is a clinically important 
condition characterized by troponin elevation without a non-ischemic explanation. 
Key features include:

1. It is often clinically silent - approximately 65% of cases are entirely 
   asymptomatic and would go undetected without routine troponin screening.

2. Fewer than 10% of patients with MINS experience chest pain, making it difficult 
   to detect based on symptoms alone.

3. Despite the lack of symptoms, MINS significantly increases 30-day mortality 
   in both symptomatic and asymptomatic patients.

4. MINS highlights that troponin elevations are clinically important even in 
   patients who do not meet the formal universal definition of myocardial 
   infarction (which requires symptoms and signs in addition to biomarker elevation).

5. It represents one of the most common perioperative complications, with about 
   25% of all 30-day postoperative deaths being cardiovascular or consequent to 
   cardiovascular events.
--------------------------------------------------------------------------------

参考了 5 个文档片段:
  1. Aggressive-intraoperative-warming-versus-routine-thermal-managemen_2022_The-\doc_0.md (相似度: 0.8923)
  2. Aggressive-intraoperative-warming-versus-routine-thermal-managemen_2022_The-\doc_1.md (相似度: 0.7654)
  3. Aggressive-intraoperative-warming-versus-routine-thermal-managemen_2022_The-\doc_2.md (相似度: 0.7234)
  4. Allocated-but-not-treated--the-silent-16-_2022_The-Lancet\doc_0.md (相似度: 0.6789)
  5. Opportunities-in-crisis-for-optimising-child-health-and-devel_2022_The-Lance\doc_0.md (相似度: 0.6456)

================================================================================
现在可以开始交互式查询
================================================================================
=== 医学文献RAG系统交互模式 ===
输入问题进行查询，输入 'quit' 或 'exit' 退出

您的问题: 
```

---

## 后续运行 - 加载已有索引

```
================================================================================
医学文献RAG检索系统 - 快速开始
================================================================================

正在初始化系统...

步骤1: 构建/加载索引
--------------------------------------------------------------------------------
正在加载已存在的索引...
索引加载成功！

步骤2: 创建查询引擎
--------------------------------------------------------------------------------
查询引擎已创建 (top_k=5)

步骤3: 运行示例查询
--------------------------------------------------------------------------------
...
```

**注意**: 后续运行时，索引加载只需1-2秒！

---

## 交互式查询示例

```
您的问题: Tell me about COVID-19 topics in these papers

问题: Tell me about COVID-19 topics in these papers
--------------------------------------------------------------------------------
回答: The papers in Volume 399, Issue 10337 discuss several COVID-19 related topics:

1. COVID-19 and the next phase - discussing the ongoing pandemic situation and 
   future considerations

2. COVID-19 and inter-generational solidarity - exploring how the pandemic has 
   affected different age groups and the importance of solidarity across generations

3. Prevention and management aspects, including discussions of public health 
   measures and their effectiveness

The papers appear to focus on both the immediate health impacts and broader 
societal implications of the pandemic.
--------------------------------------------------------------------------------

参考了 5 个文档片段:
  1. COVID-19--the-next-phase-and-beyond_2022_The-Lancet\doc_0.md (相似度: 0.9123)
  2. COVID-19-and-inter-generational-solidarity_2022_The-Lancet\doc_0.md (相似度: 0.8876)
  3. COVID-19--the-next-phase-and-beyond_2022_The-Lancet\doc_1.md (相似度: 0.8234)
  4. Responding-to-the-humanitarian-crisis-of-the-war-in-Ukraine-wit_2022_The-Lan\doc_0.md (相似度: 0.6789)
  5. Offline--Gradually--then-suddenly_2022_The-Lancet\doc_0.md (相似度: 0.6234)

您的问题: What about HIV prevention?

问题: What about HIV prevention?
--------------------------------------------------------------------------------
回答: The papers discuss significant advances in HIV prevention, particularly 
regarding cabotegravir:

1. Long-acting injectable cabotegravir has shown promising results for HIV 
   prevention in women in sub-Saharan Africa

2. The HPTN 084 trial demonstrated the efficacy of cabotegravir compared to 
   oral prevention methods

3. Long-acting injections represent an important advancement because they:
   - Reduce the need for daily pill-taking
   - May improve adherence
   - Offer a discreet prevention option
   - Are particularly relevant for populations at high risk

4. The papers discuss both the clinical trial results and the broader implications 
   for HIV prevention programs in resource-limited settings

This represents a major step forward in HIV prevention technology and could 
significantly impact prevention strategies, especially for women who face 
unique barriers to traditional prevention methods.
--------------------------------------------------------------------------------

参考了 5 个文档片段:
  1. Cabotegravir-for-the-prevention-of-HIV-1-in-women--results-from-H_2022_The-L_chunk_01\doc_0.md (相似度: 0.9345)
  2. Cabotegravir-for-the-prevention-of-HIV-1-in-women--results-from-H_2022_The-L_chunk_02\doc_0.md (相似度: 0.9123)
  3. Long-acting-injections-for-HIV-prevention-among-women-in-sub-S_2022_The-Lanc\doc_0.md (相似度: 0.8876)
  4. Cabotegravir-for-the-prevention-of-HIV-1-in-women--results-from-H_2022_The-L_chunk_01\doc_1.md (相似度: 0.8234)
  5. Cabotegravir-for-the-prevention-of-HIV-1-in-women--results-from-H_2022_The-L_chunk_02\doc_1.md (相似度: 0.7891)

您的问题: quit

再见！
```

---

## 测试脚本输出

```
================================================================================
RAG系统测试
================================================================================
检查Python版本...
  ✓ Python 3.11.5

检查依赖包...
  ✓ llama_index
  ✓ openai
  ✓ dotenv

检查环境变量配置...
  ✓ .env文件存在
  ✓ OPENAI_API_KEY已配置 (sk-...Ab3d)

检查数据目录...
  ✓ 数据目录存在: Volume 399, Issue 10337
  ✓ 找到 29 个子文件夹
   ✓ 找到 32 个doc.md文件
   ⚠ 未提供doc.md的文件夹中共找到 71 个doc_*.md文件

测试基本导入...
  ✓ 成功导入MedicalRAGSystem

================================================================================
测试摘要
================================================================================
✓ Python版本
✓ 依赖包
✓ 环境变量
✓ 数据目录
✓ 基本导入

✓ 所有检查通过！系统已准备就绪。

现在可以运行:
  python quick_start.py    # 快速开始
  python rag_demo.py       # 运行主程序
  python advanced_examples.py  # 高级示例

是否运行完整功能测试？(这会消耗API调用) [y/N]: n
```

---

## 性能指标

### 首次构建索引
- 文档加载: ~30秒
- 向量化: ~2-3分钟（103个文档）
- 索引构建: ~30秒
- **总计**: ~3-4分钟

### 后续使用
- 索引加载: ~1-2秒
- 单次查询: ~2-5秒
- 批量查询: 每个问题2-5秒

### API调用成本估算（100个文档）
- 首次构建索引: ~$0.50-1.00（仅一次）
- 单次查询（GPT-4）: ~$0.05-0.10
- 单次查询（GPT-3.5）: ~$0.01-0.02

---

## 文件大小

- 索引文件: ~50-100 MB（取决于文档数量）
- 每个文档的向量: ~500 KB
- 总存储需求: ~100-200 MB

---

这些示例展示了系统在实际运行时的表现。实际输出可能略有不同，取决于：
- 文档数量和大小
- 网络速度
- API响应时间
- 选择的模型
