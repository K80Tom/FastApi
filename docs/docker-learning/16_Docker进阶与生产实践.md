# 16 Docker 进阶与生产实践

## 1. 这一节要解决什么问题

帮你了解把 Docker 用于生产环境需要关注的问题：容器健康监控、资源限制、安全基础、日志管理、以及单机生产部署的最佳实践。

## 2. 关键知识点

### 2.1 容器健康检查

生产环境一定要配置健康检查，让 Docker 自动检测容器是否正常工作，而不是"进程在跑就当作正常"。

```dockerfile
# Dockerfile 里配置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

```yaml
# docker-compose.yml 里配置（覆盖 Dockerfile 的）
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      start_period: 40s    # 启动后 40 秒内不计失败（给应用初始化时间）
      retries: 3
```

```bash
# 查看健康状态
docker ps                          # STATUS 列会显示 (healthy) 或 (unhealthy)
docker inspect --format '{{.State.Health.Status}}' 容器名
docker inspect --format '{{json .State.Health}}' 容器名 | python -m json.tool
```

你的应用需要提供一个 `/health` 端点：

```python
# FastAPI 示例
@app.get("/health")
async def health_check():
    # 可以在这里检查数据库连接、依赖服务等
    return {"status": "healthy"}
```

### 2.2 资源限制

不限制资源，一个容器可能把宿主机内存用完，导致其他服务崩溃。

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'         # 最多用 1 个 CPU 核
          memory: 512M        # 最多用 512MB 内存
        reservations:
          cpus: '0.25'        # 保证 0.25 核
          memory: 256M        # 保证 256MB

  db:
    deploy:
      resources:
        limits:
          memory: 1G          # 数据库给多一点
```

```bash
# 监控资源使用
docker stats                          # 所有容器的实时监控
docker stats --no-stream              # 只输出一次（适合脚本）
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### 2.3 重启策略

```yaml
services:
  api:
    restart: unless-stopped    # 推荐生产使用

# 选项说明：
# no                不自动重启（默认）
# always            总是重启（包括 docker stop 后手动启动系统时）
# on-failure        只在退出码非 0 时重启
# unless-stopped    总是重启，除非用 docker stop 显式停止
```

### 2.4 安全基础

**原则一：不用 root 运行**
```dockerfile
# 在 Dockerfile 里创建非 root 用户
RUN useradd -m -u 1000 -s /bin/bash appuser
USER appuser
```

**原则二：只暴露必要端口**
```yaml
services:
  api:
    ports:
      - "8000:8000"     # 暴露给外部

  db:
    # 生产环境不暴露数据库端口！数据库只在内网访问
    # ports:
    #   - "5432:5432"  # 不要！
    expose:
      - "5432"          # 只在 Docker 网络内部暴露，外部无法访问
```

**原则三：敏感信息用环境变量，不要写在代码里**
```yaml
services:
  db:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}    # 从 .env 文件读取，不硬编码
```

**原则四：镜像扫描（发现已知漏洞）**
```bash
# Docker 内置扫描
docker scout quickview myapp:latest

# 用 trivy（开源工具，更全面）
trivy image myapp:latest
```

**原则五：使用只读根文件系统**
```yaml
services:
  api:
    read_only: true                   # 容器根文件系统只读
    tmpfs:
      - /tmp                          # 临时目录仍然可写
    volumes:
      - ./logs:/app/logs              # 需要写入的目录单独挂载
```

### 2.5 日志管理

**容器日志的问题：** 默认情况下，`docker logs` 的数据存在宿主机上没有大小限制，时间长了会把磁盘撑满。

```yaml
# 配置日志轮转（生产必配）
services:
  api:
    logging:
      driver: json-file
      options:
        max-size: "10m"       # 单个日志文件最大 10MB
        max-file: "5"         # 保留最多 5 个文件（共 50MB）
```

全局配置（`/etc/docker/daemon.json`）：
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

**集中日志（进阶）：** 生产环境推荐把日志发送到集中日志系统，方便检索和告警。

```yaml
# 发送日志到 Loki（Grafana 的日志系统）
services:
  api:
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-labels: "job=api,env=production"
```

### 2.6 单机生产部署的完整示例

小型项目（< 10万 DAU）用 Docker Compose 单机部署是够用的，不一定需要 Kubernetes。

```yaml
# docker-compose.prod.yml
services:
  nginx:                                # 反向代理（处理 HTTPS、静态文件）
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/conf:/etc/letsencrypt:ro    # HTTPS 证书
      - static_files:/app/static:ro
    depends_on:
      api:
        condition: service_healthy
    restart: always
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  api:
    image: myregistry/myapp:${APP_VERSION}    # 用具体版本号，不用 latest
    expose:
      - "8000"                                # 不暴露到宿主机，只内网访问
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G

volumes:
  pgdata:
  static_files:
```

### 2.7 部署更新流程

```bash
# 拉取新版本镜像
docker compose -f docker-compose.prod.yml pull

# 滚动更新（Compose 会逐个重启，尽量减少停机时间）
APP_VERSION=v2.0.0 docker compose -f docker-compose.prod.yml up -d

# 数据库迁移（更新前）
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# 查看更新后的状态
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api --tail 50

# 如果出问题，回滚到上个版本
APP_VERSION=v1.9.0 docker compose -f docker-compose.prod.yml up -d
```

### 2.8 定期清理脚本

```bash
#!/bin/bash
# /opt/scripts/docker-cleanup.sh
# 定期运行（cron 每周一次）

# 删除停止的容器
docker container prune -f

# 删除悬空镜像
docker image prune -f

# 删除没用的网络
docker network prune -f

# 查看清理后的磁盘使用
docker system df
```

```bash
# 加入 crontab（每周日凌晨 3 点运行）
crontab -e
# 0 3 * * 0 /opt/scripts/docker-cleanup.sh >> /var/log/docker-cleanup.log 2>&1
```

## 3. 进阶路径：Kubernetes

掌握了 Docker 单机部署后，下一步是 Kubernetes（K8s）：

```text
Docker 单机 → Docker Compose 多服务 → Docker Swarm（多机简单编排）→ Kubernetes（大规模生产编排）

学 Kubernetes 的前提：
  ✓ 能写 Dockerfile
  ✓ 能用 Compose 管理多服务
  ✓ 理解容器/镜像/网络/Volume 概念
  ✓ 理解健康检查、资源限制的意义

K8s 对应 Docker 概念：
  Docker Container → K8s Pod
  Docker Compose service → K8s Deployment
  Docker Volume → K8s PersistentVolume
  Docker Network → K8s Service
  docker-compose.yml → K8s YAML manifests
```

## 4. 实战任务

1. 给你的应用加一个 `/health` 端点，在 Compose 里配置健康检查，用 `docker ps` 看到 `(healthy)` 状态。
2. 给 API 容器加资源限制（内存 256M），用 `docker stats` 监控实际使用。
3. 配置日志轮转（max-size: 10m，max-file: 3），查看日志文件位置。

## 5. 本节总结

生产环境 Docker 的关键点：健康检查（让 Docker 知道容器是否真正正常）、资源限制（防止单容器吃掉全部资源）、`restart: always`（崩溃自动恢复）、日志轮转（防止磁盘被日志撑满）、安全基础（非 root 运行、不暴露数据库端口、敏感信息用环境变量）。单机小项目 Compose 够用，规模大了再上 Kubernetes。
