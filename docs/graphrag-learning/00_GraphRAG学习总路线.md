# 00 GraphRAG 学习总路线

本文件是整套 GraphRAG 学习文档的总览。你可以把它当成地图：先知道 GraphRAG 是什么，再按阶段拆开学。

---

## 本节学习目标

学完本节后，你应该能回答：

- GraphRAG 是什么。
- GraphRAG 和传统 RAG 有什么区别。
- GraphRAG 为什么需要“图”。
- 学 GraphRAG 前需要哪些基础。
- 应该按什么顺序学习。
- 最后可以做什么项目。
- 如果想深入，应该继续学哪些进阶主题。

---

## GraphRAG 是什么

GraphRAG 可以拆成两个部分：

```text
Graph + RAG
```

`RAG` 是 Retrieval-Augmented Generation，意思是：

```text
先从外部知识库检索资料，再把资料交给大模型生成答案。
```

`Graph` 是图结构，意思是：

```text
用“点”和“边”表示知识。
```

例如：

```text
点：张三、项目 A、合同 B、公司 C
边：张三 负责 项目 A
边：项目 A 关联 合同 B
边：合同 B 属于 公司 C
```

所以 GraphRAG 可以通俗理解为：

```text
普通 RAG 是从一堆文本片段里找相似内容。
GraphRAG 是先把文本里的关键对象和关系整理成图，再借助图来检索、总结和回答问题。
```

---

## GraphRAG 和传统 RAG 的区别

传统 RAG 常见流程：

```text
文档 -> 切块 -> 向量化 -> 向量数据库 -> top-k 相似 chunk -> LLM 回答
```

GraphRAG 常见流程：

```text
文档
-> 切块
-> 抽取实体和关系
-> 构建知识图谱
-> 发现社区
-> 生成社区摘要
-> 查询时结合图结构、社区摘要、原文 chunk 和向量检索
-> LLM 回答
```

核心区别：

| 对比项 | 传统 RAG | GraphRAG |
| --- | --- | --- |
| 知识组织方式 | 文本 chunk | 实体、关系、社区、摘要、chunk |
| 检索入口 | 向量相似度 | 实体、关系、社区摘要、向量 |
| 擅长问题 | 具体事实问题 | 跨文档、跨实体、全局总结、关系推理 |
| 主要短板 | 容易只拿到局部片段 | 构建成本更高，流程更复杂 |

---

## GraphRAG 的核心价值

GraphRAG 不是为了替代所有 RAG，而是解决普通 RAG 不擅长的问题。

普通 RAG 容易卡在这些场景：

```text
1. 问题需要跨多个文档综合。
2. 问题里没有明显关键词，向量检索不好命中。
3. 用户问的是全局主题，而不是某个具体事实。
4. 文档里有很多人、公司、系统、模块、合同条款之间的关系。
5. 需要解释“谁影响了谁”“哪些对象有关联”“整体风险在哪里”。
```

GraphRAG 的价值是：

```text
把散落在文本里的对象和关系显式整理出来，让系统不只会找相似文本，还能沿着关系找相关知识。
```

---

## 前置知识

学习 GraphRAG 前，建议先理解这些东西。

### 1. 普通 RAG

你需要知道：

```text
文档切分、embedding、向量数据库、top-k、召回、重排、引用来源
```

不用一开始很精通，但要知道普通 RAG 的基本流程。

### 2. LLM 基础

你需要知道：

```text
prompt 是什么
结构化输出是什么
为什么 LLM 可以抽取实体和关系
为什么 LLM 输出可能不稳定
```

### 3. 知识图谱基础

你需要知道：

```text
实体、关系、属性、三元组、节点、边
```

### 4. 数据库基础

你需要知道：

```text
表、主键、外键、索引
```

后面学图数据库时会更容易理解。

### 5. FastAPI 基础

最终落地项目时，你需要能写：

```text
POST /documents/upload
POST /index
POST /ask
GET /graph/entities
```

---

## 推荐学习顺序

建议先按 10 个阶段学习基础层：

```text
第 1 阶段：RAG 基础回顾
第 2 阶段：知识图谱基础
第 3 阶段：GraphRAG 核心原理
第 4 阶段：GraphRAG 数据处理流程
第 5 阶段：实体关系抽取
第 6 阶段：图数据库与图存储
第 7 阶段：GraphRAG 检索流程
第 8 阶段：GraphRAG 与向量检索结合
第 9 阶段：GraphRAG 项目实战路线
第 10 阶段：常见问题与面试表达
```

如果你觉得基础层太简单，再继续进阶层：

```text
第 11 阶段：GraphRAG 进阶学习路线
第 12 阶段：实体消歧与关系去重
第 13 阶段：社区发现与社区摘要深化
第 14 阶段：检索策略与上下文编排
第 15 阶段：GraphRAG 评估与调优
第 16 阶段：FastAPI 实现 GraphRAG 项目
```

---

## 每个阶段要达到什么程度

### 第 1 阶段：RAG 基础回顾

目标：

```text
能画出普通 RAG 流程，知道它为什么会漏掉跨文档关系。
```

### 第 2 阶段：知识图谱基础

目标：

```text
能用实体、关系、属性描述一段文本里的知识。
```

### 第 3 阶段：GraphRAG 核心原理

目标：

```text
能解释 GraphRAG 为什么通过图来增强检索。
```

### 第 4 阶段：GraphRAG 数据处理流程

目标：

```text
能说清从文档到 chunk、实体、关系、社区、摘要的完整流程。
```

### 第 5 阶段：实体关系抽取

目标：

```text
能设计一个简单 prompt，让 LLM 从文本里抽取实体和关系。
```

### 第 6 阶段：图数据库与图存储

目标：

```text
能知道实体、关系、chunk、社区摘要可以怎么存。
```

### 第 7 阶段：GraphRAG 检索流程

目标：

```text
能区分局部检索、全局检索、DRIFT 类检索思路。
```

### 第 8 阶段：GraphRAG 与向量检索结合

目标：

```text
能设计一个混合检索流程，把向量召回和图扩展结合起来。
```

### 第 9 阶段：GraphRAG 项目实战路线

目标：

```text
能做一个小型企业知识库 GraphRAG Demo。
```

### 第 10 阶段：常见问题与面试表达

目标：

```text
能把 GraphRAG 讲给别人听，能回答为什么不用普通 RAG。
```

### 第 11 阶段：GraphRAG 进阶学习路线

目标：

```text
知道 GraphRAG 为什么概念简单但工程复杂。
```

### 第 12 阶段：实体消歧与关系去重

目标：

```text
能处理同物不同名、同名不同物、重复关系和关系来源。
```

### 第 13 阶段：社区发现与社区摘要深化

目标：

```text
能解释社区摘要如何支持 Global Search。
```

### 第 14 阶段：检索策略与上下文编排

目标：

```text
能设计 local / global / hybrid 多路召回和上下文预算。
```

### 第 15 阶段：GraphRAG 评估与调优

目标：

```text
能对比普通 RAG 和 GraphRAG，并分析失败案例。
```

### 第 16 阶段：FastAPI 实现 GraphRAG 项目

目标：

```text
能把 GraphRAG 拆成 endpoint、service、repository 并设计接口。
```

---

## 最后如何落地成可展示项目

推荐项目：

```text
企业知识库 GraphRAG 问答系统
```

适合展示的场景：

```text
文档问答：从多份制度文档里回答问题。
合同审查：找出合同中的主体、义务、风险条款和相关关系。
代码知识库：理解模块、函数、类、调用关系。
Agent 记忆系统：把用户、任务、工具调用、决策过程组织成图。
```

最小项目架构：

```text
FastAPI
-> 文档上传
-> 文档切分
-> 实体关系抽取
-> 图存储
-> 向量存储
-> 查询接口
-> LLM 生成答案
```

文字版系统流程图：

```text
用户上传文档
-> 后台解析文本
-> 切成 chunks
-> LLM 抽取实体和关系
-> 保存图数据
-> 为 chunk / entity / report 生成 embedding
-> 用户提问
-> 选择局部检索 / 全局检索 / 混合检索
-> 组装上下文
-> LLM 生成答案并返回引用
```

---

## 核心概念解释

这套路线里最核心的概念有 6 个：

```text
RAG：先检索资料，再让大模型回答。
实体：文档里重要的人、组织、项目、合同、模块、概念。
关系：实体之间的连接，例如负责、使用、调用、包含。
图：由实体节点和关系边组成的知识网络。
社区：图里联系紧密的一组实体，可以理解成一个主题区域。
混合检索：把向量检索和图检索结合起来。
```

这些概念的关系是：

```text
文档提供原始知识。
实体和关系把知识结构化。
图把分散知识连接起来。
社区摘要帮助回答全局问题。
向量检索帮助找到语义相似文本。
GraphRAG 把这些能力组合起来做问答。
```

---

## 通俗理解

如果普通 RAG 像是在资料堆里找几段相似文字，那么 GraphRAG 更像是：

```text
先给资料画一张知识地图。
地图上有人、项目、合同、系统、风险点。
它们之间有负责、依赖、包含、影响等关系。
用户提问时，系统既能查文字，也能沿着地图找关系。
```

所以 GraphRAG 最适合的问题不是：

```text
“某句话在哪里？”
```

而是：

```text
“这些内容之间有什么关系？”
“整体有哪些主题？”
“哪些对象共同影响一个风险？”
```

---

## 技术流程图

总流程可以分成离线和在线两部分：

```text
离线阶段：
文档
-> 解析文本
-> 切分 chunk
-> 抽取实体和关系
-> 合并实体
-> 构建图
-> 社区发现
-> 生成社区摘要
-> 保存图数据和向量数据

在线阶段：
用户问题
-> 判断问题类型
-> 局部检索：找实体和邻居
-> 全局检索：找社区摘要
-> 混合检索：结合向量 chunk 和图关系
-> 组装上下文
-> LLM 生成答案
-> 返回答案和引用来源
```

---

## 关键代码/伪代码示例

```python
def build_index(documents):
    chunks = split_documents(documents)
    entities, relations = extract_entities_and_relations(chunks)
    graph = build_graph(entities, relations)
    communities = detect_communities(graph)
    reports = summarize_communities(communities)
    save(chunks, graph, reports)


def ask(question, mode="hybrid"):
    if mode == "global":
        context = search_community_reports(question)
    elif mode == "local":
        context = search_entity_neighbors(question)
    else:
        context = hybrid_search(question)

    return llm_answer(question, context)
```

这段伪代码只表达主干：

```text
build_index 负责把文档变成图。
ask 负责根据问题检索图和文本，再让 LLM 回答。
```

---

## 实际项目中怎么用

你可以把 GraphRAG 用在这些项目里：

```text
文档问答：回答公司制度、课程笔记、产品手册问题。
企业知识库：总结组织流程、部门职责、风险主题。
合同审查：抽取甲乙方、条款、义务、风险关系。
代码知识库：抽取模块、类、函数、接口、数据库表之间的关系。
Agent 记忆系统：保存用户目标、任务、工具调用、结果和决策路径。
```

最推荐新手先做：

```text
企业知识库 GraphRAG 问答系统
```

因为它既能体现普通 RAG，也能体现图的价值。

---

## 容易混淆的点

### 1. GraphRAG 不是只加图数据库

图数据库只是存储工具。  
GraphRAG 的关键是图参与检索和上下文组织。

### 2. GraphRAG 不是替代向量检索

很多 GraphRAG 系统仍然会使用 embedding 和向量检索。  
图和向量是互补关系。

### 3. 全局检索不是搜索所有 chunk

全局检索通常使用社区摘要等压缩后的高层信息。

### 4. 社区发现不是人工分类

社区发现是根据实体关系图自动找到联系紧密的主题团块。

### 5. GraphRAG 不一定适合简单问题

如果只是单文档事实问答，普通 RAG 可能更简单、更便宜。

---

## 学完后我应该能回答的问题

1. GraphRAG 是什么？
2. GraphRAG 和普通 RAG 最大区别是什么？
3. GraphRAG 为什么需要图？
4. 图解决了传统 RAG 的什么问题？
5. 什么是实体？
6. 什么是关系？
7. 什么是社区发现？
8. 什么是全局检索？
9. 什么是局部检索？
10. 什么是混合检索？
11. GraphRAG 适合哪些项目？
12. 学完后应该做什么 Demo？
13. 实体消歧为什么重要？
14. 社区摘要为什么影响全局检索？
15. GraphRAG 应该怎么评估？
16. GraphRAG 怎么接入 FastAPI 分层项目？

---

## 参考资料

- Microsoft GraphRAG 官方文档：https://microsoft.github.io/graphrag/
- GraphRAG GitHub：https://github.com/microsoft/graphrag
- 论文 From Local to Global: A Graph RAG Approach to Query-Focused Summarization：https://arxiv.org/abs/2404.16130

下一篇：[01_RAG基础回顾.md](01_RAG基础回顾.md)
