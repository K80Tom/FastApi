# FastAPI + AI Agent 应用开发学习路线

> 适用对象：研二计算机学生，Python 基础语法没问题，编程基础较好。  
> 学习目标：掌握 FastAPI，并能用它开发 AI 应用、RAG 服务、Agent 后端、流式接口、任务队列和可部署的工程项目。  
> 时间条件：工作日下班后每天约 1 小时，周末集中学习。  
> 建议周期：16 周。如果周末时间较少，可拉长到 20 周。

> 路线说明：这是一份综合路线，包含 FastAPI、AI 应用、RAG、Agent 和工程化内容。  
> 如果你想先单独学习 FastAPI 框架本体，请优先阅读：[01_FastAPI框架独立学习路线.md](01_FastAPI框架独立学习路线.md)。  
> 分类总览见：[00_学习路线分类总览.md](00_学习路线分类总览.md)。

---

## 1. 总体目标

学完这条路线后，你应该能独立完成一个较完整的 AI Agent 后端系统：

- 使用 FastAPI 构建清晰、可维护的 API 服务。
- 使用 Pydantic 定义请求、响应和 Agent 结构化数据。
- 使用异步编程对接 LLM、Embedding、外部工具和数据库。
- 实现普通聊天接口、流式聊天接口、RAG 问答接口和 Agent Run 接口。
- 管理用户、会话、消息、文档、任务、工具调用记录。
- 使用 PostgreSQL / Redis / 向量数据库支撑 AI 应用。
- 使用后台任务或任务队列处理长耗时任务。
- 编写测试、日志、配置、Docker 部署文件。
- 形成一套自己的 AI 后端工程模板。

最终毕业项目：

**Agent Knowledge Workspace**

一个支持用户登录、知识库上传、RAG 问答、Agent 工具调用、流式输出、历史记录、异步任务、Docker Compose 部署的 AI 应用后端。

---

## 2. 推荐技术栈

### 后端基础

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic v2
- HTTPX
- Pytest
- Ruff / Black

### 数据与状态

- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Redis
- pgvector 或 Chroma

### AI 应用

- OpenAI API 或兼容 OpenAI 协议的模型服务
- Embedding 模型
- LangGraph 或 OpenAI Agents SDK
- 可选：LlamaIndex、LangChain

### 工程化与部署

- Docker
- Docker Compose
- GitHub Actions 或其他 CI
- OpenTelemetry / structlog / loguru
- Celery / RQ / Arq 三选一

---

## 3. 学习节奏

### 工作日每天 1 小时

建议固定使用下面节奏：

1. 10 分钟：复盘昨天写了什么，确认今天的小目标。
2. 20 分钟：读官方文档或优秀代码。
3. 25 分钟：写代码，实现一个小功能。
4. 5 分钟：记录笔记，提交 Git commit。

工作日不要贪多，重点是保持连续性。

### 周末

建议每周末安排 6-8 小时：

- 周六：集中实现项目功能。
- 周日：补测试、重构、整理 README、复盘。

每周都要有一个可以运行的小成果，不要只看教程。

---

## 4. 16 周详细路线

## 第 1 周：FastAPI 入门与 HTTP API 基础

### 学习目标

理解 FastAPI 是如何把 Python 函数变成 HTTP API 的，掌握最基础的路由、参数、返回值和自动文档。

### 核心知识

- HTTP 基础：GET、POST、PUT、PATCH、DELETE。
- 状态码：200、201、202、204、400、401、403、404、409、422、500。
- JSON API 设计。
- FastAPI 应用对象：`app = FastAPI()`。
- 路径操作函数。
- 路径参数、查询参数、请求体。
- 自动 API 文档：`/docs` 和 `/redoc`。
- Uvicorn 启动方式。

### 推荐练习

写一个最小 API：

- `GET /health`
- `GET /items/{item_id}`
- `GET /items?keyword=xxx&page=1`
- `POST /items`
- `DELETE /items/{item_id}`

### 小项目 1：Prompt 模板管理 API，第一版

功能：

- 创建 Prompt 模板。
- 查看模板列表。
- 查看模板详情。
- 删除模板。
- 使用内存字典临时保存数据。

示例接口：

```text
GET    /health
POST   /prompts
GET    /prompts
GET    /prompts/{prompt_id}
DELETE /prompts/{prompt_id}
```

### 验收标准

- 能用 `uvicorn` 启动项目。
- 能在 `/docs` 中调试所有接口。
- 能解释路径参数和查询参数的区别。
- 能解释为什么请求体通常用 Pydantic 模型。

---

## 第 2 周：Pydantic 与数据校验

### 学习目标

掌握 FastAPI 的核心搭档 Pydantic。AI 应用中大量结构化输入输出都依赖它。

### 核心知识

- `BaseModel`
- 字段类型标注。
- 默认值和可选字段。
- `Field`
- 嵌套模型。
- 列表、字典、枚举。
- 请求模型与响应模型分离。
- `response_model`
- 422 校验错误。
- `model_dump()`、`model_validate()`。
- Pydantic v2 基本习惯。

### AI 相关重点

Agent 开发中，Pydantic 不只是表单校验工具，还可以用于：

- 约束 LLM 输出格式。
- 定义工具参数。
- 定义 Agent 状态。
- 定义任务结果。
- 定义 RAG 检索结果。
- 定义错误返回结构。

### 小项目 1：Prompt 模板管理 API，增强版

增加功能：

- Prompt 模板包含变量列表。
- 创建模板时校验变量名合法。
- 渲染模板：

```text
POST /prompts/{prompt_id}/render
```

请求示例：

```json
{
  "variables": {
    "topic": "FastAPI",
    "audience": "AI 工程师"
  }
}
```

返回示例：

```json
{
  "rendered_prompt": "请给 AI 工程师讲解 FastAPI"
}
```

### 验收标准

- 能区分 `PromptCreate`、`PromptUpdate`、`PromptRead`。
- 能用 `response_model` 控制返回字段。
- 能解释为什么不能直接把数据库模型暴露给外部 API。

---

## 第 3 周：项目结构、APIRouter 与分层

### 学习目标

把单文件 FastAPI 项目重构成真实项目结构。

### 核心知识

- Python 包结构。
- `APIRouter`
- router 分组。
- service 层。
- schema 层。
- dependency 层。
- 配置层。
- API version 前缀，例如 `/api/v1`。

### 推荐项目结构

```text
app/
  main.py
  api/
    v1/
      router.py
      endpoints/
        prompts.py
  core/
    config.py
    errors.py
  schemas/
    prompt.py
  services/
    prompt_service.py
  models/
  repositories/
tests/
```

### 小项目任务

重构 Prompt 模板管理 API：

- route 只处理 HTTP 层。
- service 负责业务逻辑。
- schema 定义输入输出。
- main.py 只做应用组装。

### 验收标准

- `main.py` 不超过 50 行。
- API 模块清晰。
- 新增一个功能时知道应该放在哪一层。

---

## 第 4 周：依赖注入、配置、异常与中间件

### 学习目标

掌握 FastAPI 的依赖注入能力，它是写出干净后端代码的关键。

### 核心知识

- `Depends`
- 子依赖。
- 全局依赖。
- router 级依赖。
- Pydantic Settings。
- `.env`
- 统一异常处理。
- 自定义异常类。
- 中间件。
- CORS。
- 请求日志。
- Request ID / Trace ID。

### AI 相关重点

依赖注入很适合管理：

- 当前用户。
- 数据库 Session。
- Redis 客户端。
- LLM Client。
- Embedding Client。
- Agent Service。
- 配置对象。

### 小项目任务

为 Prompt API 增加：

- 配置管理。
- 统一错误格式。
- 请求日志中间件。
- 简单 API Key 鉴权。

错误格式示例：

```json
{
  "error": {
    "code": "PROMPT_NOT_FOUND",
    "message": "Prompt not found",
    "request_id": "..."
  }
}
```

### 验收标准

- 能解释 `Depends` 的价值。
- 能用依赖注入替换硬编码对象。
- 能区分业务异常和系统异常。

---

## 第 5 周：异步编程与 HTTP 客户端

### 学习目标

掌握 FastAPI 中 `async def` 的使用边界，理解 AI 应用为什么大量使用异步 I/O。

### 核心知识

- `async def`
- `await`
- 协程。
- I/O bound 与 CPU bound。
- 阻塞调用的危害。
- `httpx.AsyncClient`
- 超时设置。
- 重试策略。
- 并发请求。
- 限流基础。

### AI 相关重点

LLM 调用、Embedding 调用、外部搜索、数据库查询都是典型 I/O 操作。  
如果在 async endpoint 中错误地调用阻塞函数，会影响并发能力。

### 小项目 2：LLM Chat Gateway，第一版

先用 mock LLM，不急着接真实模型。

接口：

```text
POST /chat
GET  /models
```

请求：

```json
{
  "message": "解释 FastAPI 的 Depends",
  "model": "mock-gpt"
}
```

返回：

```json
{
  "answer": "...",
  "model": "mock-gpt",
  "latency_ms": 120
}
```

### 验收标准

- 能解释什么时候用 `async def`，什么时候普通 `def` 也可以。
- 能给外部 HTTP 请求设置 timeout。
- 能处理外部服务失败。

---

## 第 6 周：流式响应、SSE 与 WebSocket

### 学习目标

实现 AI 聊天中常见的 token 流式输出。

### 核心知识

- `StreamingResponse`
- Server-Sent Events，简称 SSE。
- WebSocket 基础。
- 流式接口和普通接口的区别。
- 前端消费 SSE 的基本方式。
- 客户端断开连接处理。
- keep-alive。

### AI 相关重点

AI 应用通常不要等完整答案生成完再返回，而是边生成边返回。  
聊天产品、Agent 执行日志、工具调用进度，都适合流式返回。

### 小项目 2：LLM Chat Gateway，流式版

增加接口：

```text
POST /chat/stream
```

SSE 事件类型建议：

```text
event: message.delta
event: message.done
event: error
```

进阶事件：

```text
event: tool.started
event: tool.finished
event: run.step
```

### 验收标准

- 能用 curl 或浏览器看到流式输出。
- 能解释 SSE 和 WebSocket 的区别。
- 能设计一个基础 AI 流式协议。

---

## 第 7 周：数据库基础、SQLAlchemy 与 Alembic

### 学习目标

把内存数据改为数据库持久化。

### 核心知识

- PostgreSQL 基础。
- SQLAlchemy 2.x。
- ORM model。
- Session。
- 事务。
- 一对多关系。
- Alembic 数据库迁移。
- Repository 模式。

### AI 相关数据模型

建议重点设计这些表：

- users
- conversations
- messages
- prompts
- model_runs
- tool_calls
- documents
- document_chunks
- jobs

### 小项目任务

把 Prompt API 和 Chat Gateway 接入数据库：

- Prompt 模板持久化。
- Chat 消息持久化。
- 每次模型调用记录 latency、model、token usage。

### 验收标准

- 能写一个 Alembic migration。
- 能解释 ORM model 和 Pydantic schema 的区别。
- 能用事务保证数据一致性。

---

## 第 8 周：Redis、缓存、限流与会话状态

### 学习目标

掌握 Redis 在 AI 后端中的常见使用方式。

### 核心知识

- Redis 基本数据结构。
- 缓存。
- TTL。
- 简单分布式锁。
- API 限流。
- 会话临时状态。
- 幂等键。

### AI 相关场景

- 缓存模型列表。
- 缓存 embedding 结果。
- 存储临时 Agent run 状态。
- 限制用户请求频率。
- 防止重复提交文档解析任务。

### 小项目任务

给 Chat Gateway 增加：

- 用户级限流。
- 最近会话缓存。
- LLM 响应缓存，可选。

### 验收标准

- 能解释哪些数据适合放 Redis，哪些必须进数据库。
- 能实现一个简单 rate limiter。
- 能给缓存设置合理 TTL。

---

## 第 9 周：文件上传、文档解析与切块

### 学习目标

进入 RAG 应用开发，先处理知识库文档。

### 核心知识

- `UploadFile`
- `multipart/form-data`
- 文件大小限制。
- 文件类型校验。
- PDF / Markdown / TXT 解析。
- 文本清洗。
- chunking。
- metadata 设计。
- 文档处理任务状态。

### AI 相关重点

RAG 的质量很大程度取决于文档解析和切块，而不只是向量数据库。

常见切块策略：

- 固定长度切块。
- 按标题切块。
- 按段落切块。
- overlap。
- 保留 source、page、section 等 metadata。

### 小项目 3：Mini RAG，文档处理部分

接口：

```text
POST /documents/upload
GET  /documents
GET  /documents/{document_id}
POST /documents/{document_id}/chunks
GET  /documents/{document_id}/chunks
```

### 验收标准

- 能上传文档并保存 metadata。
- 能把文档切成 chunk。
- 能追踪文档处理状态：uploaded、parsed、chunked、embedded、failed。

---

## 第 10 周：Embedding、向量检索与 RAG 问答

### 学习目标

完成一个最小可用 RAG 服务。

### 核心知识

- Embedding 是什么。
- 向量相似度。
- top-k 检索。
- metadata filter。
- pgvector 或 Chroma。
- 上下文拼接。
- 引用来源。
- RAG 评估基础。

### RAG 基本流程

```text
用户问题
  -> 生成 query embedding
  -> 向量检索相关 chunks
  -> 组装 prompt
  -> 调用 LLM
  -> 返回答案和引用来源
```

### 小项目 3：Mini RAG，问答部分

接口：

```text
POST /ask
POST /ask/stream
```

请求：

```json
{
  "question": "FastAPI 的 Depends 有什么作用？",
  "top_k": 5
}
```

返回：

```json
{
  "answer": "...",
  "sources": [
    {
      "document_id": "...",
      "chunk_id": "...",
      "score": 0.82
    }
  ]
}
```

### 验收标准

- 能解释 RAG 和普通聊天的区别。
- 能返回答案来源。
- 能调节 `top_k` 并观察效果。

---

## 第 11 周：Agent 基础、工具调用与结构化输出

### 学习目标

从 RAG 进入 Agent：让模型不仅回答，还能调用工具。

### 核心知识

- Agent 的基本概念。
- Tool calling。
- Function schema。
- 结构化输出。
- 工具参数校验。
- 工具执行结果回传。
- 单轮 Agent loop。
- 多轮 Agent loop。
- 最大步数限制。
- 工具失败处理。

### 推荐先手写一个简单 Agent

不要一开始完全依赖框架。先手写能帮你理解本质：

```text
用户输入
  -> LLM 判断是否需要工具
  -> 执行工具
  -> 把工具结果交回 LLM
  -> 生成最终答案
```

### 小项目 4：Tool Agent API，第一版

工具：

- calculator
- current_time
- rag_search
- todo_create
- todo_list

接口：

```text
POST /agents/{agent_id}/runs
GET  /runs/{run_id}
GET  /runs/{run_id}/steps
```

### 验收标准

- 能定义一个工具的 Pydantic 参数模型。
- 能保存每次 tool call。
- 能限制 Agent 最大执行步数，避免死循环。

---

## 第 12 周：Agent 状态、记忆与 LangGraph / Agents SDK

### 学习目标

学习成熟 Agent 框架的状态管理能力。

### 可选框架方向

### 方向 A：LangGraph

适合：

- 多步骤工作流。
- 状态机。
- human-in-the-loop。
- 可恢复执行。
- 长流程 Agent。

重点学习：

- StateGraph。
- node。
- edge。
- conditional edge。
- checkpointer。
- streaming。
- interrupt。

### 方向 B：OpenAI Agents SDK

适合：

- OpenAI 生态。
- tools。
- handoff。
- guardrails。
- tracing。

重点学习：

- Agent。
- Runner。
- tool。
- handoff。
- tracing。
- streaming。

### 小项目任务

把第 11 周手写 Agent 改造成框架版：

- 支持状态持久化。
- 支持流式事件。
- 支持中间步骤查询。

### 验收标准

- 能解释 Agent state 包含什么。
- 能恢复一个未完成的 run。
- 能查询 Agent 执行轨迹。

---

## 第 13 周：后台任务与任务队列

### 学习目标

解决 AI 后端中的长耗时任务。

### 核心知识

- FastAPI `BackgroundTasks`。
- 任务队列。
- Celery / RQ / Arq。
- Redis broker。
- job status。
- retry。
- timeout。
- cancel。
- 幂等性。

### 什么时候不用 BackgroundTasks

下面情况不建议只用 FastAPI 内置 BackgroundTasks：

- 文档解析时间长。
- 批量 embedding。
- 长时间 Agent run。
- 需要重试。
- 需要任务状态查询。
- 需要独立 worker 扩容。

### 小项目任务

把文档解析、embedding、Agent run 改成 job：

接口：

```text
POST /jobs
GET  /jobs/{job_id}
POST /jobs/{job_id}/cancel
GET  /jobs/{job_id}/events
```

状态：

```text
queued
running
succeeded
failed
cancelled
```

### 验收标准

- 能解释 Web API 进程和 worker 进程的区别。
- 能实现 job 状态查询。
- 能处理任务失败重试。

---

## 第 14 周：鉴权、安全、日志与可观测性

### 学习目标

让 AI 应用从能跑变成可管理、可排查。

### 核心知识

- API Key 鉴权。
- JWT 基础。
- OAuth2 基础概念。
- 权限控制。
- CORS。
- 输入大小限制。
- Prompt injection 基础防护。
- 结构化日志。
- request_id。
- trace_id。
- metrics。
- OpenTelemetry。

### AI 相关观测指标

每次模型调用建议记录：

- request_id。
- user_id。
- conversation_id。
- run_id。
- model。
- prompt_tokens。
- completion_tokens。
- total_tokens。
- latency_ms。
- cost。
- error_code。
- tool_calls。

### 小项目任务

给现有项目增加：

- 用户登录或 API Key。
- 结构化日志。
- 模型调用日志。
- Agent run trace。
- 简单成本统计接口：

```text
GET /usage/me
GET /usage/daily
```

### 验收标准

- 能定位一次失败请求的完整链路。
- 能统计每个用户消耗了多少 token。
- 能解释 prompt injection 的基本风险。

---

## 第 15 周：测试、质量与压测

### 学习目标

让项目稳定，避免每次改动都靠手工点 Swagger。

### 核心知识

- Pytest。
- FastAPI TestClient。
- 依赖覆盖。
- 数据库测试。
- Mock 外部 LLM。
- 异步测试。
- 单元测试。
- 集成测试。
- 简单压测。
- Ruff / Black。

### AI 相关测试

AI 结果不稳定，所以测试应重点覆盖：

- API contract。
- 数据校验。
- 工具参数。
- RAG 检索是否返回来源。
- Agent 最大步数。
- 错误处理。
- mock LLM 场景。

不要把测试写成“模型必须回答某一句固定文本”。

### 小项目任务

给项目补充测试：

- Prompt API 测试。
- Chat API 测试。
- RAG API 测试。
- Agent tool call 测试。
- 鉴权测试。
- 错误返回测试。

### 验收标准

- 核心接口有测试。
- 外部模型调用可以 mock。
- 每次提交前能一键运行测试。

---

## 第 16 周：Docker 部署与毕业项目收尾

### 学习目标

完成可运行、可演示、可复用的 AI Agent 后端工程。

### 核心知识

- Dockerfile。
- Docker Compose。
- 多服务编排。
- 环境变量。
- 数据库迁移启动流程。
- 健康检查。
- Uvicorn / FastAPI 启动参数。
- 日志输出。
- README 编写。

### Docker Compose 服务建议

```text
api
worker
postgres
redis
```

如果使用 pgvector：

```text
postgres-pgvector
```

### 毕业项目：Agent Knowledge Workspace

最终功能清单：

- 用户注册 / 登录，或 API Key 鉴权。
- Prompt 模板管理。
- 普通聊天。
- 流式聊天。
- 文档上传。
- 文档解析和切块。
- Embedding 入库。
- RAG 问答。
- RAG 流式问答。
- Agent 工具调用。
- Agent run 记录。
- 任务队列。
- 调用日志和 token 统计。
- Docker Compose 一键启动。
- 核心接口测试。
- README 项目说明。

### 验收标准

- 新机器上可以根据 README 启动项目。
- `/docs` 能看到清晰 API 文档。
- 能完整演示：上传文档 -> 提问 -> Agent 调工具 -> 流式返回 -> 查看历史。
- 数据库中能查到消息、文档、run、tool call、usage。

---

## 5. 每个阶段的项目里程碑

### 里程碑 1：API 基础

完成时间：第 1-2 周。  
交付物：Prompt 模板管理 API。

能力证明：

- 会定义接口。
- 会用 Pydantic 校验。
- 会用 Swagger 调试。

### 里程碑 2：工程化 FastAPI 项目

完成时间：第 3-4 周。  
交付物：分层项目模板。

能力证明：

- 项目结构清晰。
- 有统一配置。
- 有统一异常。
- 有依赖注入。

### 里程碑 3：LLM Chat Gateway

完成时间：第 5-6 周。  
交付物：支持普通和流式输出的聊天 API。

能力证明：

- 会异步调用外部服务。
- 会处理超时和错误。
- 会实现 SSE。

### 里程碑 4：Conversation + Database

完成时间：第 7-8 周。  
交付物：持久化会话系统。

能力证明：

- 会设计数据表。
- 会使用 ORM。
- 会迁移数据库。
- 会使用 Redis。

### 里程碑 5：Mini RAG

完成时间：第 9-10 周。  
交付物：文档问答系统。

能力证明：

- 会上传和解析文档。
- 会切块和 embedding。
- 会向量检索。
- 会返回答案来源。

### 里程碑 6：Tool Agent

完成时间：第 11-12 周。  
交付物：支持工具调用的 Agent API。

能力证明：

- 会设计工具 schema。
- 会记录 Agent step。
- 会处理 Agent 状态。
- 会使用 LangGraph 或 Agents SDK。

### 里程碑 7：生产化

完成时间：第 13-16 周。  
交付物：可部署的 Agent 后端。

能力证明：

- 有任务队列。
- 有鉴权。
- 有日志和 usage。
- 有测试。
- 有 Docker 部署。

---

## 6. 必须掌握的 FastAPI 核心清单

### 路由与参数

- `@app.get`
- `@app.post`
- `@router.get`
- Path 参数。
- Query 参数。
- Body 参数。
- Header 参数。
- Cookie 参数。
- Form 参数。
- File 参数。

### Pydantic

- `BaseModel`
- `Field`
- 嵌套模型。
- Enum。
- 请求模型。
- 响应模型。
- 部分更新模型。
- 自定义校验。
- `model_dump`
- `model_validate`

### 依赖注入

- `Depends`
- 子依赖。
- yield dependency。
- DB Session 注入。
- 当前用户注入。
- Client 注入。
- 测试时 dependency override。

### 响应与异常

- `response_model`
- `JSONResponse`
- `StreamingResponse`
- `FileResponse`
- `HTTPException`
- 自定义异常处理器。
- 统一错误返回。

### 应用生命周期

- startup / shutdown。
- lifespan。
- 初始化数据库连接。
- 初始化 Redis。
- 初始化模型客户端。

### 中间件

- CORS。
- 请求日志。
- request_id。
- 耗时统计。
- 简单鉴权。

### 测试

- TestClient。
- async test。
- mock 外部服务。
- dependency override。
- 测试数据库。

---

## 7. AI Agent 后端必须掌握的相关知识

### LLM API

- Chat completion。
- Streaming。
- Tool calling。
- JSON mode / structured output。
- Timeout。
- Retry。
- Rate limit。
- Token usage。
- Cost tracking。

### Prompt 工程

- System prompt。
- User prompt。
- Prompt template。
- Few-shot examples。
- 输出格式约束。
- Prompt versioning。
- Prompt injection 风险。

### RAG

- 文档解析。
- Chunking。
- Embedding。
- Vector search。
- Hybrid search，可选。
- Rerank，可选。
- Context compression，可选。
- Citation。
- Retrieval evaluation。

### Agent

- Tool schema。
- Tool execution。
- Agent loop。
- Planner。
- Executor。
- Memory。
- State。
- Step log。
- Human-in-the-loop。
- Guardrails。
- Handoff。
- 最大步数限制。
- 超时和取消。

### 工程能力

- 数据建模。
- 异步 I/O。
- 任务队列。
- Redis。
- PostgreSQL。
- Docker。
- 日志。
- 测试。
- 监控。
- 安全。

---

## 8. 推荐学习资料

### FastAPI

- FastAPI 官方文档：https://fastapi.tiangolo.com/
- Bigger Applications：https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Async：https://fastapi.tiangolo.com/async/
- Testing：https://fastapi.tiangolo.com/tutorial/testing/
- Deployment Docker：https://fastapi.tiangolo.com/deployment/docker/

### Pydantic

- Pydantic 官方文档：https://docs.pydantic.dev/
- BaseModel：https://docs.pydantic.dev/latest/concepts/models/
- Validators：https://docs.pydantic.dev/latest/concepts/validators/
- Settings：https://docs.pydantic.dev/latest/concepts/pydantic_settings/

### 数据库

- SQLAlchemy：https://docs.sqlalchemy.org/
- SQLAlchemy asyncio：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic：https://alembic.sqlalchemy.org/
- PostgreSQL：https://www.postgresql.org/docs/
- pgvector：https://github.com/pgvector/pgvector

### Agent / AI

- OpenAI API 文档：https://platform.openai.com/docs/
- OpenAI Agents SDK：https://platform.openai.com/docs/guides/agents-sdk/
- LangGraph 文档：https://docs.langchain.com/oss/python/langgraph/
- LlamaIndex 文档：https://docs.llamaindex.ai/

### 工程化

- Docker 文档：https://docs.docker.com/
- Docker Compose：https://docs.docker.com/compose/
- Celery：https://docs.celeryq.dev/
- OpenTelemetry Python：https://opentelemetry.io/docs/languages/python/

---

## 9. 每周复盘模板

每周日晚上用 15 分钟写复盘：

```text
本周主题：

完成了什么：

卡住的问题：

我真正理解的概念：

还不清楚的概念：

下周要完成的项目功能：

本周代码仓库 commit：
```

不要只记录“看了什么”，要记录“做出了什么”。

---

## 10. 每天学习记录模板

```text
日期：
今天目标：

今天写了什么代码：

遇到的问题：

解决方式：

明天继续：
```

---

## 11. 毕业项目 README 建议结构

```text
# Agent Knowledge Workspace

## 项目简介

## 技术栈

## 功能列表

## 系统架构

## 数据模型

## API 文档

## 本地启动

## Docker Compose 启动

## 环境变量

## 测试

## 目录结构

## 后续优化
```

---

## 12. 最终自测清单

当你能完成下面这些事情，就说明 FastAPI + AI Agent 后端开发已经入门到可以做真实项目的程度：

- 能从零创建一个 FastAPI 多文件项目。
- 能设计清晰的 REST API。
- 能用 Pydantic 定义请求和响应。
- 能用依赖注入管理 DB、Redis、LLM Client。
- 能实现统一错误处理。
- 能实现流式聊天接口。
- 能接入 PostgreSQL 并写 Alembic migration。
- 能用 Redis 做限流或缓存。
- 能上传文档、解析、切块、embedding。
- 能完成一个基础 RAG。
- 能实现 Agent 工具调用。
- 能保存 Agent 执行步骤。
- 能把长任务放入 worker。
- 能记录 token、耗时和错误。
- 能写核心接口测试。
- 能用 Docker Compose 启动完整服务。
- 能写清楚 README，让别人能运行你的项目。

---

## 13. 学习建议

1. 官方文档优先，不要一开始沉迷二手教程。
2. 每周必须写代码，不要只看。
3. 所有项目都保留 Git commit。
4. 先手写简单版本，再引入框架。
5. AI 后端的核心不是“调模型”，而是状态、数据、可靠性和可观测性。
6. RAG 项目要重视文档处理和数据质量。
7. Agent 项目要重视工具边界、最大步数、失败恢复和执行日志。
8. 不要等项目完美再部署，能跑起来就尽早 Docker 化。
9. 学完 16 周后，把毕业项目整理成作品集项目。

---

## 14. 16 周压缩总览

```text
第 1 周：FastAPI 基础、HTTP、路由
第 2 周：Pydantic、请求响应模型
第 3 周：APIRouter、多文件结构、分层
第 4 周：Depends、配置、异常、中间件
第 5 周：async/await、HTTPX、外部 LLM
第 6 周：StreamingResponse、SSE、WebSocket
第 7 周：PostgreSQL、SQLAlchemy、Alembic
第 8 周：Redis、缓存、限流、会话状态
第 9 周：文件上传、文档解析、切块
第 10 周：Embedding、向量检索、RAG
第 11 周：Agent、工具调用、结构化输出
第 12 周：LangGraph / Agents SDK、状态持久化
第 13 周：后台任务、任务队列、worker
第 14 周：鉴权、安全、日志、可观测性
第 15 周：测试、Mock、质量、压测
第 16 周：Docker、部署、毕业项目收尾
```

---

## 15. 推荐的第一个仓库命名

建议把后续学习代码统一放在一个仓库中：

```text
fastapi-agent-lab
```

里面按阶段保存：

```text
fastapi-agent-lab/
  week01_basic_api/
  week02_pydantic/
  week03_project_structure/
  ...
  final_agent_workspace/
```

也可以一直演进一个项目，这样更接近真实开发。推荐做法是：

- 前 4 周：小项目独立练习。
- 第 5 周开始：逐渐合并成一个长期项目。
- 第 9 周后：所有能力都服务于毕业项目。

---

## 16. 最重要的一句话

FastAPI 对 AI 应用开发的价值，不只是“写几个接口调用大模型”，而是帮你把 AI 能力包装成稳定、可维护、可观测、可部署的后端服务。  
你真正要掌握的是：**API 设计 + 异步 I/O + 数据状态 + 流式输出 + Agent 执行轨迹 + 工程化部署**。
