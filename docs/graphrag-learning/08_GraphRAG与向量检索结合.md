# 08 GraphRAG 与向量检索结合

上一节讲了 GraphRAG 的局部检索和全局检索。本节讲一个实际项目中非常重要的问题：GraphRAG 要不要和向量检索一起用？

答案通常是：

```text
要。
```

---

## 本节学习目标

学完本节后，你应该能：

- 理解图检索和向量检索各自擅长什么。
- 知道为什么 GraphRAG 不应该完全抛弃向量检索。
- 设计一个混合检索流程。
- 理解实体、chunk、社区摘要都可以做 embedding。
- 能为实际项目选择合适的检索策略。

---

## 核心概念解释

### 1. 向量检索擅长什么

向量检索擅长找语义相近的文本。

例如用户问：

```text
“员工报销发票有什么要求？”
```

即使文档里写的是：

```text
“费用报销需提供合法有效票据。”
```

向量检索也可能找到，因为语义接近。

### 2. 图检索擅长什么

图检索擅长找关系。

例如：

```text
“张三负责的项目涉及哪些合同风险？”
```

图可以沿着：

```text
张三 -> 项目 -> 合同 -> 风险
```

找到答案线索。

### 3. 混合检索

混合检索就是：

```text
向量检索 + 图检索
```

它可以先用向量找相关文本，再用图扩展关系；也可以先用图找相关实体，再用向量找原文证据。

### 4. 重排

重排是对召回结果再次排序。

例如先找出 30 个候选 chunk，再用 reranker 或 LLM 判断最相关的 5 个。

### 5. 多路召回

多路召回是从多个通道找候选上下文。

例如：

```text
向量召回 chunk
图召回实体邻居
社区摘要召回主题
关键词召回精确术语
```

然后合并、去重、排序。

---

## 通俗理解

向量检索像：

```text
根据语义相似找资料。
```

图检索像：

```text
根据关系路线找资料。
```

混合检索像：

```text
先问图书管理员哪些书主题相近。
再看知识地图里这些书和哪些人物、项目、合同有关。
最后把最可靠的段落拿给大模型回答。
```

---

## 技术流程图

一种常见混合流程：

```text
用户问题
-> 问题 embedding
-> 向量检索 top-k chunks
-> 从问题和 chunks 中识别实体
-> 在图中匹配实体
-> 扩展邻居和关系
-> 找关系来源 chunks
-> 合并向量 chunks 和图 chunks
-> 去重、重排、截断
-> LLM 回答
```

另一种流程：

```text
用户问题
-> 识别实体
-> 图扩展相关实体和关系
-> 根据实体描述 / 社区摘要做向量检索
-> 找原文证据
-> LLM 回答
```

---

## 关键代码/伪代码示例

```python
def hybrid_search(question: str) -> str:
    question_vector = embedding_model.embed(question)

    vector_chunks = chunk_vector_db.search(
        vector=question_vector,
        top_k=10,
    )

    question_entities = extract_entities_from_question(question)
    seed_entities = entity_repo.find_by_names(question_entities)

    graph_context = graph_repo.expand_neighbors(
        entities=seed_entities,
        depth=2,
        limit=50,
    )

    graph_chunk_ids = collect_source_chunks(graph_context.relations)
    graph_chunks = chunk_repo.find_by_ids(graph_chunk_ids)

    candidates = merge_and_deduplicate(vector_chunks, graph_chunks)
    ranked = rerank(question, candidates)
    final_context = build_context(ranked[:8], graph_context)

    return llm_answer(question, final_context)
```

可以给不同结果打分：

```python
score = (
    0.5 * vector_similarity
    + 0.3 * graph_relation_score
    + 0.2 * source_quality_score
)
```

新手阶段不用一开始做复杂打分，可以先简单合并去重。

---

## 实际项目中怎么用

### 文档问答

推荐：

```text
向量检索为主，图检索补充关系。
```

适合问题：

```text
“某个制度条款是什么意思？”
```

### 企业知识库

推荐：

```text
社区摘要 + 向量检索 + 局部图扩展
```

适合问题：

```text
“公司知识库里关于采购流程有哪些重点？”
```

### 合同审查

推荐：

```text
图检索找主体、条款和风险关系，向量检索找原文证据。
```

适合问题：

```text
“供应商 A 涉及哪些付款和违约风险？”
```

### 代码知识库

推荐：

```text
图检索调用关系，向量检索解释代码片段。
```

适合问题：

```text
“登录接口失败可能影响哪些模块？”
```

---

## 容易混淆的点

### 1. GraphRAG 不是不要 embedding

很多 GraphRAG 系统仍然会给 chunk、entity、report 做 embedding。  
图和向量是互补关系。

### 2. 混合检索不是把所有结果都塞进去

召回结果要去重、排序、截断。  
否则 prompt 太长，模型会抓不住重点。

### 3. 图扩展层数不是越深越好

一跳邻居信息少，三跳以上可能噪声很大。  
新手可以先从二跳开始。

### 4. 相似不等于相关

向量相似只能说明语义接近。  
图关系可以补充“真实连接”。

### 5. 相关不等于可信

无论图检索还是向量检索，最好回到原文 chunk 提供证据。

---

## 学完后我应该能回答的问题

1. 向量检索擅长什么？
2. 图检索擅长什么？
3. 为什么 GraphRAG 仍然需要向量检索？
4. 什么是混合检索？
5. 什么是多路召回？
6. 什么是重排？
7. 混合检索的一种基本流程是什么？
8. 为什么图扩展层数不能太深？
9. 合同审查场景怎么结合图和向量？
10. 代码知识库场景怎么结合图和向量？

下一篇：[09_GraphRAG项目实战路线.md](09_GraphRAG项目实战路线.md)

