# 09 GraphRAG 项目实战路线

前面已经学完 GraphRAG 的核心概念和主要流程。本节把这些知识落到一个可展示项目上。

---

## 本节学习目标

学完本节后，你应该能：

- 设计一个 GraphRAG Demo 项目。
- 知道项目应该有哪些模块。
- 知道 FastAPI 接口怎么设计。
- 知道最小版本应该先做什么。
- 能把 GraphRAG 用到文档问答、合同审查、代码知识库或 Agent 记忆系统。

---

## 核心概念解释

### 1. 可展示项目

可展示项目不是只写一堆脚本，而是要能演示完整流程：

```text
上传文档
-> 构建索引
-> 查看实体关系
-> 提问
-> 返回答案和引用
```

### 2. MVP

MVP 是 Minimum Viable Product，最小可用产品。

通俗说：

```text
先做一个小但能跑通全流程的版本。
```

不要一开始就追求：

```text
多租户、复杂权限、大规模分布式、完整图数据库、异步任务队列
```

先让它能跑起来。

### 3. Pipeline

Pipeline 是处理流水线。

GraphRAG 项目里常见 pipeline：

```text
文件 -> 文本 -> chunk -> 实体关系 -> 图 -> 社区摘要 -> 检索 -> 回答
```

### 4. 引用来源

引用来源是回答时告诉用户：

```text
答案依据来自哪份文档、哪一页、哪一个 chunk。
```

这很重要，因为 RAG 项目不能只给答案，还要让用户知道答案从哪里来。

---

## 通俗理解

做 GraphRAG 项目像搭一条知识加工流水线：

```text
原材料：文档
第一道工序：解析文本
第二道工序：切块
第三道工序：抽实体和关系
第四道工序：做知识地图
第五道工序：做检索
第六道工序：生成答案
```

你的项目展示时要让别人看到：

```text
不是模型凭空回答。
它先查资料，再看关系，最后基于证据回答。
```

---

## 技术流程图

推荐项目结构：

```text
graphrag-demo/
  app/
    main.py
    api/
      endpoints/
        documents.py
        indexing.py
        graph.py
        ask.py
    schemas/
      document.py
      graph.py
      ask.py
    services/
      document_service.py
      indexing_service.py
      extraction_service.py
      graph_service.py
      retrieval_service.py
      answer_service.py
    repositories/
      document_repository.py
      chunk_repository.py
      entity_repository.py
      relation_repository.py
    core/
      config.py
  docs/
  tests/
```

系统流程：

```text
用户上传文档
-> document_service 保存文件和元数据
-> indexing_service 解析并切块
-> extraction_service 抽取实体关系
-> graph_service 构建图和社区摘要
-> retrieval_service 根据问题检索上下文
-> answer_service 调用 LLM 生成答案
```

---

## 关键代码/伪代码示例

### 1. FastAPI 接口设计

```python
@router.post("/documents/upload")
def upload_document(file: UploadFile):
    return document_service.save_file(file)


@router.post("/index")
def build_index(document_ids: list[str]):
    return indexing_service.build_graphrag_index(document_ids)


@router.get("/graph/entities")
def list_entities():
    return graph_service.list_entities()


@router.get("/graph/relations")
def list_relations(entity_id: str | None = None):
    return graph_service.list_relations(entity_id)


@router.post("/ask")
def ask(request: AskRequest):
    return answer_service.answer(
        question=request.question,
        mode=request.mode,
    )
```

### 2. 索引服务伪代码

```python
def build_graphrag_index(document_ids: list[str]) -> dict:
    documents = document_repo.find_by_ids(document_ids)
    chunks = chunk_service.split_documents(documents)
    chunk_repo.save_many(chunks)

    entities = []
    relations = []
    for chunk in chunks:
        result = extraction_service.extract(chunk.text)
        entities.extend(result.entities)
        relations.extend(result.relations)

    entities = graph_service.merge_entities(entities)
    graph_service.save_graph(entities, relations)

    communities = graph_service.detect_communities()
    reports = graph_service.summarize_communities(communities)
    graph_service.save_reports(reports)

    vector_service.embed_chunks(chunks)
    vector_service.embed_reports(reports)

    return {"status": "indexed"}
```

### 3. 问答服务伪代码

```python
def answer(question: str, mode: str = "hybrid") -> dict:
    if mode == "global":
        context = retrieval_service.global_search(question)
    elif mode == "local":
        context = retrieval_service.local_search(question)
    else:
        context = retrieval_service.hybrid_search(question)

    answer_text = llm_service.generate_answer(question, context)

    return {
        "answer": answer_text,
        "sources": context.sources,
        "mode": mode,
    }
```

---

## 实际项目中怎么用

### 项目 1：企业知识库问答

数据：

```text
公司制度、流程文档、FAQ、培训材料
```

重点实体：

```text
部门、流程、角色、制度、审批节点、限制条件
```

可以演示的问题：

```text
“报销流程涉及哪些部门？”
“这批制度文档主要有哪些主题？”
“试用期转正流程有哪些关键节点？”
```

### 项目 2：合同审查助手

数据：

```text
合同文本、补充协议、条款模板
```

重点实体：

```text
甲方、乙方、合同、条款、义务、金额、日期、风险
```

可以演示的问题：

```text
“哪些合同存在付款风险？”
“供应商 A 相关合同有哪些违约责任？”
“这批合同的主要风险主题是什么？”
```

### 项目 3：代码知识库

数据：

```text
代码文件、README、接口文档、数据库表说明
```

重点实体：

```text
模块、类、函数、接口、数据库表、配置项
```

可以演示的问题：

```text
“登录流程涉及哪些函数和表？”
“UserService 依赖哪些模块？”
“这个项目的核心架构是什么？”
```

### 项目 4：Agent 记忆系统

数据：

```text
用户目标、任务步骤、工具调用、执行结果、历史对话
```

重点实体：

```text
用户、目标、任务、工具、结果、决策
```

可以演示的问题：

```text
“这个用户之前常做什么任务？”
“上次失败的工具调用和哪个目标有关？”
“Agent 最近的决策路径是什么？”
```

---

## 容易混淆的点

### 1. 不要一开始做太大

先用 10 到 20 篇文档做 Demo。  
确认流程能跑，再扩大数据量。

### 2. 不要只做抽取，不做问答

GraphRAG 项目最终要服务问答。  
只展示实体关系图还不够。

### 3. 不要忽略引用来源

没有引用来源，用户很难信任答案。

### 4. 不要一开始追求自动化全流程

新手可以先手动触发：

```text
上传 -> 点击索引 -> 点击提问
```

等流程稳定后再做后台任务。

### 5. 不要把 GraphRAG 做成单个脚本

建议按照 service、repository、schema 分层。  
这样和你正在学的 FastAPI 路线能接上。

---

## 学完后我应该能回答的问题

1. GraphRAG Demo 应该包含哪些功能？
2. 什么是 MVP？
3. GraphRAG 项目有哪些核心模块？
4. FastAPI 接口可以怎么设计？
5. 为什么要返回引用来源？
6. 企业知识库项目适合抽哪些实体？
7. 合同审查项目适合问哪些问题？
8. 代码知识库里图关系有什么用？
9. Agent 记忆系统为什么适合 GraphRAG？
10. 为什么不要一开始做太大？

下一篇：[10_常见问题与面试表达.md](10_常见问题与面试表达.md)

