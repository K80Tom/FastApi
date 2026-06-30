# 03 Docker 核心概念：镜像、容器、仓库

## 1. 这一节要解决什么问题

帮你搞清楚 Docker 的三大核心概念：镜像（Image）、容器（Container）、仓库（Registry），理解它们的关系，不再混淆。这三个概念贯穿所有 Docker 操作。

## 2. 基础概念解释

### 镜像（Image）

通俗解释：镜像就像一个"只读的模板"，或者说安装光盘。你从这个模板出发，启动一个或多个运行中的实例（容器）。你不能直接修改镜像本身，但可以基于镜像创建新镜像。

技术解释：Docker 镜像是一个只读的分层文件系统（Union File System），每一层代表 Dockerfile 中的一条指令。镜像包含了应用运行所需的所有内容：代码、运行时、库、环境变量、配置文件。

例子：`python:3.11-slim` 是一个镜像，里面有 Python 3.11 运行时和必要的系统库。你可以用这个镜像启动 100 个容器，每个容器都有完全一样的 Python 环境。

### 容器（Container）

通俗解释：容器是镜像的"运行实例"，就像用安装光盘装好后跑起来的操作系统。容器是活的（可以运行、暂停、停止），而镜像是死的（只读模板）。

技术解释：容器是在镜像之上加了一个可写层（writable layer），容器运行时对文件系统的修改都写在这个可写层。容器停止后可写层数据默认保留；容器删除后可写层数据丢失。

例子：你运行 `docker run -d nginx` 启动了一个容器，这个容器是"活的 nginx"，对外提供 HTTP 服务。你停止它（docker stop），它就不对外服务了，但还存在。你删除它（docker rm），才真正消失。

### 仓库（Registry）

通俗解释：仓库是存放和分享镜像的地方，就像 GitHub 存放代码。最大的公开仓库是 Docker Hub（hub.docker.com）。

技术解释：Registry 是镜像的存储和分发服务，提供镜像的 push（上传）和 pull（下载）接口。每个镜像有一个名称和标签（tag），格式为 `仓库地址/用户名/镜像名:标签`。

例子：
- `nginx:latest` — Docker Hub 上的官方 nginx 最新版镜像
- `python:3.11-slim` — Docker Hub 上的官方 Python 3.11 精简版镜像
- `yourusername/myapp:v1.0` — 你推送到 Docker Hub 的自定义镜像

## 3. 为什么要学这个

这三个概念是 Docker 所有命令的基础。`docker pull` 是拉镜像，`docker run` 是从镜像创建并启动容器，`docker push` 是把镜像推到仓库。不理解这三者的关系，命令就只是机械背诵。

## 4. 关键知识点

### 4.1 三者关系图

```
Docker Hub（仓库）
    │
    │  docker pull（下载镜像）
    ▼
本地镜像（Image）—— 只读，不能直接修改
    │
    │  docker run（从镜像创建并启动容器）
    ▼
容器（Container）—— 可写，正在运行的实例
    │
    │  docker commit（把容器的当前状态保存为新镜像）
    ▼
新的本地镜像
    │
    │  docker push（把镜像推到仓库）
    ▼
Docker Hub（仓库）
```

### 4.2 镜像命名规则

解释：理解镜像名的格式，才能看懂 `docker pull` 命令在拉什么。

```text
完整格式：[仓库地址/][用户名/]镜像名[:标签]

例子：
docker.io/library/nginx:latest     完整写法（官方镜像）
nginx:latest                        简写（省略了 docker.io/library/）
nginx                               再省略（省略了 :latest，默认用 latest）

python:3.11-slim                    官方 Python 镜像，3.11-slim 标签
yourusername/myapp:v1.0            你自己的镜像，v1.0 标签

ghcr.io/owner/repo:sha-abc123      GitHub Container Registry 的镜像
registry.cn-hangzhou.aliyuncs.com/xxx/yyy:1.0   阿里云私有仓库的镜像
```

注意事项：`latest` 标签不代表"最新版"，它只是一个名叫 latest 的标签，由镜像维护者决定指向哪个版本。生产环境不要用 `:latest`，用具体版本号。

### 4.3 镜像的分层结构

解释：镜像的分层设计让多个镜像可以共享底层，节省磁盘空间和下载时间。

```text
镜像 A（python:3.11-slim）
├── 第 1 层：Debian 系统基础层（100MB）
├── 第 2 层：Python 3.11 运行时（50MB）
└── 第 3 层：pip 工具（5MB）

镜像 B（你自己的 myapp，基于 python:3.11-slim）
├── 第 1 层：Debian 系统基础层（共享，不重复存储）
├── 第 2 层：Python 3.11 运行时（共享，不重复存储）
├── 第 3 层：pip 工具（共享，不重复存储）
├── 第 4 层：你安装的依赖（20MB）
└── 第 5 层：你的应用代码（1MB）

结果：镜像 B 只需要额外存储 21MB，不是 176MB
```

注意事项：这就是为什么第一次拉镜像慢（下所有层），第二次快（很多层已经有了，只下新的层）。

### 4.4 容器的生命周期

解释：容器从创建到销毁有明确的状态，理解这些状态才能知道用哪个命令。

```text
镜像
  │
  │ docker create（只创建，不启动）
  ▼
created（已创建，未运行）
  │
  │ docker start（启动）
  ▼
running（运行中）
  │             │
  │ docker pause │ docker stop（发 SIGTERM，等待优雅退出）
  ▼             ▼
paused        exited（已退出，数据还在）
  │             │
  │ docker unpause │ docker start（重新启动）
  ▼             │
running ◄───────┘
                │
                │ docker rm（删除容器）
                ▼
              （容器消失，可写层数据丢失）
```

常用简化流程：
```bash
docker run    # = docker create + docker start 合并操作
docker run -d # 后台运行（detached mode）
docker run -it # 交互模式（分配终端）
```

### 4.5 Docker Hub 使用基础

解释：Docker Hub 是官方公共仓库，有大量可以直接用的官方镜像。

**官方镜像（Official Images）：**
```text
这些是 Docker 官方维护的镜像，质量有保证，命名不带用户名前缀：
- nginx          Web 服务器
- python         Python 运行时
- node           Node.js 运行时
- mysql          MySQL 数据库
- redis          Redis 缓存
- postgres       PostgreSQL 数据库
- ubuntu         Ubuntu 操作系统
- alpine         极简 Linux（5MB 左右，常用作基础镜像）
```

**搜索镜像：**
```bash
# 命令行搜索
docker search nginx

# 或者在浏览器访问 hub.docker.com 搜索
```

**查看镜像标签：**
```text
Docker Hub 网页版可以看到所有 tag，比如 nginx 有：
- nginx:latest
- nginx:1.25
- nginx:1.25-alpine
- nginx:1.25-slim
选 alpine 版本体积最小，选带版本号的最稳定
```

## 5. 和前后知识的关系

这一节建立核心概念模型，`04` 开始用 `docker run` 动手跑第一个容器，`05` 系统学习操作镜像和容器的所有常用命令，`06` 深入理解镜像分层原理，`07` 学习自己构建镜像。

## 6. 实战任务

1. 打开浏览器访问 hub.docker.com，搜索 nginx，看看有哪些 tag 可用。
2. 运行 `docker pull nginx:alpine`，然后运行 `docker images`，看看本地有了哪些镜像。
3. 在纸上画出"镜像→容器→仓库"的关系图，不看文档画一遍。

## 7. 检查自己是否学会

1. 镜像和容器的关系，类比到现实中是什么和什么的关系？
2. 为什么说镜像是只读的？容器的修改写到哪里去了？
3. `nginx:latest` 和 `nginx:1.25-alpine` 的区别是什么？生产环境应该用哪个？
4. 镜像分层的好处是什么？能举一个具体的节省空间的例子吗？
5. 容器被删除（docker rm）之后，里面写入的文件会怎样？

## 8. 常见误区

1. 误区：容器停止后数据就没了。  
   解释：停止（stop）≠ 删除（rm）。停止后容器还存在，数据还在可写层。只有删除（rm）容器时数据才消失。

2. 误区：latest 是最新版，直接用 latest 最好。  
   解释：latest 只是一个标签名，不保证指向真正的最新稳定版。生产环境用具体版本号，避免镜像更新导致意外的行为变化。

3. 误区：从同一个镜像运行多个容器，它们会互相影响。  
   解释：不会。每个容器有独立的可写层，一个容器的修改不会影响其他容器，也不会改变原始镜像。

4. 误区：镜像很大，存多个镜像会占很多磁盘。  
   解释：多个镜像共享相同的底层，实际占用空间比镜像大小之和小很多。用 `docker system df` 可以看真实占用。

## 9. 本节总结

Docker 的三大核心概念：**镜像**是只读的模板（光盘），**容器**是镜像的运行实例（装好在跑的系统），**仓库**是存放镜像的地方（Docker Hub 是最大的公开仓库）。镜像分层设计让多个镜像共享底层，节省空间。容器删除（rm）才会真正丢失数据，停止（stop）不会。下一节：跑第一个容器，看看背后发生了什么。
