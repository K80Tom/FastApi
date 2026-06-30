# 第 01 讲：HTTP API 基础与 FastAPI 入门

学习路线位置：第 1 周  
学习主题：HTTP API 基础与 FastAPI 入门  
今日目标：理解一个 Python 函数如何变成 HTTP 接口，并完成最小 FastAPI 项目。

---

## 1. 今天要掌握什么

今天先不追求完整 CRUD，只掌握 FastAPI 最核心的运行模型：

```text
HTTP 请求 -> FastAPI 路由匹配 -> Python 函数执行 -> JSON 响应
```

也就是说，FastAPI 做的事情可以先简单理解为：

```text
URL + HTTP 方法 -> Python 函数
```

比如：

```python
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

含义是：

```text
当客户端发送 GET /health 请求时，
FastAPI 会调用 health_check 函数，
函数返回的 Python dict 会被自动转换成 JSON。
```

---

## 2. FastAPI 最小项目

建议本阶段代码目录：

```text
code/
  fastapi-framework-lab/
    week01_basic_api/
      main.py
```

`main.py` 示例：

```python
from fastapi import FastAPI

app = FastAPI(title="TaskHub API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return [
        {
            "id": 1,
            "title": "学习 FastAPI",
            "status": "todo",
        }
    ]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return {
        "id": task_id,
        "title": "学习 FastAPI",
        "status": "todo",
    }
```

---

## 3. 启动命令

安装依赖：

```powershell
pip install fastapi uvicorn
```

进入代码目录后启动：

```powershell
uvicorn main:app --reload
```

命令含义：

```text
uvicorn：ASGI 服务器，用来运行 FastAPI 应用
main：main.py 文件
app：main.py 里的 FastAPI 应用对象
--reload：代码变化后自动重启，适合开发环境
```

启动后访问：

```text
http://127.0.0.1:8000/docs
```

也可以访问：

```text
http://127.0.0.1:8000/redoc
```

---

## 4. FastAPI 应用对象

```python
app = FastAPI(title="TaskHub API")
```

`app` 是整个 FastAPI 服务的入口。  
所有接口都会通过装饰器注册到 `app` 上。

例如：

```python
@app.get("/health")
```

表示注册一个 GET 接口。

---

## 5. 路径操作函数

FastAPI 中，一个接口对应一个 Python 函数，这个函数通常叫路径操作函数。

```python
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

这个接口可以拆成三部分理解：

```text
@app.get      -> HTTP 方法是 GET
"/health"    -> 请求路径是 /health
health_check -> 真正被执行的 Python 函数
```

返回值：

```python
return {"status": "ok"}
```

FastAPI 会自动把它转换成 JSON：

```json
{
  "status": "ok"
}
```

---

## 6. 路径参数

路径参数是 URL 路径的一部分。

示例：

```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return {"id": task_id}
```

访问：

```text
GET /tasks/1
GET /tasks/2
GET /tasks/100
```

这里的 `1`、`2`、`100` 都会被 FastAPI 提取出来，传给函数参数 `task_id`。

因为函数参数写了类型：

```python
task_id: int
```

所以 FastAPI 会自动把路径里的字符串转换成整数。

如果访问：

```text
GET /tasks/abc
```

FastAPI 会返回 422 校验错误，因为 `abc` 不能转换成整数。

---

## 7. 查询参数

查询参数在 URL 的 `?` 后面。

示例：

```text
GET /tasks?page=1&page_size=20
```

对应代码：

```python
@app.get("/tasks")
def list_tasks(page: int = 1, page_size: int = 20):
    return {
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": 1,
                "title": "学习 FastAPI",
                "status": "todo",
            }
        ],
    }
```

这里：

```text
page=1
page_size=20
```

会自动传给函数参数：

```python
page: int = 1
page_size: int = 20
```

如果请求中没有传查询参数，就使用默认值。

---

## 8. 路径参数和查询参数的区别

路径参数表示资源身份，通常是必须的。

```text
/tasks/1
```

含义：

```text
我要查看 id 为 1 的任务
```

查询参数表示筛选、分页、排序等附加条件，通常是可选的。

```text
/tasks?page=1&page_size=20&status=todo
```

含义：

```text
我要查看任务列表，第 1 页，每页 20 条，只看 todo 状态
```

简单判断：

```text
标识某个具体资源 -> 路径参数
筛选、分页、排序、搜索 -> 查询参数
```

---

## 9. 今天涉及的接口

### 健康检查接口

```text
GET /health
```

用途：

```text
确认服务是否正常运行。
```

示例响应：

```json
{
  "status": "ok"
}
```

### 任务列表接口

```text
GET /tasks
```

用途：

```text
获取任务列表。
```

### 任务详情接口

```text
GET /tasks/{task_id}
```

用途：

```text
根据任务 id 获取任务详情。
```

---

## 10. 今天先记住的 HTTP 方法

目前先记住最常见的 5 个：

```text
GET：查询资源
POST：创建资源
PUT：整体更新资源
PATCH：局部更新资源
DELETE：删除资源
```

今天只需要真正写 `GET`。  
后面实现完整任务 CRUD 时，会继续写 `POST`、`PUT`、`PATCH`、`DELETE`。

---

## 11. 今天先记住的状态码

```text
200 OK：请求成功
201 Created：资源创建成功
204 No Content：请求成功，但没有响应体
400 Bad Request：请求格式或业务参数错误
404 Not Found：资源不存在
422 Validation Error：请求参数校验失败
500 Internal Server Error：服务端内部错误
```

今天最容易遇到的是：

```text
200：接口正常返回
422：参数类型不对
```

例如访问：

```text
/tasks/abc
```

而代码要求：

```python
task_id: int
```

就会触发 422。

---

## 12. 今日练习

完成下面 3 个接口：

```text
GET /health
GET /tasks
GET /tasks/{task_id}
```

然后打开：

```text
http://127.0.0.1:8000/docs
```

在 Swagger UI 里分别测试这 3 个接口。

---

## 13. 自测问题

学完今天内容后，尝试自己回答：

1. `app = FastAPI()` 的作用是什么？
2. `@app.get("/health")` 的作用是什么？
3. 为什么函数返回 dict 后，浏览器看到的是 JSON？
4. `/tasks/{task_id}` 里的 `task_id` 是什么参数？
5. `/tasks?page=1&page_size=20` 里的 `page` 是什么参数？
6. 路径参数和查询参数有什么区别？
7. `uvicorn main:app --reload` 中的 `main:app` 分别代表什么？
8. 为什么访问 `/tasks/abc` 可能会返回 422？

---

## 14. 今日验收标准

今天完成后，你应该能做到：

- 能启动一个最小 FastAPI 服务。
- 能打开 `/docs` 查看自动接口文档。
- 能写出 `GET /health`。
- 能写出 `GET /tasks`。
- 能写出 `GET /tasks/{task_id}`。
- 能解释路径参数。
- 能解释查询参数。
- 能理解 FastAPI 的基本运行模型。

---

## 15. 明天学习方向

下一讲建议继续第 1 周内容，开始实现 TaskHub 内存版 CRUD：

```text
POST   /tasks
PUT    /tasks/{task_id}
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
```

重点理解：

```text
请求体是什么
POST / PUT / PATCH / DELETE 有什么区别
如何用内存字典临时保存任务数据
```
