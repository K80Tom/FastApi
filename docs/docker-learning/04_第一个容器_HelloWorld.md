# 04 第一个容器：Hello World

## 1. 这一节要解决什么问题

帮你跑起来第一个容器，并逐步理解 `docker run hello-world` 这一行命令背后发生了什么，把理论和实际操作连起来。

## 2. 基础概念解释

### docker run

通俗解释：`docker run` 是"给我用这个镜像跑一个容器"的命令，它是 Docker 最常用的命令，相当于"创建 + 启动"的合并操作。

技术解释：`docker run` 先检查本地有没有指定镜像（没有就从仓库 pull），然后基于镜像创建容器（docker create），再启动容器（docker start），可选择是否附着到容器的输入输出（-it 模式）或后台运行（-d 模式）。

例子：`docker run nginx` 就是"用 nginx 镜像跑一个容器，如果本地没有 nginx 镜像就先去 Docker Hub 拉"。

### 前台运行 vs 后台运行

通俗解释：前台运行（不加 -d）时你的终端被"占住"，容器的输出直接显示；后台运行（加 -d）时命令立刻返回，容器在后台默默跑着。

技术解释：
- 不加 `-d`：当前终端 attach 到容器的 stdin/stdout/stderr，Ctrl+C 会终止容器
- 加 `-d`（detached）：容器在后台运行，只返回容器 ID，用 `docker logs` 查看输出

## 3. 为什么要学这个

`docker run` 是 Docker 的核心命令。理解它背后的流程（本地找镜像 → 拉取 → 创建容器 → 启动），以后出问题时才知道是哪一步卡住了。

## 4. 关键知识点

### 4.1 运行 hello-world，逐行解析输出

```bash
docker run hello-world
```

完整输出解析：
```text
Unable to find image 'hello-world:latest' locally
```
→ Docker 在本地找不到 hello-world 镜像（你是第一次运行），决定去 Docker Hub 拉。

```text
latest: Pulling from library/hello-world
c1ec31eb5944: Pull complete
Digest: sha256:...
Status: Downloaded newer image for hello-world:latest
```
→ Docker 从 Docker Hub 拉取了 hello-world:latest 镜像，下载完成。

```text
Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.
```
→ 容器里的程序运行了，把这段文字打印出来，然后程序退出，容器停止。

这四步正是 Docker 的完整工作流程！

### 4.2 docker run 完整流程图

```
你输入 docker run hello-world
         │
         ▼
Docker CLI 把请求发给 Docker Daemon
         │
         ▼
Daemon 检查本地有没有 hello-world 镜像
    ├── 有 → 直接用
    └── 没有 → 从 Docker Hub pull 下来
         │
         ▼
Daemon 创建容器（基于 hello-world 镜像）
         │
         ▼
Daemon 启动容器（运行镜像里指定的程序）
         │
         ▼
程序输出文字 → Docker Daemon → Docker CLI → 你的终端
         │
         ▼
程序运行结束，容器进入 exited 状态
```

### 4.3 运行 nginx，访问网页

hello-world 运行完就退出了。来看一个持续运行的例子：

```bash
# 后台运行 nginx，把容器的 80 端口映射到宿主机的 8080 端口
docker run -d -p 8080:80 --name my-nginx nginx
```

命令拆解：
- `-d`：后台运行，不占用终端
- `-p 8080:80`：端口映射，格式是 `宿主机端口:容器端口`
- `--name my-nginx`：给容器起个名字（不加的话 Docker 随机起名）
- `nginx`：使用的镜像名

运行后在浏览器访问 `http://localhost:8080`，能看到 nginx 欢迎页。

验证容器在运行：
```bash
# 查看正在运行的容器
docker ps

# 输出示例
CONTAINER ID   IMAGE   COMMAND                  CREATED         STATUS         PORTS                  NAMES
a1b2c3d4e5f6   nginx   "/docker-entrypoint.…"   10 seconds ago  Up 9 seconds   0.0.0.0:8080->80/tcp   my-nginx
```

### 4.4 交互式运行容器

有时你想进入容器内部，像登录了一台 Linux 一样操作：

```bash
# 运行 ubuntu 容器，进入 bash 交互终端
docker run -it ubuntu bash
```

命令拆解：
- `-i`（interactive）：保持标准输入打开
- `-t`（tty）：分配一个伪终端（让你能看到命令提示符）
- `ubuntu`：使用 ubuntu 镜像
- `bash`：容器启动后运行 bash 这个程序

进入后你会看到类似 `root@a1b2c3:/# ` 的提示符，这时你在容器内部，可以运行 Linux 命令。输入 `exit` 退出容器（退出后容器会停止）。

```bash
# 进入容器内部后
root@a1b2c3:/# ls
root@a1b2c3:/# cat /etc/os-release
root@a1b2c3:/# exit   # 退出，容器停止
```

### 4.5 查看容器状态

```bash
# 只看正在运行的容器
docker ps

# 看所有容器（包括已停止的）
docker ps -a

# 输出字段含义
CONTAINER ID：容器唯一 ID 的前 12 位
IMAGE：基于哪个镜像
COMMAND：容器启动时运行的命令
CREATED：创建时间
STATUS：当前状态（Up/Exited）
PORTS：端口映射
NAMES：容器名称
```

### 4.6 停止和删除容器

```bash
# 停止容器（发 SIGTERM 信号，容器优雅退出）
docker stop my-nginx

# 强制停止（发 SIGKILL，立刻终止）
docker kill my-nginx

# 删除已停止的容器
docker rm my-nginx

# 强制删除运行中的容器（= stop + rm）
docker rm -f my-nginx

# 停止后自动删除（一次性任务很常用）
docker run --rm hello-world
```

注意事项：`--rm` 标志非常有用，让容器退出后自动删除，不用手动清理。

## 5. 和前后知识的关系

这一节让概念落地到实际操作。`05` 会系统整理所有常用命令，`06` 深入镜像原理，`07` 教你自己构建镜像。

## 6. 实战任务

1. 运行 `docker run hello-world`，能看到成功输出。
2. 运行 `docker run -d -p 8080:80 --name my-nginx nginx`，在浏览器访问 `http://localhost:8080`，看到 nginx 欢迎页。
3. 运行 `docker ps -a`，能看到 my-nginx 容器正在运行，hello-world 容器已退出。
4. 运行 `docker run -it ubuntu bash`，进入容器，运行 `ls` 和 `cat /etc/os-release`，然后 `exit` 退出。
5. 运行 `docker stop my-nginx`，然后 `docker rm my-nginx`，清理掉这个容器。

## 7. 检查自己是否学会

1. `docker run -d` 和 `docker run`（不加 -d）的区别是什么？
2. `-p 8080:80` 里，8080 是宿主机端口还是容器端口？
3. 用 `--name` 给容器命名有什么好处？
4. `docker stop` 和 `docker kill` 的区别是什么？
5. `--rm` 标志有什么用？什么时候适合用？

## 8. 常见误区

1. 误区：`docker run nginx` 运行后什么都没输出，卡住了。  
   解释：nginx 是持续运行的服务，不加 `-d` 时终端会被占住（附着到容器输出）。用 `-d` 让它后台运行，或者 Ctrl+C 退出（但容器也会停止）。

2. 误区：容器停止了就是删除了。  
   解释：停止（stop）的容器还存在于系统中（`docker ps -a` 能看到），只是没在运行。要删除用 `docker rm`。

3. 误区：每次运行同名容器都要先删掉旧的，很麻烦。  
   解释：用 `docker run --rm` 让容器退出后自动删除，或者先 `docker rm -f 容器名` 强制删除旧的再运行新的。

## 9. 本节总结

`docker run` 是 Docker 最核心的命令，背后流程是：检查本地镜像 → 拉取（如果没有）→ 创建容器 → 启动容器。加 `-d` 后台运行，加 `-it` 交互模式，加 `-p` 做端口映射，加 `--name` 命名，加 `--rm` 用完自动删除。`docker ps -a` 看所有容器状态，`docker stop` 停止，`docker rm` 删除。
