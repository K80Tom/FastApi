# 08 容器数据持久化：Volume

## 1. 这一节要解决什么问题

帮你解决"容器删了数据就没了"的问题。学会用 Volume 和 Bind Mount 让数据在容器生命周期之外持久存在，这是运行数据库、文件服务等有状态服务的必备知识。

## 2. 基础概念解释

### 为什么容器的数据会丢失

通俗解释：容器就像一个沙盒，你在里面做的任何修改（写文件、存数据）都在容器的"可写层"里。一旦容器被删除，可写层也消失了，里面的数据自然没了。

技术解释：容器的可写层（container layer）与容器绑定，`docker rm` 删除容器时可写层被删除。容器停止（docker stop）数据还在，但容器删除（docker rm）数据就没了。

### Volume（数据卷）

通俗解释：Volume 是 Docker 管理的一块独立存储区域，不属于任何容器。容器删了，Volume 还在。你可以把多个容器都连接到同一个 Volume 上共享数据。

技术解释：Volume 由 Docker 管理，存储在宿主机的 `/var/lib/docker/volumes/` 目录下（Linux），通过 Volume 驱动可以支持本地存储、NFS、云存储等后端。

### Bind Mount（绑定挂载）

通俗解释：Bind Mount 就是把宿主机上的一个目录或文件直接挂载进容器，容器看到的就是宿主机的真实目录，两边的修改互相可见。

技术解释：Bind Mount 将宿主机的任意路径挂载到容器的指定路径，宿主机和容器看到的是同一份数据。常用于开发时挂载源代码目录（宿主机改代码，容器立刻看到变化）。

## 3. 为什么要学这个

任何有状态的服务（数据库、文件上传、日志等）都必须用 Volume 或 Bind Mount，否则容器一重启数据就没了。这是实际项目中使用 Docker 的必备知识。

## 4. 关键知识点

### 4.1 三种挂载方式对比

| 特性 | Volume | Bind Mount | tmpfs |
| --- | --- | --- | --- |
| 存储位置 | Docker 管理的目录 | 宿主机任意路径 | 内存（不持久） |
| 数据持久化 | 是 | 是 | 否（重启消失） |
| 跨容器共享 | 是 | 是（共享同一宿主机路径） | 否 |
| 性能 | 好 | 好 | 最好 |
| Docker 管理 | 是（docker volume 命令） | 否 | 否 |
| 适合场景 | 数据库数据、生产持久化 | 开发时挂代码、配置文件 | 临时文件、缓存 |

### 4.2 Volume 的使用

```bash
# 创建 named volume
docker volume create pgdata

# 查看 volume 列表
docker volume ls

# 查看 volume 详情（包括在宿主机的实际路径）
docker volume inspect pgdata

# 运行容器时挂载 volume
docker run -d \
  --name my-postgres \
  -e POSTGRES_PASSWORD=mysecret \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# 删除容器后，volume 还在
docker rm -f my-postgres
docker volume ls  # pgdata 还在

# 重新启动容器，数据仍然存在
docker run -d \
  --name my-postgres \
  -e POSTGRES_PASSWORD=mysecret \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# 删除 volume（会真正删除数据！）
docker volume rm pgdata

# 删除容器时同时删除它使用的匿名 volume
docker rm -v my-postgres
```

### 4.3 Bind Mount 的使用

```bash
# 语法：-v 宿主机绝对路径:容器路径
# Windows 路径示例
docker run -d \
  --name my-web \
  -p 8080:80 \
  -v "C:\Users\用户名\mysite:/usr/share/nginx/html" \
  nginx

# macOS/Linux 路径示例
docker run -d \
  --name my-web \
  -p 8080:80 \
  -v /Users/用户名/mysite:/usr/share/nginx/html \
  nginx

# 推荐的新语法（--mount，更明确）
docker run -d \
  --name my-web \
  --mount type=bind,source=/Users/用户名/mysite,target=/usr/share/nginx/html \
  nginx
```

**开发时用 Bind Mount 挂载代码的典型场景：**
```bash
# 把当前目录（Python 项目）挂载进容器
# 这样修改本地代码，容器里立刻生效，不需要重新构建镜像
docker run -d \
  --name dev-server \
  -p 8000:8000 \
  -v $(pwd):/app \    # macOS/Linux，Windows 用 ${PWD} 或绝对路径
  myapp:latest
```

### 4.4 只读挂载

```bash
# 挂载为只读（容器内不能修改，安全）
docker run -d \
  -v /宿主机/config:/app/config:ro \
  myapp

# --mount 语法
docker run -d \
  --mount type=bind,source=/宿主机/config,target=/app/config,readonly \
  myapp
```

### 4.5 匿名 Volume vs Named Volume

```dockerfile
# Dockerfile 里声明 VOLUME
VOLUME /var/lib/postgresql/data
```

```bash
# 运行时不指定 -v，Docker 自动创建匿名 volume
docker run -d postgres:16-alpine

# 查看匿名 volume（名字是随机 hash）
docker volume ls
# DRIVER    VOLUME NAME
# local     3f4c8d9a2b1e...（随机生成的名字）

# 命名 volume 更好管理
docker run -d -v pgdata:/var/lib/postgresql/data postgres:16-alpine
```

注意事项：匿名 Volume 删容器时容易忘了删，会积累很多无用的 volume。养成用 named volume 的习惯。

### 4.6 数据备份与迁移

```bash
# 备份 volume 到 tar 文件
docker run --rm \
  -v pgdata:/source:ro \
  -v $(pwd):/backup \
  ubuntu \
  tar czf /backup/pgdata-backup.tar.gz -C /source .

# 从 tar 文件恢复到新 volume
docker volume create pgdata-new
docker run --rm \
  -v pgdata-new:/target \
  -v $(pwd):/backup \
  ubuntu \
  tar xzf /backup/pgdata-backup.tar.gz -C /target
```

## 5. 和前后知识的关系

数据持久化在 `10_Docker_Compose` 里会大量用到（数据库都需要挂 volume）。`16_生产实践` 里的数据管理策略也基于这里的知识。

## 6. 实战任务

1. 运行一个 MySQL 容器，用 named volume `mysql-data` 挂载数据目录，创建一个数据库和表，写入几条数据。
2. 删除 MySQL 容器，重新启动一个新的 MySQL 容器，挂载同一个 volume，验证数据还在。
3. 用 Bind Mount 把宿主机的一个目录挂载到 nginx 容器，修改宿主机目录里的 HTML 文件，刷新浏览器验证变化立刻生效。

## 7. 检查自己是否学会

1. 容器删除后数据为什么会消失？Volume 是怎么解决这个问题的？
2. Volume 和 Bind Mount 各自适合什么场景？
3. 匿名 Volume 和 Named Volume 的区别是什么？为什么推荐用 Named Volume？
4. 如何把一个 Volume 挂载为只读？用在什么场景？
5. `docker volume prune` 会删除哪些 volume？

## 8. 常见误区

1. 误区：容器停止（docker stop）数据就没了，要赶快备份。  
   解释：停止不等于删除。`docker stop` 只是停止进程，数据还在容器的可写层。只有 `docker rm` 才会删除容器和它的可写层（但 named volume 不受影响）。

2. 误区：`docker rm -v` 会删除所有挂载的 volume。  
   解释：`-v` 只删除容器使用的**匿名 volume**，Named Volume 不会被删除，必须显式 `docker volume rm` 才能删除。

3. 误区：Bind Mount 一定比 Volume 好，因为文件在宿主机上能直接看到。  
   解释：开发时 Bind Mount 方便，但生产环境推荐用 Volume：Docker 管理的 Volume 有更好的隔离性，备份迁移更方便，跨平台兼容性更好（Windows/Mac 路径问题少）。

## 9. 本节总结

容器的可写层随容器删除而消失，用 Volume 让数据独立于容器存在。Volume 由 Docker 管理，适合生产持久化；Bind Mount 挂载宿主机路径，适合开发时挂代码。用 Named Volume（`-v myvolume:/path`）而非匿名 Volume，便于管理和清理。只读挂载（`:ro`）适合挂配置文件等不应该被容器修改的内容。
