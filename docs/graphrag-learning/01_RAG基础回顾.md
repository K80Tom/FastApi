# 01 RAG 基础回顾

这一节先把普通 RAG 讲清楚。GraphRAG 不是凭空出现的，它是为了解决普通 RAG 在复杂知识场景里的不足。

---

## 本节学习目标

学完本节后，你应该能：

- 说清普通 RAG 的完整流程。
- 理解 chunk、embedding、向量数据库、top-k 是什么。
- 知道普通 RAG 为什么适合回答具体事实问题。
- 知道普通 RAG 为什么不擅长跨文档、跨关系、全局总结问题。
- 为后面理解 GraphRAG 做准备。

---

## 核心概念解释

### 1. RAG

RAG 是 Retrieval-Augmented Generation。

通俗说：

```text
大模型自己不一定知道你的私有文档。
所以先从你的知识库里查资料，再让大模型根据资料回答。
```

### 2. 文档切分

大模型一次能读的内容有限，向量检索也不适合直接处理一本完整文档。  
所以通常会把文档切成小块：

```text
原始文档 -> chunk 1 -> chunk 2 -> chunk 3
```

每个小块叫 `chunk`。

### 3. Embedding

Embedding 是把文本变成一串数字向量。

通俗理解：

```text
把一句话放到一个高维空间里。
意思相近的句子，位置更接近。
```

例如：

```text
“合同终止条件”
“协议解除条款”
```

这两句话字面不同，但语义接近，embedding 后距离可能比较近。

### 4. 向量数据库

向量数据库负责保存向量，并根据相似度查找最接近的内容。

常见向量数据库：

```text
Chroma
Milvus
Qdrant
Weaviate
pgvector
```

### 5. top-k

`top-k` 表示取最相似的前 k 个结果。

例如：

```text
top_k = 5
```

意思是：

```text
从知识库中找出最相关的 5 个 chunk。
```

---

## 通俗理解

普通 RAG 像是在图书馆查资料：

```text
用户提问
-> 图书管理员根据问题找几页最像的资料
-> 把资料交给一个很会写总结的人
-> 这个人根据资料组织答案
```

这个流程很适合：

```text
“某个制度里的报销上限是多少？”
“合同里付款时间怎么写？”
“FastAPI 的 Depends 是什么？”
```

但如果问题是：

```text
“这些合同里整体有哪些风险？”
“哪些系统模块共同影响登录流程？”
“公司 A 和项目 B、供应商 C 的关系是什么？”
```

普通 RAG 可能只拿到几个局部 chunk，看不到全局关系。

---

## 技术流程图

普通 RAG 流程：

```text
离线阶段：
原始文档
-> 文本解析
-> 文档切块
-> chunk embedding
-> 保存到向量数据库

在线阶段：
用户问题
-> question embedding
-> 向量数据库 top-k 检索
-> 拿到相关 chunks
-> 拼成 prompt
-> LLM 生成答案
```

---

## 关键代码/伪代码示例

```python
def build_rag_index(documents: list[str]) -> None:
    chunks = []
    for doc in documents:
        chunks.extend(split_text(doc))

    for chunk in chunks:
        vector = embedding_model.embed(chunk)
        vector_db.add(text=chunk, vector=vector)


def ask_with_rag(question: str) -> str:
    question_vector = embedding_model.embed(question)
    chunks = vector_db.search(question_vector, top_k=5)

    context = "\n\n".join(chunk.text for chunk in chunks)
    prompt = f"""
    请根据下面资料回答问题。

    资料：
    {context}

    问题：
    {question}
    """
    return llm.generate(prompt)
```

这段代码表达的是普通 RAG 的核心：

```text
文档变向量。
问题也变向量。
根据相似度找文本。
把文本交给 LLM。
```

---

## 实际项目中怎么用

普通 RAG 适合做这些项目：

```text
个人知识库问答
公司制度问答
产品说明书问答
课程笔记问答
客服 FAQ 问答
```

一个 FastAPI 项目里可以这样设计接口：

```text
POST /documents/upload      上传文档
POST /documents/index       建立向量索引
POST /ask                   用户提问
GET  /documents/{id}        查看文档
```

普通 RAG 的最小数据表：

```text
documents：保存文档信息
chunks：保存切块文本
embeddings：保存 chunk 向量，或者交给向量数据库
```

---

## 容易混淆的点

### 1. RAG 不是让模型重新训练

RAG 不会改变大模型参数。  
它只是把检索到的资料放进 prompt，让模型参考资料回答。

### 2. embedding 不是关键词匹配

关键词匹配看字面。  
embedding 看语义相似。

但 embedding 也不是万能的，它可能漏掉关系型问题。

### 3. top-k 越大不一定越好

top-k 太小，可能漏资料。  
top-k 太大，可能塞进很多噪声，让模型更困惑。

### 4. 普通 RAG 不等于 GraphRAG

普通 RAG 主要查文本块。  
GraphRAG 还会显式组织实体、关系、社区和摘要。

---

## 学完后我应该能回答的问题

1. RAG 是什么？
2. 为什么 RAG 要先检索再生成？
3. 什么是 chunk？
4. 什么是 embedding？
5. 向量数据库负责什么？
6. top-k 是什么意思？
7. 普通 RAG 适合回答什么问题？
8. 普通 RAG 为什么不擅长全局总结？
9. 普通 RAG 为什么容易漏掉跨文档关系？
10. GraphRAG 要解决普通 RAG 的什么问题？

下一篇：[02_知识图谱基础.md](02_知识图谱基础.md)

