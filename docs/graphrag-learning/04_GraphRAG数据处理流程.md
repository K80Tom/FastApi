# 04 GraphRAG 数据处理流程

前面讲了 GraphRAG 的核心思想。本节进入工程视角：一批原始文档到底怎样一步步变成 GraphRAG 可以检索的知识结构？

---

## 本节学习目标

学完本节后，你应该能：

- 说清 GraphRAG 的离线索引流程。
- 理解文档解析、切块、实体抽取、关系抽取、图构建、社区发现、社区摘要之间的关系。
- 知道每一步的输入和输出。
- 能设计一个最小可行的数据处理 pipeline。

---

## 核心概念解释

### 1. 离线索引

离线索引指的是：

```text
用户提问之前，提前把文档处理成可检索的数据结构。
```

普通 RAG 的离线索引通常只做：

```text
文档 -> chunk -> embedding -> 向量库
```

GraphRAG 的离线索引会多做：

```text
实体抽取、关系抽取、图构建、社区发现、社区摘要
```

### 2. 文档解析

文档解析是把 PDF、Word、Markdown、网页等格式转成纯文本。

例如：

```text
PDF 文件 -> 文本段落
Markdown 文件 -> 标题、段落、代码块
网页 -> 正文文本
```

### 3. 文档切块

切块是把长文本拆成较短的 chunk。  
GraphRAG 也需要 chunk，因为实体和关系通常从 chunk 中抽取。

### 4. 实体关系抽取

用规则、NLP 模型或 LLM，从文本里找出：

```text
实体：人、组织、项目、概念、模块
关系：负责、属于、调用、依赖、包含
```

### 5. 图构建

把抽到的实体作为节点，把关系作为边。

### 6. 实体合并

同一个实体可能有多个写法：

```text
FastAPI
FastAPI 框架
fastapi
```

实体合并就是判断它们是不是同一个对象，并统一成一个实体。

### 7. 社区发现和社区摘要

图构建后，找出联系紧密的实体群，再让 LLM 总结每个群的主题。

---

## 通俗理解

GraphRAG 数据处理像整理一家公司资料室：

```text
第一步：把所有文件拆开读。
第二步：标出里面出现的人、项目、合同、系统。
第三步：画出它们之间的关系。
第四步：把关系密切的一组内容归成主题区域。
第五步：给每个主题区域写一份摘要。
```

这样用户提问时，系统不只是翻页找句子，还能看知识地图。

---

## 技术流程图

详细流程：

```text
原始文件
-> 文档解析
-> 清洗文本
-> 文档切块
-> 为 chunk 保存 source 信息
-> LLM 抽取实体
-> LLM 抽取关系
-> 实体标准化和合并
-> 构建图
-> 社区发现
-> 生成社区摘要
-> 保存 chunk、entity、relation、community、report、embedding
```

每一步输入输出：

| 步骤 | 输入 | 输出 |
| --- | --- | --- |
| 文档解析 | PDF/Markdown/Word | 纯文本 |
| 切块 | 纯文本 | chunks |
| 实体抽取 | chunk | entities |
| 关系抽取 | chunk + entities | relations |
| 图构建 | entities + relations | graph |
| 社区发现 | graph | communities |
| 社区摘要 | community | community report |
| 入库 | 所有中间结果 | 可检索数据 |

---

## 关键代码/伪代码示例

```python
def process_documents(files: list[File]) -> None:
    documents = []
    for file in files:
        text = parse_file(file)
        clean_text = clean_document_text(text)
        documents.append(clean_text)

    chunks = split_documents(documents)
    save_chunks(chunks)

    entities = []
    relations = []

    for chunk in chunks:
        result = extract_graph_items(chunk.text)
        entities.extend(result.entities)
        relations.extend(result.relations)

    entities = merge_duplicate_entities(entities)
    graph = build_graph(entities, relations)

    communities = detect_communities(graph)
    reports = []
    for community in communities:
        reports.append(summarize_community(community))

    save_entities(entities)
    save_relations(relations)
    save_communities(communities)
    save_reports(reports)
```

一个 chunk 最好保留来源信息：

```python
chunk = {
    "id": "chunk_001",
    "document_id": "doc_001",
    "text": "...",
    "page": 3,
    "section": "合同终止",
}
```

后面回答问题时才能返回引用来源。

---

## 实际项目中怎么用

在 FastAPI 项目里可以拆成这些任务：

```text
POST /documents/upload
-> 保存文件

POST /documents/{document_id}/parse
-> 解析文本

POST /documents/{document_id}/chunks
-> 切块

POST /index/graph
-> 抽取实体关系并构图

POST /index/communities
-> 社区发现和摘要
```

新手阶段也可以简化成一个接口：

```text
POST /index
```

它内部按顺序做完：

```text
解析 -> 切块 -> 抽取 -> 构图 -> 摘要 -> 入库
```

但真实项目里，建议把每一步记录状态：

```text
uploaded
parsed
chunked
extracted
graphed
summarized
failed
```

这样出错时更容易排查。

---

## 容易混淆的点

### 1. GraphRAG 不是查询时才抽图

大部分图构建工作应该提前做。  
否则每次提问都临时抽实体关系，速度会很慢。

### 2. chunk 仍然重要

GraphRAG 有图，但不代表不需要 chunk。  
chunk 是原文证据来源，也是实体关系抽取的基础。

### 3. 实体抽取不是一次就完美

LLM 抽取可能漏掉实体，也可能把同一个实体写成多个版本。  
所以需要实体合并和质量检查。

### 4. 社区摘要不是最终答案

社区摘要是检索上下文的一部分。  
最终答案仍然由 LLM 根据问题和上下文生成。

---

## 学完后我应该能回答的问题

1. 什么是离线索引？
2. GraphRAG 的离线索引比普通 RAG 多了哪些步骤？
3. 为什么 GraphRAG 仍然需要 chunk？
4. 实体抽取的输入是什么？
5. 关系抽取的输出是什么？
6. 为什么需要实体合并？
7. 社区发现发生在什么时候？
8. 社区摘要有什么用？
9. 实际项目中为什么要记录处理状态？
10. 如何设计一个最小 GraphRAG 数据处理 pipeline？

下一篇：[05_实体关系抽取.md](05_实体关系抽取.md)

