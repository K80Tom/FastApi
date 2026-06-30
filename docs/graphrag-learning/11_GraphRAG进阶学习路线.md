# 11 GraphRAG 进阶学习路线

前面 `00-10` 是入门层，目标是让你知道 GraphRAG 是什么、为什么需要图、整体流程怎么走。  
从本节开始进入进阶层，目标是理解 GraphRAG 真正难在哪里，并逐步具备做工程 Demo 的能力。

---

## 本节学习目标

学完本节后，你应该能：

- 知道 GraphRAG 为什么“概念简单，落地复杂”。
- 区分入门版 GraphRAG 和工程版 GraphRAG。
- 知道进阶学习应该深入哪些模块。
- 明确每个进阶模块的产出物。
- 为后续实体消歧、社区发现、检索编排、评估调优做准备。

---

## 核心概念解释

### 1. 入门版 GraphRAG

入门版通常只需要理解：

```text
文档 -> chunk -> 实体关系抽取 -> 图 -> 检索 -> LLM 回答
```

这个层级适合讲概念。

### 2. 工程版 GraphRAG

工程版会遇到更多问题：

```text
实体重复怎么办？
关系抽错怎么办？
社区划分不合理怎么办？
全局检索和局部检索怎么选择？
上下文太长怎么裁剪？
答案怎么评估？
图数据库、向量数据库、关系型数据库怎么配合？
```

这些问题才是 GraphRAG 真正有挑战的地方。

### 3. 进阶学习的核心模块

进阶层建议拆成 6 个模块：

```text
1. 进阶架构总览
2. 实体消歧与关系去重
3. 社区发现与社区摘要
4. 检索策略与上下文编排
5. GraphRAG 评估与调优
6. FastAPI 工程化落地
```

---

## 通俗理解

GraphRAG 入门像是：

```text
我知道要把文档变成一张知识图。
```

GraphRAG 进阶像是：

```text
这张图怎么画才不乱？
画错了怎么修？
用户问问题时，我到底该查哪部分图？
查出来的东西怎么裁剪给模型？
模型答得对不对怎么判断？
```

也就是说，进阶层不是背更多术语，而是开始处理真实工程里的“脏问题”。

---

## 技术流程图

进阶 GraphRAG 全流程：

```text
数据接入
-> 文档解析
-> chunk 切分
-> 实体关系抽取
-> 实体标准化
-> 实体消歧
-> 关系去重和置信度打分
-> 图构建
-> 社区发现
-> 社区摘要生成
-> chunk / entity / report 向量化
-> 查询意图识别
-> 多路召回
-> 图扩展
-> 重排
-> 上下文预算控制
-> LLM 回答
-> 引用来源
-> 效果评估
-> 反馈迭代
```

你会发现，这已经不是一个简单函数，而是一套系统。

---

## 关键代码/伪代码示例

```python
def build_advanced_graphrag_index(documents):
    chunks = parse_and_split(documents)

    raw_entities, raw_relations = extract_graph_items(chunks)

    canonical_entities = resolve_entities(raw_entities)
    cleaned_relations = deduplicate_relations(
        raw_relations,
        canonical_entities,
    )

    graph = build_graph(canonical_entities, cleaned_relations)
    communities = detect_communities(graph)
    reports = summarize_communities(communities)

    embed_chunks(chunks)
    embed_entities(canonical_entities)
    embed_reports(reports)

    return GraphRAGIndex(
        chunks=chunks,
        graph=graph,
        reports=reports,
    )
```

查询阶段：

```python
def advanced_query(question):
    intent = classify_query_intent(question)

    candidates = retrieve_from_multiple_routes(
        question=question,
        intent=intent,
    )

    ranked_context = rerank_and_budget_context(candidates)
    answer = generate_answer(question, ranked_context)

    return attach_sources(answer, ranked_context)
```

---

## 实际项目中怎么用

如果你要把现在的学习路线升级成项目，建议这样分阶段：

### 第 1 版：能跑通

```text
上传文档
切块
抽实体关系
保存实体和关系
支持 /ask/hybrid
```

### 第 2 版：图质量提升

```text
实体合并
关系去重
置信度字段
错误抽取样本回看
```

### 第 3 版：检索质量提升

```text
local / global / hybrid 三种模式
query intent 判断
上下文去重和截断
引用来源
```

### 第 4 版：可评估

```text
准备测试问题集
对比普通 RAG 和 GraphRAG
记录召回内容、答案、引用、评分
```

### 第 5 版：工程化

```text
FastAPI 分层
后台任务
数据库迁移
日志
错误处理
README 演示步骤
```

---

## 容易混淆的点

### 1. 进阶不是一开始就上复杂框架

你应该先知道复杂点在哪里，再选择工具。  
不要一上来就堆 Neo4j、Celery、Redis、OpenTelemetry。

### 2. 图越大不一定越好

图太大、噪声太多，检索反而会变差。

### 3. 抽取越多不一定越好

GraphRAG 不是把所有名词都变成实体。  
实体和关系要服务问题。

### 4. 评估不能只看答案顺不顺

答案流畅不代表正确。  
要看引用来源、关系链路和事实一致性。

### 5. GraphRAG 不只是算法问题

它是数据处理、检索、生成、存储和工程化共同组成的系统。

---

## 学完后我应该能回答的问题

1. 为什么 GraphRAG 概念简单但工程复杂？
2. 入门版 GraphRAG 和工程版 GraphRAG 有什么区别？
3. 进阶学习应该深入哪些模块？
4. 为什么实体消歧很重要？
5. 为什么关系需要去重和置信度？
6. 为什么社区摘要会影响全局检索？
7. 为什么上下文编排很关键？
8. GraphRAG 应该怎么评估？
9. 一个 GraphRAG 项目可以分几个版本迭代？
10. 为什么不要一开始把系统做得太大？

下一篇：[12_实体消歧与关系去重.md](12_实体消歧与关系去重.md)

