# 10 Docker Compose 入门

## 1. 这一节要解决什么问题

帮你从"一次只能管一个容器"升级到"用一个文件定义和管理多个容器"，学会用 Docker Compose 一键启动包含多个服务（Web + 数据库 + 缓存）的完整应用。

## 2. 基础概念解释

### Docker Compose

通俗解释：Docker Compose 是"多容器的 Docker 管理工具"，你在一个 `docker-compose.yml` 文件里描述所有服务，然后用一条命令把它们全部启动起来，自动配置好网络和依赖关系。

技术解释：Docker Compose 是一个声明式工具，把多个容器的配置（镜像、端口、环境变量、volume、网络）写在 YAML 文件里，通过 `docker compose up/down` 统一管理这些容器的生命周期。

例子：你的项目有 FastAPI 后端 + PostgreSQL 数据库 + Redis 缓存，以前需要三个 `docker run` 命令，现在一个 `docker compose up` 全搞定，而且各服务之间的网络和依赖关系自动配好。

### docker compose vs docker-compose

通俗解释：两者功能一样，`docker compose`（中间没有连字符）是新版（V2），集成在 docker 命令里；`docker-compose`（有连字符）是老版（V1），需要单独安装。

推荐用新版：`docker compose`。

## 3. 为什么要学这个

现实项目几乎没有只有一个容器的情况。Compose 是日常开发中管理多容器项目的标准方式，也是理解 Kubernetes 等编排工具的入门台阶。

## 4. 关键知识点

### 4.1 docker-compose.yml 基本结构

```yaml
# docker-compose.yml

# Compose 文件版本（现代 Docker 已不需要指定，但老教程里会看到 version: "3.8"）
# version: "3.8"    # 可以省略

services:           # 定义所有服务（容器）
  service-name:     # 服务名（自定义，会作为 DNS 名）
    image: xxx      # 使用哪个镜像
    # 或者
    build: .        # 用 Dockerfile 构建

volumes:            # 定义 named volumes（可选）
  vol-name:

networks:           # 定义自定义网络（可选，不定义时 Compose 自动创建默认网络）
  net-name:
```

### 4.2 最常用的 service 配置项

```yaml
services:
  myapp:
    # 镜像来源：二选一
    image: nginx:1.25-alpine              # 直接用现有镜像
    build:                                # 或者用 Dockerfile 构建
      context: .                          # 构建上下文目录
      dockerfile: Dockerfile              # Dockerfile 文件名（默认就是 Dockerfile）

    # 容器名（可选，不指定则自动生成）
    container_name: my-web-container

    # 端口映射（宿主机:容器）
    ports:
      - "8080:80"
      - "8443:443"

    # 环境变量
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
      - DEBUG=false
      # 或者从 .env 文件读取
    env_file:
      - .env

    # 数据卷挂载
    volumes:
      - mydata:/app/data                  # named volume
      - ./config:/app/config:ro           # bind mount（只读）
      - .:/app                            # 开发时挂代码

    # 依赖的其他服务（先启动依赖，再启动本服务）
    depends_on:
      - db
      - redis

    # 网络（不指定则加入默认网络）
    networks:
      - app-net

    # 重启策略
    restart: unless-stopped    # no | always | on-failure | unless-stopped

    # 覆盖镜像的启动命令
    command: uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4.3 完整示例：FastAPI + PostgreSQL + Redis

```yaml
# docker-compose.yml

services:
  # 后端 API 服务
  api:
    build: .                              # 当前目录有 Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://appuser:apppass@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app                            # 开发时挂代码，热重载
    restart: unless-stopped

  # PostgreSQL 数据库
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD=apppass
      - POSTGRES_DB=appdb
    volumes:
      - pgdata:/var/lib/postgresql/data   # 数据持久化
    ports:
      - "5432:5432"                       # 可选：暴露给宿主机（方便用数据库工具连）
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
```

### 4.4 核心命令

```bash
# 启动所有服务（前台，能看到所有服务日志）
docker compose up

# 后台启动（最常用）
docker compose up -d

# 构建镜像后再启动（代码有变化时用）
docker compose up -d --build

# 停止并删除所有容器（volume 不删）
docker compose down

# 停止并删除容器 + volume（彻底清理数据）
docker compose down -v

# 只停止（不删除容器）
docker compose stop

# 重启某个服务
docker compose restart api

# 查看所有服务的状态
docker compose ps

# 查看服务日志
docker compose logs                 # 所有服务的日志
docker compose logs api             # 只看 api 服务
docker compose logs -f api          # 实时追踪 api 服务日志
docker compose logs --tail 50 api   # 最后 50 行

# 在某个服务里执行命令
docker compose exec api bash
docker compose exec db psql -U appuser -d appdb

# 查看服务的资源使用
docker compose top

# 拉取最新镜像（不重建）
docker compose pull
```

### 4.5 Compose 的网络自动配置

Compose 启动时会自动：
1. 创建一个以项目名命名的网络（如 `myproject_default`）
2. 把所有服务的容器都加入这个网络
3. 自动配置 DNS，让每个服务可以用**服务名**互相访问

```yaml
services:
  api:
    # 可以直接用 "db" 这个服务名访问数据库
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/appdb
  db:
    image: postgres:16-alpine
# 不需要手动创建网络，Compose 自动处理
```

所以 `@db:5432` 里的 `db` 就是服务名，Compose 帮你解析成数据库容器的 IP。

### 4.6 项目名和多环境

```bash
# 默认项目名是当前目录名
# 也可以用 -p 指定项目名
docker compose -p myproject up -d

# 用不同的 compose 文件（比如开发 vs 生产）
docker compose -f docker-compose.prod.yml up -d

# 查看当前项目列表
docker compose ls
```

## 5. 和前后知识的关系

这一节整合了前面所有知识（容器、镜像、Volume、网络），`11_Compose_进阶` 讲健康检查、依赖等待、环境变量管理等进阶技巧。

## 6. 实战任务

1. 创建一个包含 nginx + redis 的 `docker-compose.yml`，用 `docker compose up -d` 启动。
2. 用 `docker compose ps` 验证两个服务都在运行。
3. 用 `docker compose logs redis` 查看 Redis 的日志。
4. 用 `docker compose exec redis redis-cli ping` 进入 Redis 执行命令。
5. 用 `docker compose down` 停止并清理，用 `docker compose down -v` 连 volume 一起清理。

## 7. 检查自己是否学会

1. `docker compose up` 和 `docker compose up -d` 的区别是什么？
2. `docker compose down` 和 `docker compose down -v` 的区别是什么？
3. Compose 里服务之间怎么用服务名互相访问？这是怎么实现的？
4. `depends_on` 保证了什么？不保证什么（提示：只保证容器启动顺序，不保证服务就绪）？
5. `docker compose up --build` 和 `docker compose up` 的区别是什么？

## 8. 常见误区

1. 误区：`depends_on` 能保证数据库完全就绪后再启动 API。  
   解释：`depends_on` 只保证数据库**容器**已经启动，不保证数据库**服务**已经可以接受连接。数据库初始化需要时间，API 启动太快会连接失败。解决方案见 `11_Compose_进阶` 里的 healthcheck。

2. 误区：`docker compose down` 会删除数据。  
   解释：`docker compose down` 只删容器和网络，Named Volume 不受影响。只有加 `-v` 才会删 volume。

3. 误区：每次改了代码都要重新 build 镜像。  
   解释：开发时用 Bind Mount（`- .:/app`）挂载代码，代码改动立刻生效，不需要重新 build。只有改了 Dockerfile 或依赖（requirements.txt）才需要 `--build`。

## 9. 本节总结

Docker Compose 用 YAML 文件声明多个服务，`docker compose up -d` 一键启动，`docker compose down` 一键停止。Compose 自动创建网络，服务间用服务名互相访问。`depends_on` 控制启动顺序（但不能等待服务就绪），volume 保证数据持久化。开发环境推荐挂 Bind Mount 让代码改动实时生效，不用重复 build。
