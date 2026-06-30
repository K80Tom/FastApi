# 03 GraphRAG 核心原理

前两节分别讲了普通 RAG 和知识图谱。本节把它们合起来：GraphRAG 为什么要用图增强 RAG？

---

## 本节学习目标

学完本节后，你应该能：

- 解释 GraphRAG 的核心思想。
- 说清图解决了普通 RAG 的什么问题。
- 理解实体、关系、社区、社区摘要在 GraphRAG 中的作用。
- 区分全局检索和局部检索。
- 能用通俗语言讲清 GraphRAG 的价值。

---

## 核心概念解释

### 1. GraphRAG

GraphRAG 是一种增强型 RAG 思路：

```text
先从文档中抽取实体和关系，构建图结构。
再利用图结构帮助检索、组织上下文和生成答案。
```

它不是只看“哪几个 chunk 和问题相似”，还会看：

```text
问题提到了哪些实体？
这些实体连接了哪些其他实体？
它们属于哪些主题社区？
相关社区有什么摘要？
原始文本证据在哪里？
```

### 2. 社区

社区是图里联系比较紧密的一组节点。

通俗理解：

```text
一群经常互相关联的实体，可以看成一个主题团块。
```

例如企业文档中可能形成这些社区：

```text
财务报销社区
人事入职社区
合同审批社区
技术架构社区
```

### 3. 社区发现

社区发现就是自动找出图里的这些主题团块。

它回答的问题是：

```text
图里哪些实体经常连在一起？
这些实体是不是共同构成了某个主题？
```

### 4. 社区摘要

社区摘要是对一个社区的总结。

例如：

```text
“这个社区主要围绕合同审批流程，包含法务部、采购部、供应商、合同模板、审批节点和风险条款。”
```

社区摘要很重要，因为它让 GraphRAG 能回答全局问题。

### 5. 全局检索

全局检索适合回答：

```text
“这批文档的主要主题是什么？”
“公司合同管理有哪些风险？”
“整个系统架构有哪些关键模块？”
```

这类问题不是找某一个 chunk 就够了，而是需要跨文档总结。

### 6. 局部检索

局部检索适合回答：

```text
“项目 A 涉及哪些合同？”
“张三负责哪些任务？”
“UserService 和哪些模块有关？”
```

这类问题通常从一个或几个实体出发，沿着图找邻居和原文证据。

---

## 通俗理解

普通 RAG 像：

```text
拿着问题去找几段相似文本。
```

GraphRAG 像：

```text
先给整批文档画一张知识地图。
提问时，不只找相似段落，还会看地图上相关的人、事、物、关系和主题区域。
```

为什么需要图？

因为很多问题的答案不是藏在单个段落里，而是分散在多个地方：

```text
一个段落提到张三。
另一个段落提到项目 A。
第三个段落提到项目 A 关联合同 B。
第四个段落提到合同 B 有违约风险。
```

普通 RAG 可能只召回其中一两段。  
GraphRAG 可以通过关系串起来：

```text
张三 -> 项目 A -> 合同 B -> 违约风险
```

---

## 技术流程图

GraphRAG 总体流程：

```text
离线索引阶段：
文档
-> chunk
-> 实体抽取
-> 关系抽取
-> 构建图
-> 社区发现
-> 社区摘要
-> 保存图数据、摘要、原文证据、向量

在线查询阶段：
用户问题
-> 判断适合全局还是局部
-> 全局：检索社区摘要
-> 局部：识别实体并扩展邻居关系
-> 可选：结合向量检索原文 chunk
-> 组装上下文
-> LLM 生成答案
```

---

## 关键代码/伪代码示例

```python
def build_graphrag_index(documents: list[str]) -> None:
    chunks = split_documents(documents)

    all_entities = []
    all_relations = []

    for chunk in chunks:
        extraction = llm_extract_entities_and_relations(chunk)
        all_entities.extend(extraction.entities)
        all_relations.extend(extraction.relations)

    graph = build_graph(all_entities, all_relations)
    communities = detect_communities(graph)

    for community in communities:
        report = summarize_community(community)
        save_community_report(report)

    save_graph(graph)
    save_chunks(chunks)
```

查询时：

```python
def ask_graphrag(question: str) -> str:
    if is_global_question(question):
        context = search_community_reports(question)
    else:
        seed_entities = find_entities_in_question(question)
        subgraph = expand_neighbors(seed_entities)
        chunks = find_source_chunks(subgraph)
        context = build_context(subgraph, chunks)

    return llm_answer(question, context)
```

---

## 实际项目中怎么用

### 企业知识库

普通 RAG 能回答：

```text
“报销发票要求是什么？”
```

GraphRAG 更适合回答：

```text
“公司报销制度里涉及哪些部门、流程和风险点？”
```

### 合同审查

普通 RAG 能回答：

```text
“付款期限是多少？”
```

GraphRAG 更适合回答：

```text
“这批合同里哪些供应商、条款和违约风险有关联？”
```

### 代码知识库

普通 RAG 能回答：

```text
“这个函数做什么？”
```

GraphRAG 更适合回答：

```text
“登录功能涉及哪些模块、函数和数据库表？”
```

### Agent 记忆系统

GraphRAG 可以把 Agent 运行历史整理成：

```text
用户 -> 目标 -> 任务 -> 工具调用 -> 结果 -> 决策依据
```

这样 Agent 后续可以按关系找回记忆，而不只是靠语义相似。

---

## 容易混淆的点

### 1. GraphRAG 不只是“加一个图数据库”

图数据库只是存储方式。  
GraphRAG 的核心是：

```text
用图结构参与索引、检索和上下文组织。
```

### 2. GraphRAG 不一定比普通 RAG 永远更好

如果你的问题很简单：

```text
“某条制度写了什么？”
```

普通 RAG 可能更便宜、更快。

GraphRAG 更适合复杂关系和全局总结。

### 3. 社区不是人工分类

社区通常是根据图结构自动发现的主题团块。  
它和你手工给文档打标签不是一回事。

### 4. 全局检索不是搜索全库所有 chunk

全局检索更多依赖社区摘要、全局主题报告等高层信息。  
它不是简单把所有 chunk 都塞给模型。

---

## 学完后我应该能回答的问题

1. GraphRAG 的核心思想是什么？
2. GraphRAG 为什么需要图？
3. 图解决了普通 RAG 的什么问题？
4. 什么是社区？
5. 什么是社区发现？
6. 什么是社区摘要？
7. 什么是全局检索？
8. 什么是局部检索？
9. 哪些场景适合 GraphRAG？
10. GraphRAG 为什么不一定适合所有问答？

下一篇：[04_GraphRAG数据处理流程.md](04_GraphRAG数据处理流程.md)

