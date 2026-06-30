# 07 Dockerfile 编写与镜像构建

## 1. 这一节要解决什么问题

帮你学会写 Dockerfile，把自己的应用打包成 Docker 镜像。这是 Docker 最核心的技能之一：把"我的应用需要什么环境"用代码描述出来，让任何人都能一键重现。

## 2. 基础概念解释

### Dockerfile

通俗解释：Dockerfile 是一个文本文件，里面写了构建镜像的"菜谱"，一步一步告诉 Docker 怎么准备运行环境，把什么代码放进去，最后怎么启动应用。

技术解释：Dockerfile 是一组构建指令，Docker 按顺序执行每条指令，每条指令产生一个新的镜像层，所有层叠加就是最终镜像。

例子：就像你告诉新同事"先装 Python，再装这些依赖，再把代码放进来，然后这样启动"——Dockerfile 就是把这些步骤写成代码。

### docker build

通俗解释：`docker build` 是"按照 Dockerfile 里的菜谱，做出一个镜像"的命令。

技术解释：`docker build` 读取 Dockerfile，逐条执行指令，每条指令提交一个新层，最终生成带有指定名称和标签的镜像。构建上下文（`.`）里的文件可以被 COPY/ADD 指令使用。

## 3. 为什么要学这个

没有 Dockerfile，你的应用就无法被打包成镜像，无法在其他机器上复现环境，无法进入 CI/CD 流程。Dockerfile 是容器化的入口。

## 4. 关键知识点

### 4.1 Dockerfile 所有常用指令

#### FROM —— 指定基础镜像（必须是第一条指令）

```dockerfile
FROM python:3.11-slim
FROM node:20-alpine
FROM ubuntu:22.04
FROM scratch        # 空白镜像，用于构建最小化镜像（比如 Go 编译后的二进制）
```

选择基础镜像的原则：
- **功能够用**：官方镜像已经帮你装好了运行时，不需要从 ubuntu 开始手动装 Python
- **体积小**：优先用 `-slim`（去掉了很多文档和可选工具）或 `-alpine`（基于 Alpine Linux，最小）
- **版本固定**：用 `python:3.11-slim` 而不是 `python:slim`，避免镜像悄悄升级

#### WORKDIR —— 设置工作目录

```dockerfile
WORKDIR /app
```

- 后续所有 RUN/COPY/ADD/CMD/ENTRYPOINT 指令的相对路径都基于这个目录
- 如果目录不存在会自动创建
- 等价于 `RUN mkdir -p /app && cd /app`，但更清晰

#### COPY —— 把文件从构建上下文复制进镜像

```dockerfile
# 复制单个文件
COPY requirements.txt .

# 复制整个目录（注意：是把目录的内容复制进去，不是目录本身）
COPY src/ ./src/

# 复制当前目录所有文件（常用，但要配合 .dockerignore）
COPY . .
```

#### ADD —— 类似 COPY，但有额外功能

```dockerfile
# ADD 可以自动解压 tar 文件
ADD app.tar.gz /app/

# ADD 可以从 URL 下载（但不推荐，不能缓存，用 RUN curl 代替）
ADD https://example.com/file.tar.gz /tmp/
```

注意事项：大多数情况用 COPY，不用 ADD。ADD 的自动解压功能偶尔有用，其他场景用 COPY 更明确。

#### RUN —— 在镜像构建时执行命令

```dockerfile
# Shell 形式（默认 /bin/sh -c）
RUN apt-get update && apt-get install -y curl

# Exec 形式（不经过 shell，直接执行）
RUN ["apt-get", "install", "-y", "curl"]

# 实际项目中的标准写法（安装完清理缓存，减小镜像体积）
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl wget \
    && rm -rf /var/lib/apt/lists/*
```

注意事项：多条相关命令用 `&&` 连接在一个 RUN 里，避免每条命令都产生一层（虽然功能一样，但每层都有元数据开销，而且中间层的临时文件无法被删掉）。

#### ENV —— 设置环境变量

```dockerfile
ENV APP_PORT=8000
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# 多个变量
ENV APP_PORT=8000 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=info
```

ENV 设置的变量在容器运行时也可以用，可以被 `docker run -e` 覆盖。

#### EXPOSE —— 声明容器监听的端口

```dockerfile
EXPOSE 8000
EXPOSE 8000/tcp
EXPOSE 8000/udp
```

注意事项：EXPOSE 只是"声明"，不是"映射"。不加 EXPOSE，端口照样能用 `-p` 映射。EXPOSE 的价值是文档说明（告诉用户容器用哪个端口）和 `-P`（大写）自动随机映射。

#### CMD —— 容器启动时的默认命令

```dockerfile
# Exec 形式（推荐）
CMD ["python", "app.py"]
CMD ["nginx", "-g", "daemon off;"]
CMD ["node", "server.js"]

# Shell 形式（信号处理有问题，不推荐）
CMD python app.py
```

注意事项：CMD 可以被 `docker run` 命令末尾的参数覆盖。例如 `docker run myimage bash` 会覆盖掉 CMD，直接运行 bash。

#### ENTRYPOINT —— 容器入口程序

```dockerfile
# Exec 形式（推荐）
ENTRYPOINT ["python", "app.py"]

# 配合 CMD 使用：ENTRYPOINT 是命令，CMD 是默认参数
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
```

**CMD vs ENTRYPOINT 对比：**

| | CMD | ENTRYPOINT |
| --- | --- | --- |
| 能被 docker run 参数覆盖 | 能（直接替换） | 能（作为额外参数追加） |
| 典型用途 | 默认启动命令，可以被覆盖 | 容器的固定入口，参数可变 |
| 两者同时存在 | CMD 作为 ENTRYPOINT 的默认参数 | ENTRYPOINT 是主命令 |

例子：
```dockerfile
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]
# docker run myimage             → 运行 docker-entrypoint.sh postgres
# docker run myimage redis-server → 运行 docker-entrypoint.sh redis-server
```

#### ARG —— 构建时参数（只在构建时有效）

```dockerfile
ARG APP_VERSION=1.0.0
ARG BUILD_ENV=production

# 使用
RUN echo "Building version $APP_VERSION"

# 构建时传入
# docker build --build-arg APP_VERSION=2.0.0 .
```

注意事项：ARG 和 ENV 的区别：ARG 只在构建时有效，容器运行时看不到。ENV 构建和运行时都有效。不要用 ARG/ENV 传入密码（会保留在镜像历史里）。

#### USER —— 切换运行用户

```dockerfile
# 创建非 root 用户
RUN useradd -m -u 1000 appuser

# 切换到非 root 用户（安全实践）
USER appuser
```

注意事项：默认情况下容器以 root 用户运行，这是安全隐患。生产环境应该切换到非 root 用户。

#### HEALTHCHECK —— 健康检查

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### 4.2 完整示例：Python FastAPI 应用

```dockerfile
# 第一步：选择基础镜像，固定版本
FROM python:3.11-slim

# 第二步：设置工作目录
WORKDIR /app

# 第三步：先复制依赖文件（利用构建缓存）
COPY requirements.txt .

# 第四步：安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 第五步：复制应用代码（经常变，放后面）
COPY . .

# 第六步：声明端口
EXPOSE 8000

# 第七步：创建非 root 用户（安全）
RUN useradd -m -u 1000 appuser
USER appuser

# 第八步：启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.3 .dockerignore 文件

解释：`.dockerignore` 告诉 Docker 哪些文件不要放进构建上下文（类似 `.gitignore`）。这样可以加快构建速度，也避免把不必要的文件（如 `.env`、`node_modules`）复制进镜像。

```text
# .dockerignore 示例
.git
.env
.env.*
__pycache__
*.pyc
*.pyo
node_modules
.DS_Store
*.log
tests/
docs/
README.md
```

### 4.4 docker build 命令

```bash
# 基本构建（. 表示构建上下文是当前目录，默认找 Dockerfile）
docker build .

# 指定镜像名和标签
docker build -t myapp:latest .
docker build -t myapp:v1.0 .

# 使用指定的 Dockerfile（不叫 Dockerfile 时）
docker build -f Dockerfile.prod -t myapp:prod .

# 传入构建参数
docker build --build-arg APP_VERSION=2.0.0 -t myapp:2.0.0 .

# 不使用缓存（强制重新构建每一层）
docker build --no-cache -t myapp .

# 查看构建过程（详细输出）
docker build --progress=plain -t myapp .
```

## 5. 和前后知识的关系

这一节是 Docker 核心技能的重心。`06` 讲了分层原理，这一节应用这些原理写出高效的 Dockerfile。`08` 讲 Volume，`13` 讲多阶段构建（让镜像更小）。

## 6. 实战任务

1. 写一个简单的 Python 脚本 `hello.py`（内容：`print("Hello from Docker!")`），为它写一个 Dockerfile，构建成镜像，运行后能看到输出。
2. 用 `docker history 你的镜像名` 查看每一层，数一数有几层。
3. 修改 `hello.py` 的输出内容，重新构建，观察哪些层用了缓存，哪些层重新构建了。
4. 创建 `.dockerignore` 文件，排除 `.env` 和 `__pycache__`。

## 7. 检查自己是否学会

1. FROM 指令如果省略版本号会有什么风险？
2. 为什么要先 `COPY requirements.txt` 再 `RUN pip install`，而不是直接 `COPY . .` 后再 pip install？
3. CMD 和 ENTRYPOINT 的本质区别是什么？
4. ARG 和 ENV 的区别是什么？哪个能在容器运行时看到？
5. `.dockerignore` 的作用是什么？不加会有什么问题？

## 8. 常见误区

1. 误区：RUN 每条命令单独一行更清晰。  
   解释：每个 RUN 指令产生一层。如果第一层 RUN 安装了包，第二层 RUN 删除了缓存，缓存文件其实还在第一层，镜像没有变小。相关命令用 `&&` 连接成一个 RUN。

2. 误区：EXPOSE 会自动开放端口。  
   解释：EXPOSE 只是文档声明，实际端口映射还是要用 `docker run -p`。

3. 误区：容器里用 root 运行没关系，反正是隔离的。  
   解释：容器隔离不是绝对的，内核漏洞可能导致容器逃逸。以 root 运行的容器逃逸后危害更大。生产环境务必用 USER 切换到非 root。

## 9. 本节总结

Dockerfile 的核心指令：FROM 选基础镜像，WORKDIR 设工作目录，COPY 复制文件，RUN 执行命令，ENV 设环境变量，EXPOSE 声明端口，CMD/ENTRYPOINT 定义启动方式。最重要的实践：依赖安装在代码复制之前（利用缓存），相关 RUN 命令合并（减少层数），加 `.dockerignore`（避免无用文件进镜像），用 USER 切换非 root（安全）。
