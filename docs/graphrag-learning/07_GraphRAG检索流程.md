# 07 GraphRAG 检索流程

前面讲了如何构建图和存储图。本节进入查询阶段：用户提问后，GraphRAG 到底怎么检索？

---

## 本节学习目标

学完本节后，你应该能：

- 理解 GraphRAG 查询阶段的核心流程。
- 区分局部检索和全局检索。
- 理解社区摘要如何参与回答。
- 知道 DRIFT 类检索的大致思路。
- 能设计一个简单的 GraphRAG 查询接口。

---

## 核心概念解释

### 1. 查询阶段

查询阶段指的是：

```text
用户提出问题后，系统如何找上下文并让 LLM 回答。
```

普通 RAG 通常只做：

```text
问题 embedding -> top-k chunk -> LLM
```

GraphRAG 会多考虑：

```text
问题里有哪些实体？
这些实体在图上连着谁？
相关社区摘要是什么？
相关原文 chunk 是哪些？
```

### 2. 局部检索

局部检索适合从一个具体实体出发。

例如：

```text
“项目 A 关联了哪些风险？”
“UserService 依赖哪些模块？”
“合同 B 的甲乙方和付款条款是什么？”
```

流程通常是：

```text
识别问题里的实体
-> 找实体节点
-> 扩展一跳或二跳邻居
-> 找相关关系和原文 chunk
-> 组装上下文
```

### 3. 全局检索

全局检索适合宏观总结问题。

例如：

```text
“这批文档主要讲了哪些主题？”
“合同集合中有哪些常见风险？”
“整个代码库的核心模块有哪些？”
```

流程通常是：

```text
检索相关社区摘要
-> 对多个社区摘要进行排序或汇总
-> LLM 根据摘要回答全局问题
```

### 4. DRIFT 类检索

DRIFT 可以先理解成一种结合全局和局部的搜索思路。  
它不会只看社区摘要，也不会只看局部邻居，而是尝试在全局主题和局部细节之间动态移动。

通俗理解：

```text
先从较大的主题区域入手。
发现相关区域后，再钻到具体实体和文本证据。
```

新手阶段不用急着实现完整 DRIFT，先理解它的方向即可。

---

## 通俗理解

GraphRAG 查询像在地图上找答案。

局部检索：

```text
你已经知道一个地点，比如“项目 A”。
然后沿着项目 A 周围的道路，看它连接了谁。
```

全局检索：

```text
你不关心某一个地点，而是想知道整张地图有哪些区域。
比如商业区、住宅区、工业区。
```

混合或 DRIFT 类检索：

```text
先看地图上的大区域，再进入某个区域看具体街道。
```

---

## 技术流程图

局部检索：

```text
用户问题
-> 实体识别
-> 实体匹配
-> 图邻居扩展
-> 查找关系来源 chunk
-> 可选向量召回补充 chunk
-> 组装上下文
-> LLM 回答
```

全局检索：

```text
用户问题
-> 问题 embedding
-> 检索 community reports
-> 选择相关社区摘要
-> 可选展开社区内关键实体
-> 组装上下文
-> LLM 回答
```

DRIFT 类思路：

```text
用户问题
-> 初步找相关社区
-> 找社区内关键实体
-> 沿实体关系扩展
-> 回到原文证据
-> LLM 回答
```

---

## 关键代码/伪代码示例

### 1. 局部检索

```python
def local_search(question: str) -> str:
    entity_names = extract_entities_from_question(question)
    seed_entities = entity_repo.find_by_names(entity_names)

    subgraph = graph_repo.expand_neighbors(
        entities=seed_entities,
        depth=2,
        limit=50,
    )

    source_chunk_ids = collect_source_chunks(subgraph.relations)
    chunks = chunk_repo.find_by_ids(source_chunk_ids)

    context = build_local_context(subgraph, chunks)
    return llm_answer(question, context)
```

### 2. 全局检索

```python
def global_search(question: str) -> str:
    question_vector = embedding_model.embed(question)
    reports = report_vector_db.search(question_vector, top_k=5)

    context = "\n\n".join(report.summary for report in reports)
    return llm_answer(question, context)
```

### 3. 自动选择检索模式

```python
def choose_search_mode(question: str) -> str:
    if contains_specific_entity(question):
        return "local"
    if asks_for_overview(question):
        return "global"
    return "hybrid"
```

---

## 实际项目中怎么用

可以设计 3 个接口：

```text
POST /ask/local
POST /ask/global
POST /ask/hybrid
```

也可以只暴露一个接口：

```text
POST /ask
```

请求体：

```json
{
  "question": "这批合同有哪些主要风险？",
  "mode": "auto"
}
```

服务端内部：

```text
mode = local：走实体邻居扩展
mode = global：走社区摘要检索
mode = hybrid：图检索 + 向量检索一起用
mode = auto：让系统判断
```

不同场景推荐：

```text
文档问答：local + vector
企业知识库总结：global
合同审查：global 找风险主题，local 查具体合同和条款
代码知识库：local 查调用链，global 总结模块架构
Agent 记忆：local 查某个目标相关历史，global 总结长期偏好
```

---

## 容易混淆的点

### 1. 局部检索不是只查一个节点

局部检索通常会扩展邻居。  
只查一个实体本身，信息太少。

### 2. 全局检索不是把所有文档都塞给 LLM

全局检索依赖社区摘要等压缩后的全局信息。  
不是把所有 chunk 拼进 prompt。

### 3. 自动选择模式不是必须一开始就做

新手项目可以先让用户手动选择：

```text
local / global / hybrid
```

等流程稳定后再做 auto。

### 4. 图检索也需要原文证据

图上的关系是结构化结果，但回答时最好仍然引用原文 chunk。  
这样可信度更高。

### 5. 检索模式没有绝对优劣

具体事实问题适合 local。  
宏观总结问题适合 global。  
复杂问题适合 hybrid。

---

## 学完后我应该能回答的问题

1. GraphRAG 查询阶段做什么？
2. 什么是局部检索？
3. 什么是全局检索？
4. 什么问题适合局部检索？
5. 什么问题适合全局检索？
6. 社区摘要如何参与回答？
7. 为什么图检索仍然需要原文 chunk？
8. DRIFT 类检索大概想解决什么问题？
9. 如何设计 `/ask/local` 和 `/ask/global`？
10. 为什么新手可以先手动选择检索模式？

下一篇：[08_GraphRAG与向量检索结合.md](08_GraphRAG与向量检索结合.md)

