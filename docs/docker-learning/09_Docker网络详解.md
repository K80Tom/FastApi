# 09 Docker 网络详解

## 1. 这一节要解决什么问题

帮你搞懂 Docker 的网络模型：容器之间怎么通信、容器和宿主机怎么通信、容器和外网怎么通信，以及如何让多个容器形成一个互联的服务网络。

## 2. 基础概念解释

### 容器网络

通俗解释：每个容器默认有自己的网络空间（独立的 IP、网卡），就像一台虚拟的局域网设备。Docker 提供几种网络模式，决定容器"接在哪个网络上"。

技术解释：Docker 使用 Linux 的 network namespace 给每个容器独立的网络栈。Docker 通过虚拟网桥（docker0）和 iptables 规则实现容器间通信、端口映射、网络隔离。

### 端口映射

通俗解释：容器里的端口外面看不到，用 `-p` 把容器的端口"开一个洞"映射到宿主机的端口上，外面才能访问。

技术解释：`-p 宿主机端口:容器端口` 通过 iptables NAT 规则，把宿主机端口的流量转发到容器的 IP:端口。

## 3. 为什么要学这个

多容器项目（Web + 数据库 + 缓存）需要容器间互相通信。不懂 Docker 网络，容器就是孤立的，无法组成完整的系统。

## 4. 关键知识点

### 4.1 Docker 的五种网络模式

#### bridge（桥接，默认模式）

```text
特点：
- 容器连接到 Docker 创建的虚拟网桥（docker0）
- 每个容器有独立 IP（通常 172.17.x.x 范围）
- 容器间可以通过 IP 通信
- 容器访问外网：通过 NAT 转发
- 外部访问容器：必须用 -p 映射端口
```

```bash
# 默认就是 bridge 模式
docker run -d --name web nginx

# 查看容器 IP
docker inspect --format '{{.NetworkSettings.IPAddress}}' web
# 输出：172.17.0.2

# 从另一个容器访问（通过 IP）
docker run --rm alpine ping 172.17.0.2
```

局限性：默认 bridge 网络的容器不能用容器名互相访问，只能用 IP。用**自定义网络**解决这个问题。

#### 自定义 bridge 网络（推荐）

```bash
# 创建自定义网络
docker network create my-net

# 运行时指定网络
docker run -d --name web --network my-net nginx
docker run -d --name db --network my-net postgres:16-alpine

# 在自定义网络里，容器可以用名字互相访问！
docker exec -it web ping db     # 直接用容器名 db 访问
docker exec -it web curl db:5432  # 容器名当域名用
```

这是最常用的容器间通信方式，也是 Docker Compose 默认采用的方式。

#### host（宿主机网络）

```bash
docker run -d --network host nginx
```

```text
特点：
- 容器直接使用宿主机的网络栈，没有独立 IP
- 容器监听的端口直接在宿主机上开放（不需要 -p 映射）
- 性能最好（没有 NAT 开销）
- 隔离性最差（容器和宿主机共享网络）
- Linux 可用，Mac/Windows Docker Desktop 不支持
适合场景：对网络性能要求极高、或需要容器直接绑定宿主机端口
```

#### none（无网络）

```bash
docker run --network none alpine
```

```text
特点：
- 容器完全没有网络，只有 loopback 接口
适合场景：完全隔离的计算任务，不需要任何网络
```

#### container（共享另一个容器的网络）

```bash
# 两个容器共享同一个网络栈（同一个 IP）
docker run -d --name web nginx
docker run -d --network container:web --name sidecar busybox
```

```text
特点：
- 两个容器共享同一个 IP 和端口空间
适合场景：Kubernetes sidecar 模式的模拟
```

### 4.2 端口映射详解

```bash
# 格式：-p [宿主机IP:]宿主机端口:容器端口[/协议]

# 最常用：映射单个端口
docker run -p 8080:80 nginx

# 指定只绑定到 localhost（外部无法访问，只有本机能访问）
docker run -p 127.0.0.1:8080:80 nginx

# 映射多个端口
docker run -p 8080:80 -p 8443:443 nginx

# 随机分配宿主机端口（-P 大写，自动分配）
docker run -P nginx
docker port nginx  # 查看分配了哪个端口

# 指定 UDP 端口
docker run -p 53:53/udp mydns
```

### 4.3 容器间通信实战

```bash
# 创建应用网络
docker network create app-net

# 启动 Redis
docker run -d \
  --name redis \
  --network app-net \
  redis:7-alpine

# 启动应用（可以用 "redis" 这个名字访问 Redis）
docker run -d \
  --name myapp \
  --network app-net \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  -p 8000:8000 \
  myapp:latest

# 验证：进入 myapp 容器，访问 redis
docker exec -it myapp sh
# 在容器内：
# ping redis
# redis-cli -h redis ping
```

### 4.4 查看和调试网络

```bash
# 查看所有网络
docker network ls

# 查看网络详情（包括哪些容器在这个网络里）
docker network inspect app-net

# 查看容器的网络信息
docker inspect --format '{{json .NetworkSettings.Networks}}' myapp

# 查看容器端口映射
docker port myapp

# 在容器里调试网络（用 alpine 作为调试工具）
docker run --rm --network app-net alpine sh
# 然后：ping redis, wget redis:6379, nslookup redis
```

### 4.5 DNS 解析机制

解释：自定义网络里，Docker 内置了 DNS 服务，容器名自动作为域名解析。

```text
app-net 网络里：
- redis 容器的 IP 是 172.20.0.2
- Docker 的内置 DNS 会把 "redis" 解析到 172.20.0.2
- myapp 容器里 curl http://redis:6379 可以访问 redis 容器
- 如果 redis 容器重启，IP 变了，DNS 自动更新，myapp 不需要改配置
```

注意事项：只有自定义网络才有 DNS 解析功能，默认的 bridge 网络没有！这是为什么推荐总是用自定义网络的原因。

### 4.6 网络管理命令

```bash
# 创建网络（指定子网和网关，可选）
docker network create \
  --driver bridge \
  --subnet 172.20.0.0/16 \
  --gateway 172.20.0.1 \
  app-net

# 把运行中的容器加入网络（一个容器可以在多个网络里）
docker network connect app-net existing-container

# 从网络中移除容器
docker network disconnect app-net existing-container

# 删除网络（有容器在使用时无法删除）
docker network rm app-net

# 清理没有容器使用的网络
docker network prune
```

## 5. 和前后知识的关系

`10_Docker_Compose` 会大量用到自定义网络（Compose 自动创建），`09` 里的网络概念是理解 Compose 服务间通信的基础。

## 6. 实战任务

1. 创建一个名为 `test-net` 的自定义网络。
2. 在 `test-net` 里启动一个 Redis 容器（名字叫 `my-redis`）和一个 alpine 容器（`docker run -it --network test-net --rm alpine sh`）。
3. 在 alpine 容器里 `ping my-redis`，验证能用容器名通信。
4. 在 alpine 容器里 `nc my-redis 6379`，输入 `PING`，看到 `+PONG` 响应。

## 7. 检查自己是否学会

1. 默认 bridge 网络和自定义 bridge 网络的主要区别是什么？
2. `-p 8080:80` 和 `-p 127.0.0.1:8080:80` 有什么区别？
3. 为什么在自定义网络里可以用容器名当域名？
4. host 网络模式的优势和适用场景是什么？
5. 一个容器可以同时连接多个网络吗？

## 8. 常见误区

1. 误区：容器连同一个默认 bridge 网络就能用名字互访。  
   解释：不能。默认 bridge 网络不支持 DNS 解析。必须用自定义网络。

2. 误区：宿主机能访问容器 IP（172.17.x.x）是永久可靠的。  
   解释：容器 IP 是动态分配的，容器重启后 IP 可能变。不要依赖 IP，用容器名或 Compose 服务名。

## 9. 本节总结

Docker 网络的核心：自定义 bridge 网络里容器可以互相用名字访问（内置 DNS），是多容器项目通信的标准方案。端口映射（-p）让外部能访问容器服务。host 模式性能最好但隔离性最差，仅特殊场景用。Docker Compose 自动创建网络并处理 DNS，下一节会看到这带来多大的便利。
