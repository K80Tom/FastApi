# 11 Docker Compose 进阶

## 1. 这一节要解决什么问题

解决 Compose 使用中的进阶问题：数据库没准备好 API 就启动了怎么办、密码不能硬编码在 yml 里怎么办、不同环境（开发/生产）用不同配置怎么办。

## 2. 关键知识点

### 2.1 healthcheck + depends_on condition（等待服务就绪）

`depends_on` 只保证容器启动顺序，不保证数据库可以接受连接。正确做法是给数据库加 healthcheck，API 等数据库健康后再启动。

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy    # 等 db 健康后再启动
      redis:
        condition: service_started    # 只等启动，不等健康

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s       # 每 10 秒检查一次
      timeout: 5s         # 超时 5 秒判定失败
      retries: 5          # 失败 5 次判定 unhealthy
      start_period: 30s   # 启动后 30 秒内不计失败（给数据库初始化时间）

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
```

常用的 healthcheck test 命令：
```yaml
# PostgreSQL
test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]

# MySQL
test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]

# Redis
test: ["CMD", "redis-cli", "ping"]

# HTTP 服务
test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]

# TCP 端口是否开放
test: ["CMD-SHELL", "nc -z localhost 8000 || exit 1"]
```

### 2.2 环境变量与 .env 文件

**方式一：在 yml 里写死（不推荐，密码会进 git）**
```yaml
environment:
  POSTGRES_PASSWORD: mysecret123   # 不要这样！
```

**方式二：从 .env 文件读取（推荐）**

`.env` 文件（在 .gitignore 里排除）：
```env
POSTGRES_USER=appuser
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=appdb
API_SECRET_KEY=myverylongsecretkey
DEBUG=false
```

`docker-compose.yml`：
```yaml
services:
  api:
    environment:
      - SECRET_KEY=${API_SECRET_KEY}      # 从 .env 读取
      - DEBUG=${DEBUG:-false}             # 从 .env 读，没有则用默认值 false

  db:
    image: postgres:16-alpine
    env_file:
      - .env                              # 整个 .env 文件里的变量都传给容器
    environment:
      # 也可以单独设置，覆盖 env_file 里的同名变量
      - PGDATA=/var/lib/postgresql/data/pgdata
```

`.env.example`（提交到 git，给团队参考）：
```env
POSTGRES_USER=appuser
POSTGRES_PASSWORD=          # 填写你的数据库密码
POSTGRES_DB=appdb
API_SECRET_KEY=             # 填写你的密钥
DEBUG=false
```

`.gitignore`：
```
.env
.env.*
!.env.example
```

### 2.3 多环境配置：override 文件

Docker Compose 支持多文件合并，后面的文件会覆盖前面的同名配置。

```bash
# 默认：合并 docker-compose.yml + docker-compose.override.yml
docker compose up

# 明确指定文件（生产环境）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

`docker-compose.yml`（基础配置，开发和生产共用）：
```yaml
services:
  api:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/appdb

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

`docker-compose.override.yml`（开发环境专用，自动加载）：
```yaml
services:
  api:
    volumes:
      - .:/app                              # 挂代码，热重载
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"

  db:
    ports:
      - "5432:5432"                         # 开发时暴露端口，方便用数据库工具连
```

`docker-compose.prod.yml`（生产环境专用）：
```yaml
services:
  api:
    image: myregistry/myapp:${APP_VERSION}  # 用正式镜像，不用 build
    restart: always
    deploy:
      replicas: 2                           # 生产跑多个实例

  db:
    # 生产不暴露数据库端口
    restart: always
```

### 2.4 资源限制

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '0.5'          # 最多用 50% CPU
          memory: 512M         # 最多用 512MB 内存
        reservations:
          cpus: '0.25'         # 保证 25% CPU
          memory: 256M         # 保证 256MB 内存
```

注意事项：`deploy.resources` 在 `docker compose up` 里生效（Compose V2），旧版 `mem_limit` 已废弃。

### 2.5 profiles：按需启动服务

```yaml
services:
  api:
    build: .
    # 没有 profiles，总是启动

  db:
    image: postgres:16-alpine
    # 没有 profiles，总是启动

  adminer:                                  # 数据库管理界面，只在开发时需要
    image: adminer
    ports:
      - "8080:8080"
    profiles:
      - tools                               # 只有显式激活 tools 才启动

  prometheus:
    image: prom/prometheus
    profiles:
      - monitoring
```

```bash
# 只启动没有 profiles 的服务（api + db）
docker compose up -d

# 启动 tools profile（api + db + adminer）
docker compose --profile tools up -d

# 启动多个 profile
docker compose --profile tools --profile monitoring up -d
```

### 2.6 常用完整模板

```yaml
# docker-compose.yml（适合大多数 Web 项目）

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ${PROJECT_NAME}-api
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-net

  db:
    image: postgres:16-alpine
    container_name: ${PROJECT_NAME}-db
    env_file:
      - .env
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    networks:
      - app-net

  redis:
    image: redis:7-alpine
    container_name: ${PROJECT_NAME}-redis
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
    restart: unless-stopped
    networks:
      - app-net

volumes:
  pgdata:
  redisdata:

networks:
  app-net:
    driver: bridge
```

## 3. 和前后知识的关系

这一节是 Compose 的完整实践。后续 `15_开发实践` 会在真实开发工作流中用到这里的模板。

## 4. 实战任务

1. 在 `10` 节的 Compose 文件基础上，给 PostgreSQL 加上 healthcheck，给 API 加上 `condition: service_healthy`，验证 API 等数据库就绪后才启动。
2. 创建 `.env` 文件存放数据库密码，yml 里用 `${变量名}` 引用，确保密码不硬编码在 yml 里。
3. 创建 `.env.example` 文件作为模板提交到 git，`.env` 加入 `.gitignore`。

## 5. 常见误区

1. 误区：`depends_on` + `condition: service_healthy` 万无一失。  
   解释：healthcheck 只检查你指定的命令。数据库进程在跑不等于表都建好了、迁移都跑完了。应用代码里还是要有连接重试逻辑。

2. 误区：把 `.env` 文件提交到 git 是常规操作。  
   解释：`.env` 里有密码和密钥，绝对不能提交。提供 `.env.example` 作为模板。

## 6. 本节总结

Compose 进阶的三个关键点：healthcheck + `condition: service_healthy` 解决服务启动顺序和就绪问题；`.env` 文件分离配置和代码；多 compose 文件叠加（override/prod）解决多环境配置差异。生产环境一定要加 `restart: unless-stopped`，保证服务崩溃自动重启。
