#!/usr/bin/env python3
"""生成 FastAPI 教程的确定性 SVG/PNG 技术图解。

运行：python tools/generate_diagrams.py
依赖：Pillow（仅 PNG 导出需要）；所有文字与节点均来自本文件，不调用图像模型。
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images"
WIDTH, HEIGHT = 1600, 1000
FONT = "PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif"
MONO = "Menlo, SFMono-Regular, Consolas, Liberation Mono, monospace"
PNG_FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
PNG_BOLD_FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
PNG_MONO_FONT_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

# 每张图都对应正文的一条完整知识链：五步主流程、异常出口、示例、拆解和验收。
DIAGRAMS = [
    dict(num="00", slug="roadmap", title="FastAPI 八周学习地图", core="先建立请求响应直觉，再逐层加入工程能力；每周都有可运行、可验证的 TaskHub 版本。",
         steps=[("第 1 周｜跑通 API", "HTTP 方法与状态码\n路径／查询／请求体\n内存版任务 CRUD"), ("第 2 周｜约束数据", "Pydantic 校验\n请求与响应模型\n嵌套与统一响应"), ("第 3 周｜拆清职责", "APIRouter 与 /api/v1\nendpoint/service/repository\n异常、依赖、配置"), ("第 4～5 周｜增强边界", "中间件、CORS、API Key\nasync、文件、后台任务\n流式响应与 WebSocket"), ("第 6～8 周｜交付项目", "SQLAlchemy 与 Alembic\nJWT 与资源级权限\nPytest、CI、Docker")],
         exception="任何一章都遵循：先复现问题 → 小步修改 → 运行验证 → 解释为什么，而不是只复制最终代码。",
         code=["GET /api/v1/tasks?page=1&page_size=20", "→ endpoint 接收 HTTP", "→ service 执行业务规则", "→ repository 访问数据", "← 统一 JSON / 统一错误"],
         details=["输入模型负责校验客户端数据，响应模型限制服务端输出。", "内存仓库与数据库仓库实现同一职责，替换时不改 HTTP 合约。", "鉴权回答“你是谁”，权限回答“你能否操作这条资源”。", "测试和 Docker 是交付的一部分，不是项目结束后的补充。"],
         checks=["能独立启动应用并打开 /docs。", "能解释一次请求经过的每一层。", "能用测试证明成功与失败分支。", "能用 Compose 启动 API 与数据库。"]),
    dict(num="01", slug="http-basic", title="HTTP 请求如何变成 FastAPI 响应", core="URL 与 HTTP 方法定位路径操作函数；类型注解帮助 FastAPI 转换参数并生成文档。",
         steps=[("客户端", "GET /tasks/42?verbose=true\nHeader: Accept: application/json"), ("Uvicorn / ASGI", "监听端口并接收请求\n把 HTTP 转成 ASGI 消息"), ("FastAPI 路由", "匹配 GET + /tasks/{task_id}\n找不到：404"), ("参数与函数", "task_id: int = 42\nverbose: bool = True\n转换失败：422"), ("JSON 响应", "dict / Pydantic 模型\n序列化为 response body\n默认成功：200")],
         exception="路由没匹配与参数校验失败是两类问题：先看 404 还是 422，再检查路径、方法和类型。",
         code=["@app.get('/tasks/{task_id}')", "def get_task(task_id: int, verbose: bool = False):", "    return {'id': task_id, 'verbose': verbose}", "# GET /tasks/abc → 422"],
         details=["路径参数标识资源，例如 /tasks/42。", "查询参数表达筛选、分页和开关，例如 ?page=1。", "函数返回 dict 不等于已经发出 JSON，框架还要序列化。", "OpenAPI 文档来自路由、类型和 response_model 等声明。"],
         checks=["/docs 能看到接口与参数类型。", "合法路径参数被转换为 int。", "非法参数返回可读的 422。", "路径与方法共同决定匹配结果。"]),
    dict(num="02", slug="crud", title="请求体、HTTP 方法与内存 CRUD", core="CRUD 不只是五个装饰器：要先定义资源、字段规则、缺失语义和持久化边界。",
         steps=[("Create｜POST", "读取 JSON 请求体\n创建新资源\n成功通常返回 201"), ("Read｜GET", "查询列表或单条资源\n列表加分页与筛选\n不存在返回 404"), ("Replace｜PUT", "整体替换可写字段\n未提供字段按完整表示处理\n不是局部补丁"), ("Patch｜PATCH", "exclude_unset=True\n只修改本次传入字段\n显式 null 单独决定"), ("Delete｜DELETE", "确认资源存在\n执行删除\n204 不返回响应体")],
         exception="进程重启会清空普通 dict；内存版用于理解 HTTP 与业务，不等于持久化，也不适合多进程共享。",
         code=["changes = payload.model_dump(exclude_unset=True)", "if not changes: raise EmptyUpdateError(...)", "task.update(changes)", "return Response(status_code=204)"],
         details=["请求体通常是 JSON，GET 不使用请求体传主要筛选条件。", "POST /tasks 创建集合成员，PUT/PATCH 操作指定 id。", "PATCH 要区分字段未传与显式传 null。", "列表顺序、默认分页和最大 page_size 应保持稳定。"],
         checks=["创建后可按 id 查询。", "PUT 与 PATCH 的字段语义不同。", "重复删除得到明确的 404 或幂等策略。", "204 响应没有多余 JSON。"]),
    dict(num="03", slug="pydantic", title="Pydantic 请求模型与响应模型的边界", core="请求模型防止坏输入进入业务，响应模型防止内部字段泄露；两者不能用一个类包打天下。",
         steps=[("原始 JSON", "字段名、类型、缺省值\n可能包含多余字段\n可能格式非法"), ("请求模型", "Field 约束与 Enum\nfield/model validator\nextra='forbid'"), ("业务对象", "得到可信 Python 数据\n服务层处理业务规则\n补服务端字段"), ("响应模型", "response_model=TaskDetail\nfrom_attributes 按需开启\n只暴露白名单字段"), ("客户端响应", "字段形状稳定\n时间／枚举可序列化\n错误统一为 422")],
         exception="422 表示请求格式或校验失败；“标题已被占用”这类业务冲突应在业务层返回 409，而不是塞进字段校验。",
         code=["class TaskCreate(BaseModel):", "    title: str = Field(min_length=1, max_length=100)", "    priority: Priority = Priority.medium", "    model_config = ConfigDict(extra='forbid')"],
         details=["Field 管单字段，model_validator 管跨字段关系。", "枚举限制取值集合，序列化时输出其值。", "请求中的密码、internal_note 等不能出现在响应模型。", "Pydantic 校验通过不代表数据库中的资源一定存在。"],
         checks=["缺字段、错类型、额外字段都有测试。", "嵌套模型错误能定位到具体字段。", "响应不包含内部备注和密码哈希。", "业务 404/409 与校验 422 分开。"]),
    dict(num="04", slug="nested-response", title="嵌套模型与统一分页响应", core="把“资源长什么样”和“本次调用结果如何”分开：data 装资源，meta 装分页，code/message 装结果说明。",
         steps=[("资源摘要", "UserSummary / ProjectSummary\n列表只暴露必要字段\n避免层层递归"), ("详情与列表项", "TaskDetail 字段更完整\nTaskListItem 更轻量\n复用稳定基础模型"), ("集合与标签", "list[TagRead]\ndefault_factory=list\n限制最大数量"), ("统一包装", "code + message + data\n列表增加 meta\n错误使用 error 结构"), ("分页元信息", "page / page_size / total\ntotal_pages\nhas_next / has_prev")],
         exception="不要在每个接口随意发明 items、result、rows 等不同包装；统一结构让前端、测试和错误处理都能复用逻辑。",
         code=["{'code': 'OK', 'message': 'success',", " 'data': [TaskListItem, ...],", " 'meta': {'page': 1, 'page_size': 20,", "          'total': 57, 'has_next': True}}"],
         details=["default_factory 为每个实例创建独立列表，避免共享可变默认值。", "摘要模型避免为了显示任务而加载完整用户对象。", "空列表 total=0 时 total_pages=0，规则要固定。", "统一包装不应掩盖正确的 HTTP 状态码。"],
         checks=["标签列表不会产生重复名称。", "分页边界 0 条、尾页、超范围页有定义。", "列表与详情响应模型各自明确。", "成功和错误响应不会混用 data/error。"]),
    dict(num="05", slug="router-layers", title="APIRouter 与四层请求调用链", core="router 管 HTTP，schema 管数据形状，service 管业务规则，repository 管数据访问。",
         steps=[("main / router", "创建 FastAPI app\n注册 /api/v1\n组合 users/tasks 路由"), ("endpoint", "接收路径／查询／请求体\n声明 response_model\n不直接操作数据库"), ("service", "检查资源与业务规则\n组织事务和响应\n抛出业务异常"), ("repository", "list/get/create/update/delete\n当前是内存 dict\n以后换成 SQLAlchemy"), ("response", "Pydantic 输出校验\n统一成功或错误结构\n状态码保持语义")],
         exception="分层不是文件越多越好：如果 endpoint 直接改 dict，或 repository 写权限规则，替换数据库时仍会牵连所有层。",
         code=["@router.post('', response_model=TaskDetailResponse)", "def create_task(payload: TaskCreate):", "    return task_service.create_task(payload)", "# service → repository，不反向依赖"],
         details=["/api/v1 给未来不兼容升级保留空间。", "Pydantic schema 与 ORM model 是两种不同职责。", "service 是可独立测试的业务编排层。", "repository 屏蔽存储细节，但不要过度抽象每个 SQL 查询。"],
         checks=["能从 URL 追踪到具体函数与文件。", "业务规则不依赖 Request/Response 对象。", "替换存储实现不需要改路由路径。", "模块导入方向没有循环。"]),
    dict(num="06", slug="errors", title="业务异常与统一错误处理", core="业务层抛出语义明确的异常，应用边界统一记录并转换响应；不要逐层拼 HTTPException。",
         steps=[("发现问题", "资源不存在 / 状态冲突\n权限不足 / 请求规则失败\n区分可预期与未知异常"), ("业务异常", "NotFoundError\nConflictError\n携带稳定 error code"), ("全局处理器", "捕获已知业务异常\n记录必要上下文\n映射 HTTP 状态码"), ("统一错误响应", "code + message + details\nrequest_id 便于追踪\n不含堆栈/敏感信息"), ("客户端与日志", "客户端按 code 处理\n日志按 request_id 定位\n未知异常不泄露堆栈")],
         exception="HTTP 200 包业务错误会让缓存、监控和客户端重试失真；401、403、404、409、422、500 应保持各自语义。",
         code=["raise NotFoundError('Task not found',", "                     details={'task_id': task_id})", "# handler → 404 + {'code':'TASK_NOT_FOUND', ...}", "# 未捕获异常 → 500，不返回 traceback"],
         details=["异常类型表达类别，错误代码供程序稳定判断。", "message 面向人，details 面向可公开的上下文。", "RequestValidationError 可单独格式化为 422。", "500 要记录服务端堆栈，但响应不能包含密钥和 SQL。"],
         checks=["同一异常在任何 endpoint 结构一致。", "404 与 409 不被统一成 400。", "错误响应包含 request_id。", "未知异常有日志、无敏感泄露。"]),
    dict(num="07", slug="dependencies", title="Depends 依赖注入与覆盖测试", core="把横贯多个接口的“提供什么”抽成依赖；FastAPI 按函数签名构建依赖图并缓存本次请求结果。",
         steps=[("声明依赖", "Annotated[Session, Depends(get_db)]\nAnnotated[User, Depends(get_current_user)]"), ("构建依赖图", "路由依赖 → 子依赖\n同请求默认可复用\nuse_cache 控制缓存"), ("执行与注入", "普通参数由请求解析\nDepends 先执行依赖函数\n返回值注入 endpoint"), ("yield 清理", "yield 前获取资源\nyield 后释放资源\n异常路径也要关闭"), ("测试覆盖", "app.dependency_overrides[original] = fake\n测试结束清空\n不修改生产代码")],
         exception="全局单例保存某个请求的用户或 Session 会串请求；请求级状态必须留在依赖返回值、Request.state 或上下文变量中。",
         code=["DbDep = Annotated[AsyncSession, Depends(get_db)]", "CurrentUser = Annotated[User, Depends(get_current_user)]", "async def endpoint(db: DbDep, user: CurrentUser): ...", "app.dependency_overrides[get_db] = override_get_db"],
         details=["依赖既可返回数据，也可做校验、限流和资源管理。", "Annotated 让类型与 Depends 元数据复用且签名清爽。", "yield 依赖适合 Session、HTTP client 等成对清理。", "覆盖键必须是原函数对象，不是同名字符串。"],
         checks=["依赖执行顺序能用日志验证。", "同一请求不会意外创建多个 Session。", "正常和异常路径都释放资源。", "测试后 override 不泄漏到其他用例。"]),
    dict(num="08", slug="settings", title="配置、环境变量与密钥边界", core="代码只声明配置结构，环境提供具体值；默认值服务开发，生产缺密钥应快速失败。",
         steps=[("配置来源", "代码默认值 ← .env ← 环境变量\n明确优先级\nDocker 由 Compose 注入"), ("Settings 模型", "BaseSettings 类型校验\nenv_file='.env'\nextra='ignore'"), ("缓存实例", "@lru_cache\nget_settings() 复用不可变配置\n测试可清缓存"), ("依赖注入", "Annotated[Settings, Depends(get_settings)]\n应用装配时读取\n业务不直接读 os.environ"), ("不同环境", ".env.example 可提交\n真实 .env 被忽略\n生产密钥单独管理")],
         exception="lru_cache 缓存的是配置对象，不应缓存随请求变化的值；修改环境变量后要清缓存或重启进程。",
         code=["class Settings(BaseSettings):", "    database_url: str", "    jwt_secret_key: SecretStr", "    model_config = SettingsConfigDict(env_file='.env')", "# .env.example 只放占位值，不放真实密钥"],
         details=["pydantic-settings 将字符串环境变量转换成声明类型。", "CORS origins 建议用列表或明确解析，不靠模糊 split。", "SecretStr 减少日志误打印风险，但不是加密存储。", "启动时尽早校验必要配置，避免运行到一半才失败。"],
         checks=["仓库中不存在真实 .env。", "缺 database_url/密钥时启动报错清楚。", "测试能隔离配置并清理缓存。", "日志不输出密码、Token 和连接串密码。"]),
    dict(num="09", slug="middleware-cors", title="中间件、Request ID、耗时与 CORS", core="中间件包围整个 HTTP 调用；Request ID 串联日志，CORS 是浏览器跨源约束，不是身份认证。",
         steps=[("请求进入", "生成或校验 X-Request-ID\nrequest.state 保存 ID\n记录 method/path"), ("中间件链", "CORSMiddleware\nRequestContext\nMiddleware\n注意注册与执行顺序"), ("路由与依赖", "预检 OPTIONS 由 CORS 处理\n业务请求继续路由\n异常处理器仍参与"), ("响应离开", "写 X-Request-ID\n写 X-Process-Time-ms\n记录 status_code 与耗时"), ("浏览器判定", "Origin 与 allow_origins 匹配\nallow_credentials 谨慎开启\n业务仍需鉴权")],
         exception="allow_origins=['*'] 与凭据组合不能随意使用；CORS 允许只代表浏览器愿意发/读，不能代替 API Key、JWT 或权限检查。",
         code=["request_id = request.headers.get('x-request-id') or uuid4().hex", "request.state.request_id = request_id", "response = await call_next(request)", "response.headers['X-Request-ID'] = request_id", "# finally 中记录耗时，异常路径也不能漏"],
         details=["同源要求协议、主机、端口三者一致。", "OPTIONS 预检不是业务 GET，不应要求登录。", "耗时用 perf_counter，不用 UTC 时间差避免时钟跳变。", "请求日志不记录 Authorization、密码和完整请求体。"],
         checks=["成功与异常响应都有 Request ID。", "日志可用同一 ID 串起一次请求。", "预检允许的方法与头与前端一致。", "未允许 Origin 不能读取跨源响应。"]),
    dict(num="10", slug="api-key", title="简单 API Key 认证与 Fail-Closed", core="API Key 是预共享凭据，只适合受控客户端；必须校验配置、限制暴露面，并明确它不知道最终用户身份。",
         steps=[("客户端持有 Key", "X-API-Key: <secret>\n或 Authorization 方案\n不要放 URL query"), ("配置检查", "API_KEY_ENABLED=true\n必须配置非空 API_KEY\n缺失时拒绝而不是放行"), ("安全比较", "secrets.compare_digest\n避免普通时序差异\n限制错误信息"), ("通过或拒绝", "失败：401 + WWW-Authenticate\n成功：注入客户端身份\n可记录 key 的标识而非原值"), ("业务权限", "Key 只代表应用/服务\n最终用户仍需 JWT\n权限和限流继续执行")],
         exception="API Key 泄露后知道它的任何客户端都能冒用；不要把长期 Key 写进前端 JavaScript、Git、日志或教程真实示例。",
         code=["api_key = APIKeyHeader(name='X-API-Key', auto_error=False)", "if not settings.api_key_enabled: return None", "if not settings.api_key or not api_key:", "    raise UnauthorizedError('Valid API key required')", "secrets.compare_digest(api_key, settings.api_key.get_secret_value())"],
         details=["auto_error=False 让项目统一错误结构接管失败响应。", "开放文档 /docs 是否保护应单独决定。", "Key 轮换可用双 Key 过渡期，再撤销旧 Key。", "API Key 与 JWT 解决的问题不同，可组合但不能混淆。"],
         checks=["未配置 Key 时不会意外开放保护接口。", "错误 Key、缺失 Key 都返回统一 401。", "OpenAPI 能显示安全要求。", "仓库与日志中找不到真实 Key。"]),
    dict(num="11", slug="async-httpx", title="async、await 与非阻塞外部调用", core="async 的价值是等待 I/O 时让出事件循环；把同步阻塞调用写进 async 函数并不会自动加速。",
         steps=[("事件循环", "一个线程可调度多个协程\nawait 是显式让出点\n不是所有代码都并行"), ("I/O 等待", "数据库／网络／异步文件\n等待时切换其他任务\n适合高并发 I/O"), ("并发任务", "asyncio.gather 并发独立请求\n共享 AsyncClient\n设置 timeout"), ("阻塞工作", "requests、time.sleep、重 CPU\n会卡住事件循环\n必要时线程池/进程池"), ("响应与取消", "异常按任务收集\n取消要传播\n记录每个外部调用耗时")],
         exception="async def 中直接 time.sleep(5) 或 requests.get(...) 会阻塞所有协程；CPU 密集计算改 async 也不会变快。",
         code=["async with httpx.AsyncClient(timeout=5.0) as client:", "    a, b = await asyncio.gather(", "        client.get(url_a), client.get(url_b))", "# 独立 I/O 才 gather；有先后依赖仍顺序 await"],
         details=["协程对象只有被 await/调度后才执行。", "AsyncClient 复用连接，通常由 lifespan 管理。", "超时、重试、状态码和响应大小都属于边界治理。", "线程池适合部分同步 I/O，CPU 密集优先考虑进程或专门服务。"],
         checks=["能用并发实验解释耗时不是简单相加。", "外部请求全部设置超时。", "一个外部失败时异常处理符合预期。", "压测时其他健康检查不会被同步请求卡住。"]),
    dict(num="12", slug="lifespan-background", title="lifespan 资源生命周期与后台任务", core="lifespan 管应用级长寿命资源，BackgroundTasks 管响应后的短任务；两者都不是可靠分布式任务队列。",
         steps=[("启动阶段", "创建 AsyncClient / Engine\n执行必要连接检查\n失败则应用不启动"), ("应用就绪", "yield 将资源交给 app.state\n开始接收请求\n依赖从 state 获取资源"), ("请求处理", "复用连接池和客户端\n不要每请求重复建重资源\n响应先返回"), ("后台任务", "BackgroundTasks.add_task\n响应发送后执行\n失败只记录，不能改已发响应"), ("关闭阶段", "停止接收新请求\n关闭 client / engine\n等待必要清理完成")],
         exception="进程崩溃、重启或多副本部署时，BackgroundTasks 不提供持久化与至少一次投递；重要任务应写入数据库并交给可靠 Worker。",
         code=["@asynccontextmanager", "async def lifespan(app: FastAPI):", "    app.state.http = httpx.AsyncClient(timeout=5)", "    yield", "    await app.state.http.aclose()"],
         details=["启动与关闭要成对，关闭代码放在 yield 后并考虑异常。", "数据库 Engine 是应用级，Session 是请求/操作级。", "后台任务不持有即将关闭的请求 Session。", "部署滚动重启时还要考虑连接排空与任务持久化。"],
         checks=["启动失败有明确日志且不假装健康。", "关闭后连接池已释放。", "后台任务不访问已关闭 Session。", "重要通知具备持久化和重试方案。"]),
    dict(num="13", slug="uploads", title="UploadFile、Form 与安全文件下载", core="上传不是把 filename 直接拼进磁盘：要验证类型、大小、路径与授权，并流式读写。",
         steps=[("multipart 请求", "UploadFile + File\nForm 接收元数据\npython-multipart 解析"), ("元数据校验", "扩展名只是线索\n检查 content_type 与实际内容\n限制文件大小"), ("流式保存", "服务端生成 UUID 文件名\nwhile chunk = await file.read(...)\n异步/线程写临时文件"), ("原子落盘与记录", "成功后 rename\n数据库保存大小、哈希、owner\n失败清理临时文件"), ("授权下载", "先查记录与权限\nFileResponse 或流式响应\n安全 Content-Disposition")],
         exception="绝不能让 ../../etc/passwd、绝对路径或用户提供的任意下载路径绕过目录边界；下载前也要做资源级权限检查。",
         code=["chunk = await upload.read(1024 * 1024)", "if total + len(chunk) > MAX_BYTES: raise PayloadTooLarge", "safe_name = f'{uuid4().hex}{suffix}'", "await upload.close()  # finally 中执行"],
         details=["UploadFile 适合较大文件，但代码仍要限制累计字节。", "MIME 类型可伪造，高风险场景还需文件签名检测和病毒扫描。", "原文件名仅用于展示，存储名由服务端生成。", "下载响应设置 nosniff，HTML/SVG 等主动内容需谨慎。"],
         checks=["超大文件被拒绝且临时文件清理。", "同名上传不会覆盖他人文件。", "非成员不能猜测 id 下载附件。", "断点异常后数据库与磁盘不留下脏状态。"]),
    dict(num="14", slug="streaming-websocket", title="StreamingResponse、SSE 与 WebSocket 的选择", core="普通响应一次结束，SSE 是服务端到客户端的持续文本流，WebSocket 是双向长连接；协议选择决定生命周期。",
         steps=[("普通 Streaming", "异步生成器逐块 yield\n文件/CSV 不必一次进内存\n客户端断开要停止"), ("SSE 推送", "text/event-stream\nevent/id/data 格式\n每条事件以空行结束"), ("WebSocket 握手", "HTTP Upgrade 建立连接\naccept 前可鉴权\n失败要关闭并说明"), ("双向消息循环", "receive_json / send_json\n校验每条消息\n心跳、超时与并发写入"), ("断开与清理", "WebSocketDisconnect\n取消生产任务\n关闭连接并释放资源")],
         exception="流式响应开始发送后不能再把状态码改成 500；生成器必须有取消与退出条件，长连接也不能无限制积累。",
         code=["yield f'id: {event.id}\\n'", "yield f'data: {json.dumps(payload)}\\n\\n'", "if await request.is_disconnected(): break", "# WebSocket：finally 取消 task 并释放连接"],
         details=["SSE 适合进度和通知，浏览器自动重连可配 Last-Event-ID。", "WebSocket 适合协作、聊天和双向控制。", "反向代理要关闭不必要缓冲并配置读超时。", "每个连接的鉴权、限流、心跳和资源上限不可省略。"],
         checks=["CSV 流不会把全表载入内存。", "客户端断开后生产者停止。", "SSE 事件格式能被 EventSource 解析。", "WebSocket 异常消息不会导致连接泄漏。"]),
    dict(num="15", slug="sqlalchemy-async", title="SQLAlchemy 2.x 异步 Engine 与 Session", core="Engine 管理连接池并长期复用，AsyncSession 管一次业务工作单元；不要在模块全局共享一个 Session。",
         steps=[("DATABASE_URL", "postgresql+asyncpg://...\nSQLite 学习：sqlite+aiosqlite\n密码从环境注入"), ("AsyncEngine", "create_async_engine\npool_size / max_overflow\n应用级单例"), ("sessionmaker", "async_sessionmaker\nexpire_on_commit=False\n统一创建 Session"), ("请求依赖", "async with Session() as session\nyield session\n请求结束关闭"), ("事务与查询", "await session.execute(select(...))\nasync with session.begin()\n提交或异常回滚")],
         exception="在 async 应用中混用 psycopg2 同步驱动和 create_engine 会阻塞事件循环；驱动、Engine、Session 与查询都要保持异步链一致。",
         code=["engine = create_async_engine(settings.database_url)", "SessionFactory = async_sessionmaker(engine, expire_on_commit=False)", "async with SessionFactory() as session:", "    result = await session.execute(select(Task))", "# lifespan 结束：await engine.dispose()"],
         details=["连接池复用数据库连接，不等于所有请求共享事务。", "expire_on_commit=False 避免提交后访问属性再次隐式加载。", "查询构建是同步 Python 操作，真正 I/O 在 await execute。", "事务边界由 service 明确控制，repository 不随处 commit。"],
         checks=["每请求独立 Session 且最终关闭。", "数据库 URL 驱动与异步代码匹配。", "异常时事务回滚，连接仍归还池。", "关闭应用时 Engine 正确 dispose。"]),
    dict(num="16", slug="orm-relationships", title="ORM 模型、外键与关系加载", core="表定义数据库约束，relationship 描述对象导航；两者相关但不相同，加载策略必须避免 N+1。",
         steps=[("实体与主键", "User / Project / Task\nMapped[int] 类型声明\nmapped_column 列定义\n时间戳使用 UTC"), ("外键约束", "Task.project_id → projects.id\nondelete 明确 RESTRICT/CASCADE\n业务规则不能全靠 DB"), ("对象关系", "relationship(...)\nback_populates 成对\nlazy 不依赖隐式异步加载"), ("多对多", "tags — task_tags — tasks\n关联表有联合主键\n唯一约束防重复"), ("显式加载", "selectinload 集合\njoinedload 单个关联\n一次查询需要的关系")],
         exception="AsyncSession 中访问未加载的 lazy relationship 可能触发 MissingGreenlet；在查询时显式加载，或构造专用响应 DTO。",
         code=["stmt = (select(Task)", "        .options(selectinload(Task.tags),", "                 joinedload(Task.owner))", "        .where(Task.id == task_id))", "# schema 读取前，需要的属性已加载"],
         details=["外键保证引用存在，唯一索引保证邮箱/名称等业务约束。", "CASCADE 删除要评估影响，审计业务常倾向软删除或 RESTRICT。", "selectinload 对集合常比大量 joined 行膨胀更稳定。", "Pydantic from_attributes 只解决属性映射，不解决异步懒加载。"],
         checks=["外键、唯一约束和索引符合查询。", "无 N+1 的列表查询。", "删除项目时任务处理策略明确。", "响应序列化不触发隐式数据库 I/O。"]),
    dict(num="17", slug="database-crud", title="数据库 CRUD、事务与分页", core="service 决定业务事务，repository 执行查询与写入；唯一约束、并发冲突和空结果都要转成明确语义。",
         steps=[("接收业务命令", "已校验 TaskCreate\n检查用户与项目\n权限规则在 service"), ("构建查询", "select(Task).where(...)\n动态筛选不拼字符串 SQL\n排序规则稳定"), ("统计与分页", "count 使用同一筛选\noffset=(page-1)*page_size\n限制 page_size"), ("写入事务", "async with session.begin()\nadd / flush / refresh\n一次业务操作统一提交"), ("异常映射", "无记录 → 404\nIntegrityError → 409\n未知 DB 错误 → 500 + 日志")],
         exception="不要在 repository 每次查询后自动 commit；否则跨多次写入的业务无法整体回滚，事务边界也会变得不可预测。",
         code=["async with session.begin():", "    task = Task(**payload.model_dump())", "    session.add(task)", "    await session.flush()  # 获取数据库生成 id", "# 出异常：上下文管理器回滚"],
         details=["flush 把 SQL 发给数据库但事务尚未提交。", "refresh 会再次查询，批量场景应避免不必要往返。", "分页同时追加 id 排序，避免仅按非唯一字段造成翻页漂移。", "IntegrityError 映射后要 rollback，不能继续复用失败事务。"],
         checks=["创建失败不会留下半条数据。", "筛选与 count 条件一致。", "重复邮箱/名称返回 409 而非 500。", "更新与删除检查影响行数。"]),
    dict(num="18", slug="alembic", title="Alembic 迁移与可回滚数据库演进", core="模型是目标结构，migration 是从一个版本到另一个版本的明确步骤；生产不能只靠 create_all。",
         steps=[("初始化", "alembic init alembic\n配置 sqlalchemy.url\nenv.py 导入 Base.metadata"), ("生成版本", "alembic revision --autogenerate -m ...\n逐行审查 diff\n自动检测不是全知"), ("升级数据库", "alembic upgrade head\n在事务中执行可行的变更\n记录当前 revision"), ("验证与回滚", "downgrade 只在设计安全时使用\n destructive 变更先备份\n应用兼容新旧结构"), ("团队协作", "迁移文件进入 Git\n多分支 heads 要合并\nCI 从空库升级验证")],
         exception="改字段名、删列、拆分表通常需要 expand/backfill/contract 多阶段迁移；直接 autogenerate 可能把 rename 当成删旧加新。",
         code=["alembic revision --autogenerate -m 'create core tables'", "alembic upgrade head", "alembic current && alembic history", "# CI：空数据库 → upgrade head → 运行测试"],
         details=["env.py 必须看到所有模型，否则 autogenerate 会漏表。", "数据库 URL 由环境提供，迁移脚本不硬编码密码。", "NOT NULL 新列需考虑已有行默认值与回填。", "回滚代码存在不等于生产数据可无损恢复。"],
         checks=["空库可从 base 升到 head。", "已有数据升级有备份与演练。", "upgrade/downgrade 操作经过人工审查。", "模型 metadata 与迁移结果无意外差异。"]),
    dict(num="19", slug="password-registration", title="密码哈希与用户注册", core="密码只能保存慢哈希；注册接口同时处理格式校验、唯一约束、正常响应与防用户枚举。",
         steps=[("注册输入", "email / username / password\n长度与格式校验\n不直接信任 role"), ("密码哈希", "pwdlib 推荐算法\n每次随机 salt\n只保存 hash，不保存明文"), ("唯一性", "先查可给友好提示\n数据库唯一索引兜底\n并发重复映射 409"), ("创建用户", "is_active=True\nrole=user 默认\n事务内写入并返回公开字段"), ("验证登录密码", "hash.verify(password)\n失败统一“凭据无效”\n必要时 dummy verify")],
         exception="SHA-256(password) 不是安全密码存储；不要自己设计加密、固定 salt 或把 hash 放到响应、日志和异常 details 中。",
         code=["password_hash = password_hashers.recommended().hash(password)", "password_hashers.recommended().verify(password, stored_hash)", "# UserRead：id/email/username/is_active/role", "# 永远没有 password 或 password_hash"],
         details=["慢哈希增加暴力破解成本，并随硬件升级参数。", "先查唯一性提升体验，唯一索引才保证并发正确性。", "注册成功不自动授予管理员角色。", "登录失败不透露“邮箱不存在”还是“密码错误”。"],
         checks=["相同密码两次哈希结果不同。", "正确密码可验证，错误密码失败。", "响应与日志没有明文或哈希。", "并发重复注册最终只有一个用户。"]),
    dict(num="20", slug="jwt-auth", title="JWT 登录、Bearer Token 与当前用户", core="登录验证凭据后签发自包含 Token；每个受保护请求验证签名、过期和 subject，再查询当前用户状态。",
         steps=[("OAuth2 登录", "POST /auth/token\nusername + password 表单\nSwagger Authorize 复用"), ("签发 JWT", "sub=user.id 稳定标识\nexp/iat/iss/aud\nHS256 密钥来自环境"), ("Bearer 请求", "Authorization: Bearer <token>\nOAuth2PasswordBearer 解析\n缺失统一 401"), ("验证声明", "验证签名与过期\n校验 iss/aud/sub\n算法白名单"), ("加载当前用户", "按 sub 查询用户\n不存在/禁用拒绝\n返回 ORM User 给业务")],
         exception="JWT 签名不等于加密，payload 不能放密码和敏感资料；仅解码不验证签名、不过期或接受任意 alg 都是严重漏洞。",
         code=["token = jwt.encode({'sub': str(user.id),", "    'exp': expire, 'iat': now, 'iss': ISS, 'aud': AUD}, key, algorithm='HS256')", "payload = jwt.decode(token, key, algorithms=['HS256'],", "                     issuer=ISS, audience=AUD)", "headers = {'WWW-Authenticate': 'Bearer'}"],
         details=["401 表示未认证或 Token 无效，403 表示已认证但权限不足。", "sub 使用用户 id 比可修改 username 更稳定。", "过期时间用 UTC，服务器时钟需同步。", "无状态 JWT 的撤销需要短过期、刷新轮换或额外 denylist。"],
         checks=["无 Token、错签名、过期 Token 都是 401。", "/users/me 返回当前用户而非任意 id。", "禁用用户即使 Token 未过期也被拒绝。", "Token 不出现在 URL 和访问日志。"]),
    dict(num="21", slug="authorization", title="从当前用户到资源级权限", core="认证只得到身份；每次操作还要根据角色、项目成员和资源归属判断，不能用前端隐藏按钮代替。",
         steps=[("识别主体", "current_user.id / role\n是否 active\n服务内部调用单独身份"), ("定位资源", "task → project → members\n不存在先返回 404\n避免泄露他人资源"), ("动作策略", "viewer 可读\nmember 可建任务/评论\nowner/admin 管成员与删除"), ("统一依赖或服务", "require_project_role(...)\n在 service 事务内重查\n不能只在列表页检查"), ("安全响应", "无身份 401\n无权限 403\n记录主体、资源、动作与结果")],
         exception="仅检查 task.owner_id 会漏掉项目管理员；仅检查 URL 中 project_id 又可能错判 task 实际所属项目，必须以数据库资源关系为准。",
         code=["if current_user.role == 'admin': return project", "membership = await repo.get_membership(project.id, user.id)", "if membership is None or role_rank[membership.role] < required:", "    raise ForbiddenError('Insufficient project permission')"],
         details=["权限矩阵按“角色 × 动作”定义，避免散落 if。", "对象不存在与无权访问的响应策略要一致并防枚举。", "列表查询也必须按可见项目过滤。", "审计日志不记录 Token 和敏感正文。"],
         checks=["非成员读、写、删均有负向测试。", "项目 owner 与任务 owner 权限不混淆。", "管理员覆盖规则明确且最小化。", "直接请求隐藏接口仍会被拒绝。"]),
    dict(num="22", slug="pytest-api", title="Pytest 与 TestClient API 测试", core="测试要证明 HTTP 合约：状态码、响应结构、数据库副作用和错误分支，而不是只断言 200。",
         steps=[("安排 Arrange", "隔离测试应用与数据库\n创建用户/项目夹具\n准备合法与非法输入"), ("执行 Act", "client.post/get/patch\n带 Bearer Token\n一次测试聚焦一个行为"), ("断言 Assert", "status_code / code / data\n字段值与敏感字段缺失\n数据库确实改变"), ("参数化", "pytest.mark.parametrize\n多种非法字段共享测试\n错误路径同样覆盖"), ("隔离与报告", "每用例独立应用/数据库\n失败输出可定位\nCI 可重复执行")],
         exception="测试之间共享全局 users dict 或真实开发数据库会产生顺序依赖；一个测试创建的数据不能被另一个测试默默当成前提。",
         code=["response = client.post('/api/v1/auth/token', data=login)", "assert response.status_code == 200", "token = response.json()['access_token']", "response = client.get('/api/v1/users/me',", "                     headers={'Authorization': f'Bearer {token}'})"],
         details=["TestClient 通过 ASGI 调用应用，不必先启动真实端口。", "fixture 负责重复准备，不把全部逻辑塞进 helper 后失去可读性。", "201、204、401、403、404、409、422 都要有代表用例。", "测试响应不应只比较完整 JSON 而忽略关键副作用。"],
         checks=["创建后能查到，删除后查不到。", "非法输入有参数化测试。", "响应不含 password_hash。", "随机顺序执行也能通过。"]),
    dict(num="23", slug="test-database", title="测试数据库、事务夹具与隔离", core="本项目每个测试使用独立临时文件数据库、应用实例和上传目录；事务夹具是另一种可选方案，不能混用半套。",
         steps=[("独立测试库", "SQLite 临时文件\nPostgreSQL 做集成复核\n绝不指向开发/生产库"), ("创建结构", "auto_create_tables=True\nlifespan 为每用例建表\n真实迁移另做 CI 测试"), ("隔离边界", "tmp_path / test.db\n每用例新 app + Engine\n不共享 Session/users"), ("真实依赖链", "保留 get_db/鉴权/路由\n应用与断言看到同库\n不覆盖事务"), ("清理与并发", "TestClient 退出关 Engine\ntmp_path 自动清理\n异步用例显式标记")],
         exception="独立内存 SQLite 连接可能互不可见；本项目用 tmp_path 文件库。若改成事务夹具，必须共享连接/事务，不能只覆盖 get_db 的一半。",
         code=["app = create_app(make_settings(tmp_path))", "with TestClient(app) as client:", "    response = client.get('/health/ready')", "# tmp_path/test.db + uploads；退出后 dispose"],
         details=["临时文件库让连接池内不同连接看到同一数据库。", "create_app 每用例建立独立 Engine，不需要覆盖 get_db。", "tmp_path 同时隔离上传目录，测试结束自动清理。", "SAVEPOINT 事务夹具适合大型套件，但应作为另一套完整策略实现。"],
         checks=["单测通过且连跑也通过。", "测试结束后开发数据不变。", "测试 DB 能验证唯一约束和外键。", "CI 另有从迁移建库的集成测试。"]),
    dict(num="24", slug="overrides-mocks", title="依赖覆盖、Mock 与外部服务测试", core="覆盖应用拥有的依赖接口，Mock 外部边界；不要把所有内部函数都 mock 到只剩假代码。",
         steps=[("选测试层级", "纯 service 单测\nAPI + 测试 DB 集成\n真实外部服务少量契约测试"), ("依赖覆盖", "替换 get_db/get_current_user\n使用原函数作为键\n验证安全依赖仍生效"), ("Mock 外部 HTTP", "httpx.MockTransport 或 respx\n模拟 200/timeout/500\n断言 URL、头和超时"), ("故障与映射", "超时/非法JSON/非对象\n映射为 UpstreamError\n有界重试需另行显式测试"), ("清理与防伪", "恢复 overrides 和 patch\n检查调用参数\n保留真实路由与序列化")],
         exception="如果 mock 直接返回测试期望的最终响应，路由、事务、序列化和权限都可能没被执行；测试通过也不能证明链路正确。",
         code=["transport = httpx.MockTransport(handler)", "app.state.http = httpx.AsyncClient(transport=transport)", "with pytest.raises(UpstreamError):", "    await service.load_external(...)", "assert request.headers['Authorization'] != 'logged-secret'"],
         details=["MockTransport 与 AsyncClient 接口一致，适合精确模拟外部响应。", "认证 override 适合授权分支测试，但登录本身必须有真实测试。", "断言外部请求内容，防止参数拼接和敏感头错误。", "少量端到端测试覆盖 mock 与真实实现的协议偏差。"],
         checks=["外部 500、超时、非法 JSON 都有用例。", "测试过程没有真实网络副作用。", "依赖覆盖在用例后恢复。", "至少一条真实鉴权到数据库的集成链。"]),
    dict(num="25", slug="quality-ci", title="Ruff、测试与 GitHub Actions 门禁", core="把本地能复现的检查变成每次提交自动执行的门禁；CI 必须真正运行新测试，而不只是显示绿色。",
         steps=[("格式与静态检查", "Ruff check 查错误与风格\nRuff format 统一格式\n配置目标 Python 版本"), ("类型与测试", "Pytest 运行单元/集成\n关键模块可补 mypy\n覆盖率用于发现空白"), ("安全与秘密", "检查依赖漏洞\nGit 忽略 .env\nsecret scanning 防误提交"), ("GitHub Actions", "push / pull_request 触发\n缓存依赖\n固定 Python 与命令"), ("失败即阻断", "任何一步失败不合并\n上传必要报告\n变更测试后核对确实被执行")],
         exception="CI 的绿勾只在当前提交、当前命令和当前测试范围有效；把测试文件放错目录或脚本未包含它们，都会形成虚假安全感。",
         code=["python -m ruff check app tests", "python -m ruff format --check app tests", "python -m pytest -q", "# CI 再执行：alembic upgrade head（空测试库）", "# 不使用 continue-on-error 掩盖门禁"],
         details=["格式化和 lint 是两件事，一个改排版，一个发现潜在问题。", "覆盖率不是质量本身，关键分支和边界必须有断言。", "CI 密钥只放加密 Secrets，不写进 YAML。", "并发数据库测试需独立 schema/数据库，避免相互删除。"],
         checks=["本地与 CI 使用相同命令。", "新测试在 CI 日志中可见并执行。", "故意失败的测试能阻断流程。", "构建产物和密钥不进入提交。"]),
    dict(num="26", slug="docker-compose", title="Dockerfile、Compose 与生产启动链", core="镜像包含不可变应用与依赖，Compose 编排 API/PostgreSQL；迁移、健康检查和关闭顺序都必须明确。",
         steps=[("构建镜像", "固定基础镜像版本\n先复制依赖再复制代码\n非 root 用户运行"), ("启动 PostgreSQL", "命名卷保存数据\n健康检查 pg_isready\n密码来自环境"), ("迁移与启动 API", "等待数据库可用\nalembic upgrade head\nuvicorn 监听 0.0.0.0"), ("健康与依赖", "/health/live 只看进程\n/health/ready 检查 DB\nservice_healthy 条件"), ("运行与排错", "docker compose up --build\nlogs/ps/exec 定位\ndown 不随意 -v 删数据")],
         exception="容器启动不代表数据库已就绪；healthcheck 也不能代替迁移。docker compose down -v 会删除命名卷，不能当普通重启命令。",
         code=["docker compose up --build -d", "docker compose ps", "docker compose logs -f api", "docker compose exec api alembic current", "curl -f http://127.0.0.1:8000/health/ready"],
         details=[".dockerignore 排除 .venv、.env、测试缓存和本地数据。", "多阶段/缓存挂载可优化构建，但锁定依赖优先。", "生产不使用 --reload， worker 数结合连接池和 CPU 规划。", "密钥由部署平台 secret 管理，镜像层里不放 .env。"],
         checks=["全新环境仅凭示例配置可启动。", "数据库重启后命名卷数据仍在。", "ready 在 DB 不可用时失败。", "容器以非 root 运行且能优雅关闭。"]),
    dict(num="27", slug="capstone", title="TaskHub 综合项目验收与后续演进", core="最终验收沿真实用户旅程检查完整链路，再按负载与团队需求选择 Redis、SSE、审计和可观测性。",
         steps=[("用户与项目", "注册 → 登录 → /users/me\n创建项目与成员\n唯一约束与角色"), ("任务协作", "创建/筛选/更新任务\n评论、标签、附件\n权限与事务"), ("可靠性与安全", "统一错误与 Request ID\n密码/JWT/CORS/API Key\n敏感信息不泄露\n限流与 SSRF 列演进"), ("测试与交付", "单元 + 集成 + 负向测试\nAlembic 空库升级\nDocker Compose 健康"), ("按需演进", "Redis 缓存/限流\nSSE 实时通知\nOpenTelemetry / GitHub Actions")],
         exception="不要为了“技术完整”一次加入所有组件；缓存、消息队列和微服务都要由明确问题驱动，并保持现有 API 合约可测试。",
         code=["注册并登录 → 创建项目 → 添加成员", "→ 创建任务/标签/评论/附件 → 修改状态", "→ 非成员访问返回 403 → 日志可按 request_id 追踪", "→ pytest 全绿 → 空库迁移 → Compose 启动", "→ 备份恢复与关闭流程演练"],
         details=["功能验收包含成功、失败、边界和权限，不只演示 happy path。", "性能优化先用指标和查询计划定位，再决定索引或缓存。", "软删除、审计日志和分页要在数据模型与 API 中统一。", "最终 README 让新成员能从克隆走到测试和启动。"],
         checks=["核心用户旅程端到端通过。", "权限矩阵每条有负向测试。", "数据库迁移与容器启动可复现。", "后续增强有指标或业务需求依据。"]),
]


def units(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WFA" else 1 for ch in text)


def wrap(text: str, limit: int) -> list[str]:
    """中文按字换行；长英文标识不逐字拆开，交给渲染层局部缩小。"""
    lines: list[str] = []
    token_pattern = re.compile(r"[A-Za-z0-9_./:@+\-#=<>\[\]{}()]+|[ \t]+|.", re.DOTALL)
    for paragraph in text.split("\n"):
        current = ""
        for token in token_pattern.findall(paragraph):
            if token.isspace():
                if not current:
                    continue
                token = " "
            if units(token) > limit:
                if current:
                    lines.append(current.rstrip())
                current = token.lstrip()
            elif units(current + token) > limit and current:
                lines.append(current.rstrip())
                current = token.lstrip()
            else:
                current += token
        if current:
            lines.append(current.rstrip())
    return lines


def fitted_size(value: str, limit: int, size: int, minimum: int = 13) -> int:
    """仅对超宽行局部缩字，避免截断、越界或破坏英文标识。"""
    width = units(value)
    if width <= limit:
        return size
    return max(minimum, int(size * limit / width))


def text(x: int, y: int, value: str, size: int = 24, color: str = "#172033", weight: int = 400,
         family: str = FONT, anchor: str = "start") -> str:
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>')


def multiline(x: int, y: int, value: str, limit: int, size: int = 22, color: str = "#45536b",
              line_height: int = 31, weight: int = 400, family: str = FONT, bullet: bool = False) -> tuple[str, int]:
    out: list[str] = []
    lines = wrap(value, limit - (3 if bullet else 0))
    for index, line in enumerate(lines):
        prefix = "• " if bullet and index == 0 else ("  " if bullet else "")
        out.append(text(x, y + index * line_height, prefix + line, fitted_size(prefix + line, limit, size), color, weight, family))
    return "".join(out), len(lines) * line_height


def box(x: int, y: int, w: int, h: int, fill: str = "#ffffff", stroke: str = "#d5dfec", radius: int = 20,
        extra: str = "") -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" {extra}/>'


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = "#3a6f85", dashed: bool = False) -> str:
    dash = ' stroke-dasharray="8 7"' if dashed else ""
    return (f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="2.5" '
            f'marker-end="url(#arrow-{color[1:]})"{dash}/>' )


def render_svg(item: dict) -> str:
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">第 {item['num']} 讲：{escape(item['title'])}</title>
<desc id="desc">{escape(item['core'])}</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4f9fc"/><stop offset="0.55" stop-color="#eef5f8"/><stop offset="1" stop-color="#f8f5ef"/></linearGradient>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#7ea1b2" stroke-opacity="0.10" stroke-width="1"/></pattern>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#18354a" flood-opacity="0.09"/></filter>
''']
    for color in ["3a6f85", "c46a32"]:
        parts.append(f'<marker id="arrow-{color}" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#{color}"/></marker>')
    parts.append('</defs>')
    parts.append('<rect width="1600" height="1000" fill="url(#bg)"/><rect width="1600" height="1000" fill="url(#grid)"/>')
    parts.append('<path d="M0 0H1600V10H0Z" fill="#28758a"/>')
    parts.append(text(72, 68, f"FASTAPI · TASKHub  ·  第 {item['num']} 讲", 20, "#28758a", 700, MONO))
    parts.append(text(72, 119, item['title'], 42, "#102a43", 700))
    parts.append(text(72, 153, item['core'], 22, "#45536b"))

    x_positions = [72, 370, 668, 966, 1264]
    for i, ((title_value, body), x) in enumerate(zip(item['steps'], x_positions)):
        fill = "#ffffff" if i % 2 == 0 else "#f7fbfc"
        parts.append(box(x, 184, 264, 246, fill, "#c8d9e2", 18, 'filter="url(#shadow)"'))
        parts.append(f'<rect x="{x}" y="184" width="264" height="7" rx="3.5" fill="{["#28758a", "#3a8f85", "#5b7fa6", "#28758a", "#3a8f85"][i]}"/>')
        title_lines = wrap(title_value, 18)
        ty = 225
        for line in title_lines:
            parts.append(text(x + 18, ty, line, fitted_size(line, 18, 23, 15), "#173b52", 700))
            ty += 31
        ty += 5
        body_svg, _ = multiline(x + 18, ty, body, 21, 20, "#45536b", 31)
        parts.append(body_svg)
        if i < 4:
            parts.append(arrow(x + 267, 307, x_positions[i + 1] - 8, 307))

    parts.append(box(72, 448, 1456, 52, "#fff5eb", "#e9b78e", 12))
    parts.append(text(91, 477, "异常／边界", 18, "#a55025", 700))
    parts.append(text(208, 477, item['exception'], fitted_size(item['exception'], 140, 18, 14), "#81462b"))

    parts.append(box(72, 518, 1456, 145, "#102a43", "#102a43", 18))
    parts.append(text(94, 546, "代码 / 协议示例", 18, "#8ed5d1", 700))
    y = 574
    for line in item['code'][:5]:
        parts.append(text(94, y, line, 17, "#edf7f6", 400, MONO))
        y += 19

    parts.append(box(72, 680, 714, 275, "#ffffff", "#c8d9e2", 18))
    parts.append(box(814, 680, 714, 275, "#f9fcfb", "#c8d9e2", 18))
    parts.append(text(96, 720, "关键拆解", 26, "#173b52", 700))
    parts.append(text(838, 720, "常见误区与验收", 26, "#173b52", 700))
    y = 754
    for detail in item['details']:
        svg, used = multiline(96, y, detail, 64, 18, "#45536b", 23, bullet=True)
        parts.append(svg)
        y += max(used, 23) + 4
    y = 754
    for check in item['checks']:
        svg, used = multiline(838, y, check, 64, 18, "#36594f", 23, bullet=True)
        parts.append(svg)
        y += max(used, 23) + 4
    parts.append(text(1528, 978, f"{item['num']} / 27", 16, "#688295", 400, MONO, "end"))
    parts.append('</svg>')
    return "".join(parts)


def render_png(item: dict, destination: Path) -> None:
    """用 Pillow 重绘同一版式，避免依赖 Cairo 等系统动态库。"""
    from PIL import Image, ImageDraw, ImageFont

    def first_existing(candidates: list[str]) -> str:
        for candidate in candidates:
            if Path(candidate).is_file():
                return candidate
        raise FileNotFoundError("未找到中文制图字体，请安装 Noto Sans CJK 或修改字体候选路径。")

    regular_path = first_existing(PNG_FONT_CANDIDATES)
    bold_path = first_existing(PNG_BOLD_FONT_CANDIDATES)
    mono_path = first_existing(PNG_MONO_FONT_CANDIDATES)
    font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def font(size: int, weight: int = 400, mono: bool = False) -> ImageFont.FreeTypeFont:
        path = mono_path if mono else (bold_path if weight >= 600 else regular_path)
        key = (path, size)
        if key not in font_cache:
            font_cache[key] = ImageFont.truetype(path, size)
        return font_cache[key]

    # 连续浅色渐变与细网格；所有正文区域另用不透明表面承托。
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f4f9fc")
    pixels = image.load()
    start, end = (244, 249, 252), (248, 245, 239)
    for y in range(HEIGHT):
        for x in range(0, WIDTH, 4):
            ratio = (x / WIDTH + y / HEIGHT) / 2
            color = tuple(round(start[i] * (1 - ratio) + end[i] * ratio) for i in range(3))
            for dx in range(4):
                if x + dx < WIDTH:
                    pixels[x + dx, y] = color
    draw = ImageDraw.Draw(image)
    for x in range(0, WIDTH, 32):
        draw.line((x, 0, x, HEIGHT), fill="#e5edef", width=1)
    for y in range(0, HEIGHT, 32):
        draw.line((0, y, WIDTH, y), fill="#e5edef", width=1)
    draw.rectangle((0, 0, WIDTH, 10), fill="#28758a")

    def p_text(x: int, y: int, value: str, size: int = 24, color: str = "#172033",
               weight: int = 400, mono: bool = False, anchor: str = "ls") -> None:
        # Menlo 不覆盖中文；含非 ASCII 的代码行使用已验证的中文字体。
        use_mono = mono and all(ord(ch) < 128 for ch in value)
        draw.text((x, y), value, font=font(size, weight, use_mono), fill=color, anchor=anchor)

    def p_multiline(x: int, y: int, value: str, limit: int, size: int = 22,
                    color: str = "#45536b", line_height: int = 31, weight: int = 400,
                    bullet: bool = False) -> int:
        lines = wrap(value, limit - (3 if bullet else 0))
        for index, line in enumerate(lines):
            prefix = "• " if bullet and index == 0 else ("  " if bullet else "")
            p_text(x, y + index * line_height, prefix + line, fitted_size(prefix + line, limit, size), color, weight)
        return len(lines) * line_height

    def p_box(x: int, y: int, w: int, h: int, fill: str = "#ffffff",
              stroke: str = "#d5dfec", radius: int = 20) -> None:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=stroke, width=2)

    def p_arrow(x1: int, y1: int, x2: int, y2: int) -> None:
        draw.line((x1, y1, x2 - 8, y2), fill="#3a6f85", width=3)
        draw.polygon(((x2, y2), (x2 - 11, y2 - 7), (x2 - 11, y2 + 7)), fill="#3a6f85")

    p_text(72, 68, f"FASTAPI · TASKHUB · 第 {item['num']} 讲", 20, "#28758a", 700)
    p_text(72, 119, item['title'], 42, "#102a43", 700)
    core_lines = wrap(item['core'], 132)
    if len(core_lines) != 1:
        raise ValueError(f"{item['num']} 核心句过长，请拆到正文或缩短：{item['core']}")
    p_text(72, 153, item['core'], 21, "#45536b")

    x_positions = [72, 370, 668, 966, 1264]
    accents = ["#28758a", "#3a8f85", "#5b7fa6", "#28758a", "#3a8f85"]
    for i, ((title_value, body), x) in enumerate(zip(item['steps'], x_positions)):
        p_box(x, 184, 264, 246, "#ffffff" if i % 2 == 0 else "#f7fbfc", "#c8d9e2", 18)
        draw.rounded_rectangle((x, 184, x + 264, 191), radius=3, fill=accents[i])
        ty = 225
        for line in wrap(title_value, 18):
            p_text(x + 18, ty, line, fitted_size(line, 18, 23, 15), "#173b52", 700)
            ty += 31
        p_multiline(x + 18, ty + 5, body, 21, 20, "#45536b", 31)
        if i < 4:
            p_arrow(x + 267, 307, x_positions[i + 1] - 8, 307)

    p_box(72, 448, 1456, 52, "#fff5eb", "#e9b78e", 12)
    p_text(91, 477, "异常／边界", 18, "#a55025", 700)
    exception_lines = wrap(item['exception'], 140)
    if len(exception_lines) > 1:
        raise ValueError(f"{item['num']} 异常句过长，请缩短或改到关键拆解：{item['exception']}")
    p_text(208, 477, item['exception'], fitted_size(item['exception'], 140, 18, 14), "#81462b")

    p_box(72, 518, 1456, 145, "#102a43", "#102a43", 18)
    p_text(94, 546, "代码 / 协议示例", 18, "#8ed5d1", 700)
    y = 574
    for line in item['code'][:5]:
        p_text(94, y, line, 17, "#edf7f6", mono=True)
        y += 19

    p_box(72, 680, 714, 275, "#ffffff", "#c8d9e2", 18)
    p_box(814, 680, 714, 275, "#f9fcfb", "#c8d9e2", 18)
    p_text(96, 720, "关键拆解", 26, "#173b52", 700)
    p_text(838, 720, "常见误区与验收", 26, "#173b52", 700)
    y = 754
    for detail in item['details']:
        used = p_multiline(96, y, detail, 64, 18, "#45536b", 23, bullet=True)
        y += max(used, 23) + 4
    if y > 956:
        raise ValueError(f"{item['num']} 关键拆解超出画布：{y}")
    y = 754
    for check in item['checks']:
        used = p_multiline(838, y, check, 64, 18, "#36594f", 23, bullet=True)
        y += max(used, 23) + 4
    if y > 956:
        raise ValueError(f"{item['num']} 验收清单超出画布：{y}")
    p_text(1528, 978, f"{item['num']} / 27", 16, "#688295", mono=True, anchor="rs")
    image.save(destination, format="PNG", optimize=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for item in DIAGRAMS:
        stem = f"{item['num']}-{item['slug']}"
        svg = render_svg(item)
        (OUT / f"{stem}.svg").write_text(svg, encoding="utf-8")
        render_png(item, OUT / f"{stem}.png")
    print(f"Generated {len(DIAGRAMS)} SVG + PNG diagrams in {OUT}")


if __name__ == "__main__":
    main()
