# 16 FastAPI 实现 GraphRAG 项目

这一节把 GraphRAG 和你正在学的 FastAPI 接起来。  
目标不是一口气做工业级系统，而是设计一个能逐步实现的项目骨架。

---

## 本节学习目标

学完本节后，你应该能：

- 设计 GraphRAG 项目的 FastAPI 目录结构。
- 知道 endpoint、service、repository 在 GraphRAG 项目中的职责。
- 设计文档上传、索引、图查询、问答接口。
- 设计基础数据库表。
- 规划从 MVP 到进阶版的实现顺序。

---

## 核心概念解释

### 1. endpoint

endpoint 负责 HTTP 层：

```text
接收请求
校验参数
调用 service
返回响应
```

它不应该直接写复杂 GraphRAG 逻辑。

### 2. service

service 负责业务流程：

```text
文档处理
索引构建
实体关系抽取
检索编排
答案生成
```

### 3. repository

repository 负责数据访问：

```text
documents 表
chunks 表
entities 表
relations 表
community_reports 表
```

### 4. background job

GraphRAG 索引可能很慢。  
真实项目里最好放到后台任务：

```text
上传文档后立即返回 job_id。
后台慢慢解析、抽取、构图。
用户通过 job_id 查询状态。
```

新手第一版可以同步执行，第二版再加后台任务。

### 5. retrieval mode

问答接口可以支持：

```text
vector
local
global
hybrid
auto
```

---

## 通俗理解

你可以把 FastAPI GraphRAG 项目拆成 5 条线：

```text
文档线：上传、解析、切块。
抽取线：实体、关系、清洗。
存储线：表、图、向量。
检索线：local、global、hybrid。
问答线：组装上下文、调用 LLM、返回引用。
```

每条线都可以先做简单版，再逐步升级。

---

## 技术流程图

项目模块：

```text
app/
  main.py
  api/
    v1/
      router.py
      endpoints/
        documents.py
        indexing.py
        graph.py
        ask.py
        jobs.py
  schemas/
    document.py
    graph.py
    ask.py
    job.py
  services/
    document_service.py
    chunk_service.py
    extraction_service.py
    graph_service.py
    retrieval_service.py
    answer_service.py
    indexing_service.py
  repositories/
    document_repository.py
    chunk_repository.py
    entity_repository.py
    relation_repository.py
    report_repository.py
  core/
    config.py
    errors.py
```

请求流程：

```text
POST /documents/upload
-> document_service
-> document_repository

POST /index
-> indexing_service
-> chunk_service
-> extraction_service
-> graph_service
-> repositories

POST /ask
-> retrieval_service
-> answer_service
-> LLM
```

---

## 关键代码/伪代码示例

### 1. API 设计

```python
@router.post("/documents/upload")
def upload_document(file: UploadFile):
    return document_service.upload(file)


@router.post("/index")
def build_index(request: BuildIndexRequest):
    return indexing_service.build_index(request.document_ids)


@router.get("/graph/entities")
def list_entities(keyword: str | None = None):
    return graph_service.list_entities(keyword)


@router.get("/graph/entities/{entity_id}/neighbors")
def get_entity_neighbors(entity_id: str, depth: int = 1):
    return graph_service.get_neighbors(entity_id, depth)


@router.post("/ask")
def ask(request: AskRequest):
    return answer_service.answer(
        question=request.question,
        mode=request.mode,
    )
```

### 2. Schema 设计

```python
class AskRequest(BaseModel):
    question: str
    mode: Literal["vector", "local", "global", "hybrid", "auto"] = "auto"
    top_k: int = 8
    include_sources: bool = True


class AskResponse(BaseModel):
    answer: str
    mode: str
    sources: list[SourceItem]
    retrieval: dict
```

### 3. Service 编排

```python
def answer(question: str, mode: str) -> dict:
    selected_mode = retrieval_service.resolve_mode(question, mode)
    context = retrieval_service.retrieve(question, selected_mode)
    answer_text = llm_service.generate_answer(question, context)

    return {
        "answer": answer_text,
        "mode": selected_mode,
        "sources": context.sources,
        "retrieval": context.debug_info,
    }
```

### 4. 数据表草案

```sql
documents(id, title, source_path, status, created_at)
chunks(id, document_id, text, page_no, section, created_at)
entities(id, name, type, description, aliases, created_at)
relations(id, source_entity_id, target_entity_id, type, description, confidence)
relation_sources(id, relation_id, chunk_id)
community_reports(id, title, summary, level, entity_ids, created_at)
```

---

## 实际项目中怎么用

### MVP 版本

先做：

```text
1. 上传 TXT / Markdown
2. 简单切块
3. LLM 抽实体关系
4. 用普通表保存 entities / relations
5. 用 Chroma 保存 chunk 向量
6. 实现 /ask/hybrid
```

### 第二版

增加：

```text
1. 实体 alias
2. 关系去重
3. /graph/entities
4. /graph/entities/{id}/neighbors
5. local / global / hybrid 模式
```

### 第三版

增加：

```text
1. 社区发现
2. 社区摘要
3. report embedding
4. global search
5. 评估问题集
```

### 第四版

增加工程能力：

```text
1. 后台任务
2. job 状态
3. 日志
4. 错误处理
5. README 演示脚本
6. Docker Compose
```

---

## 容易混淆的点

### 1. 不要把所有逻辑写 endpoint 里

endpoint 应该薄一点。  
复杂流程放 service。

### 2. 不要第一版就上全套数据库

第一版可以：

```text
SQLite/PostgreSQL + Chroma
```

先跑通流程。

### 3. 不要忽略处理状态

索引会失败。  
每个 document/job 都应该有状态。

### 4. 不要把 LLM 调用散落各处

最好封装成：

```text
llm_service
embedding_service
```

以后换模型更方便。

### 5. 不要只返回 answer

建议返回：

```text
answer
sources
retrieval debug_info
```

这样你才能调试 GraphRAG。

---

## 学完后我应该能回答的问题

1. GraphRAG 项目应该有哪些 endpoint？
2. endpoint、service、repository 分别负责什么？
3. 为什么索引适合放后台任务？
4. `/ask` 请求体应该包含哪些字段？
5. `AskResponse` 为什么要有 sources？
6. GraphRAG 最小数据表有哪些？
7. MVP 版本应该先做什么？
8. 第二版应该优先增强什么？
9. 为什么不要把 LLM 调用散落在各处？
10. 如何把 GraphRAG 接到你现在学的 FastAPI 分层结构？

回到导航：[README.md](README.md)

