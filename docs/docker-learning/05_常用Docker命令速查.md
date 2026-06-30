# 05 常用 Docker 命令速查

## 1. 这一节要解决什么问题

把 Docker 日常操作中最常用的命令系统整理一遍，让你知道"我要做这件事，用哪个命令"。这一节是参考手册，可以反复翻查。

## 2. 基础概念解释

### 命令结构

通俗解释：Docker 命令有规律，基本格式是 `docker 动作 目标`，比如 `docker run 镜像名`、`docker stop 容器名`、`docker pull 镜像名`。

技术解释：新版 Docker 推荐使用管理命令格式 `docker <object> <verb>`，如 `docker container run`、`docker image pull`，老版格式 `docker run`、`docker pull` 也完全支持，两者等价。

## 3. 关键知识点

### 3.1 镜像相关命令

```bash
# 拉取镜像（从 Docker Hub 或指定仓库）
docker pull nginx
docker pull nginx:1.25-alpine
docker pull python:3.11-slim

# 查看本地所有镜像
docker images
docker image ls  # 等价写法

# 查看镜像详细信息（架构、分层、配置等）
docker inspect nginx

# 查看镜像构建历史（每一层做了什么）
docker history nginx

# 删除镜像
docker rmi nginx
docker rmi nginx:latest python:3.11-slim  # 一次删多个

# 强制删除（镜像被容器使用时也删，慎用）
docker rmi -f nginx

# 删除所有没有被容器使用的镜像（清理磁盘）
docker image prune

# 给镜像打标签（相当于起别名）
docker tag nginx myregistry/mynginx:v1.0

# 搜索 Docker Hub 上的镜像
docker search redis
```

### 3.2 容器相关命令

```bash
# 创建并启动容器（最常用）
docker run nginx                          # 前台运行
docker run -d nginx                       # 后台运行
docker run -it ubuntu bash                # 交互模式
docker run --rm hello-world               # 用完自动删除
docker run --name my-web -d nginx         # 指定名字，后台运行
docker run -p 8080:80 -d nginx            # 端口映射
docker run -e ENV_VAR=value -d myapp      # 设置环境变量

# 查看容器
docker ps                                 # 正在运行的容器
docker ps -a                              # 所有容器（含已停止）
docker ps -q                              # 只输出容器 ID（方便批量操作）
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"  # 自定义格式

# 启动/停止/重启容器
docker start my-web                       # 启动已停止的容器
docker stop my-web                        # 优雅停止（SIGTERM）
docker kill my-web                        # 强制停止（SIGKILL）
docker restart my-web                     # 重启

# 进入运行中的容器
docker exec -it my-web bash               # 进入 bash（镜像有 bash 时）
docker exec -it my-web sh                 # 进入 sh（alpine 镜像用这个）
docker exec my-web ls /etc/nginx          # 在容器内执行命令，不进入交互

# 查看容器日志
docker logs my-web                        # 查看所有日志
docker logs -f my-web                     # 实时追踪日志（类似 tail -f）
docker logs --tail 50 my-web              # 只看最后 50 行
docker logs --since 10m my-web            # 看最近 10 分钟的日志

# 查看容器详细信息
docker inspect my-web                     # 完整 JSON 信息
docker inspect --format '{{.NetworkSettings.IPAddress}}' my-web  # 取特定字段

# 查看容器内进程
docker top my-web

# 查看容器资源使用（CPU/内存/网络）
docker stats                              # 所有容器的实时统计
docker stats my-web                       # 只看某个容器

# 删除容器
docker rm my-web                          # 删除已停止的容器
docker rm -f my-web                       # 强制删除（运行中也删）
docker rm $(docker ps -aq)                # 删除所有已停止的容器
docker container prune                    # 删除所有已停止的容器（更安全，会确认）

# 复制文件（宿主机 ↔ 容器）
docker cp my-web:/etc/nginx/nginx.conf ./nginx.conf  # 容器 → 宿主机
docker cp ./nginx.conf my-web:/etc/nginx/nginx.conf  # 宿主机 → 容器
```

### 3.3 Volume 相关命令

```bash
# 创建数据卷
docker volume create my-data

# 查看所有数据卷
docker volume ls

# 查看数据卷详情
docker volume inspect my-data

# 删除数据卷
docker volume rm my-data

# 删除所有没被使用的数据卷
docker volume prune

# 运行时挂载数据卷
docker run -v my-data:/app/data myapp     # named volume
docker run -v /宿主机/路径:/容器/路径 myapp  # bind mount
```

### 3.4 网络相关命令

```bash
# 查看所有网络
docker network ls

# 创建网络
docker network create my-network

# 查看网络详情
docker network inspect my-network

# 把容器连接到网络
docker network connect my-network my-web

# 把容器从网络断开
docker network disconnect my-network my-web

# 删除网络
docker network rm my-network

# 运行时指定网络
docker run --network my-network myapp
```

### 3.5 系统级命令

```bash
# 查看 Docker 系统信息
docker info

# 查看 Docker 版本
docker version

# 查看磁盘使用情况（镜像/容器/Volume 各占多少）
docker system df

# 清理所有未使用的资源（镜像/容器/网络/构建缓存）
docker system prune        # 会确认
docker system prune -a     # 连同没用的镜像一起删（更彻底）
docker system prune -af    # 强制，不确认（小心用）
```

### 3.6 常用组合场景

```bash
# 场景一：快速运行一个数据库，用完就删
docker run --rm -d \
  -e POSTGRES_PASSWORD=mysecret \
  -p 5432:5432 \
  --name temp-pg \
  postgres:16-alpine

# 场景二：进入一个一次性的 ubuntu 容器探索环境
docker run --rm -it ubuntu bash

# 场景三：查看所有容器，找出用了哪些端口
docker ps --format "table {{.Names}}\t{{.Ports}}"

# 场景四：批量停止所有运行中的容器
docker stop $(docker ps -q)

# 场景五：清理环境（开发机定期清理）
docker container prune   # 删已停止的容器
docker image prune       # 删悬空镜像
docker volume prune      # 删没用的 volume
```

### 3.7 命令速查表

| 操作 | 命令 |
| --- | --- |
| 拉取镜像 | `docker pull 镜像名:标签` |
| 查看本地镜像 | `docker images` |
| 删除镜像 | `docker rmi 镜像名` |
| 运行容器（后台） | `docker run -d 镜像名` |
| 运行容器（交互） | `docker run -it 镜像名 bash` |
| 查看运行中容器 | `docker ps` |
| 查看所有容器 | `docker ps -a` |
| 停止容器 | `docker stop 容器名` |
| 删除容器 | `docker rm 容器名` |
| 进入容器 | `docker exec -it 容器名 bash` |
| 查看日志 | `docker logs -f 容器名` |
| 查看资源用量 | `docker stats` |
| 构建镜像 | `docker build -t 镜像名 .` |
| 推送镜像 | `docker push 镜像名` |
| 清理未用资源 | `docker system prune` |

## 4. 和前后知识的关系

这一节是命令速查手册，随时可以翻。`06` 深入镜像原理，`07` 讲 `docker build`，`08`-`09` 讲 volume 和 network 的详细用法，`10` 讲 Docker Compose。

## 5. 实战任务

1. 拉取 `redis:alpine` 镜像，后台运行，名字叫 `my-redis`，端口映射 6379:6379。
2. 用 `docker stats my-redis` 查看它的资源使用情况。
3. 用 `docker exec -it my-redis redis-cli` 进入 Redis 命令行，输入 `PING`，看到 `PONG`。
4. 用 `docker logs my-redis` 查看 Redis 的启动日志。
5. 停止并删除 my-redis，再用 `docker system df` 查看磁盘使用。

## 6. 常见误区

1. 误区：`docker rm` 能删除运行中的容器。  
   解释：不行，必须先 stop 再 rm，或者用 `docker rm -f` 强制删除。

2. 误区：`docker system prune -a` 是安全的清理命令。  
   解释：`-a` 会删除所有没被容器使用的镜像，包括你精心构建的自定义镜像！只用 `docker system prune`（不加 -a），只删悬空镜像。

## 7. 本节总结

Docker 命令按操作对象分类记忆：镜像用 pull/images/rmi，容器用 run/ps/stop/rm/exec/logs，volume 用 volume create/ls/rm，网络用 network create/ls/rm，系统用 system df/prune。`docker exec -it 容器名 bash` 进入容器，`docker logs -f` 实时追踪日志，这两个是排查问题最常用的。
