# 02 安装 Docker 与环境配置

## 1. 这一节要解决什么问题

帮你完成 Docker 的安装和基本配置，让 `docker version` 和 `docker run hello-world` 能正常运行，为后续所有操作准备好环境。

## 2. 基础概念解释

### Docker Desktop

通俗解释：Docker Desktop 是 Windows 和 Mac 上的 Docker 图形化客户端，里面包含了 Docker 引擎、一个轻量 Linux 虚拟机、Compose、图形界面，一键安装全搞定。

技术解释：在 Windows/Mac 上，容器必须跑在 Linux 内核上，Docker Desktop 用 WSL2（Windows）或 HyperKit（Mac）运行一个轻量 Linux VM 来承载容器，用户感知不到这个 VM 的存在。

例子：在 Windows 上安装 Docker Desktop 后，打开终端就能用 `docker` 命令，所有 Linux 容器都正常跑，完全不需要自己配 Linux 环境。

### Docker Engine

通俗解释：Docker Engine 是 Linux 服务器上的 Docker，没有图形界面，直接装在系统上，是生产环境的标准选择。

技术解释：Docker Engine 包含 dockerd（后台服务）、containerd、docker CLI，通过 apt/yum 包管理器安装，以 systemd 服务形式运行。

### 镜像加速器

通俗解释：Docker Hub 服务器在国外，国内拉取镜像很慢。镜像加速器是国内的缓存服务器，配置后从国内节点拉，速度快很多。

技术解释：Docker 支持配置 registry-mirrors，将 pull 请求代理到指定的镜像加速服务，如阿里云、腾讯云、网易云提供的加速地址。

## 3. 为什么要学这个

没有可用的 Docker 环境，后面所有操作都做不了。安装看似简单，但 Windows 上的 WSL2 配置、权限问题、镜像加速配置都是新手常见的卡点，提前了解能省很多时间。

## 4. 关键知识点

### 4.1 Windows 安装（推荐用 Docker Desktop + WSL2）

**第一步：确认系统要求**
```text
Windows 版本：Windows 10 21H1 或更高（家庭版也支持）
架构：64位
WSL2：需要启用（Docker Desktop 安装时会引导你）
```

**第二步：启用 WSL2**
```powershell
# 以管理员身份运行 PowerShell，执行以下命令
wsl --install

# 重启电脑后，WSL2 会完成安装
# 验证 WSL2 版本
wsl --version
```

**第三步：下载安装 Docker Desktop**
```text
官方下载地址：https://www.docker.com/products/docker-desktop/
下载 Docker Desktop Installer.exe
双击安装，勾选 "Use WSL2 instead of Hyper-V"
安装完成后重启电脑
```

**第四步：验证安装**
```powershell
# 查看 Docker 版本
docker version

# 预期输出（版本号可能不同）
# Client: Docker Engine - Community
#  Version:           26.x.x
# Server: Docker Desktop
#  Engine Version:    26.x.x

# 运行测试容器
docker run hello-world
```

注意事项：如果提示 "Docker Desktop requires WSL2"，说明 WSL2 没装好，回到第二步。

### 4.2 macOS 安装

**Intel Mac：**
```text
下载：https://desktop.docker.com/mac/main/amd64/Docker.dmg
拖拽到 Applications 文件夹，打开即可
```

**Apple Silicon（M1/M2/M3）：**
```text
下载：https://desktop.docker.com/mac/main/arm64/Docker.dmg
安装方式相同，但镜像架构要注意（arm64 vs amd64 的兼容性问题）
```

**验证：**
```bash
docker version
docker run hello-world
```

### 4.3 Linux 安装（Ubuntu 为例）

```bash
# 1. 更新包索引
sudo apt-get update

# 2. 安装依赖
sudo apt-get install ca-certificates curl

# 3. 添加 Docker 官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# 4. 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装 Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# 6. 把当前用户加入 docker 组（避免每次都要 sudo）
sudo usermod -aG docker $USER
newgrp docker   # 让组权限立即生效，或者重新登录

# 7. 验证
docker version
docker run hello-world
```

注意事项：Linux 上不加 `sudo usermod -aG docker $USER` 的话，每次都要 `sudo docker`，很麻烦，建议装完立刻配置。

### 4.4 配置国内镜像加速（国内用户必配）

国内访问 Docker Hub 很慢，配置加速器可以显著提升拉取速度。

**方法一：通过 Docker Desktop 图形界面配置（推荐 Windows/Mac）**
```text
1. 打开 Docker Desktop
2. 点击右上角齿轮 → Settings → Docker Engine
3. 在 JSON 配置里加入 registry-mirrors
```

**配置内容（在 Docker Engine 的 JSON 里修改）：**
```json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://dockerhub.azk8s.cn",
    "https://registry.docker-cn.com"
  ]
}
```

**方法二：直接修改配置文件（Linux）**
```bash
# 创建或编辑 /etc/docker/daemon.json
sudo nano /etc/docker/daemon.json
```

```json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://dockerhub.azk8s.cn"
  ]
}
```

```bash
# 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置是否生效
docker info | grep -A 5 "Registry Mirrors"
```

注意事项：加速器地址可能会失效，如果拉取仍然慢，可以搜索"Docker 镜像加速 2024"获取最新可用地址。

### 4.5 验证安装完整性

运行以下命令，确认一切正常：

```bash
# 1. 查看版本（Client 和 Server 都要有输出）
docker version

# 2. 查看系统信息（能看到容器数量、镜像数量、存储驱动等）
docker info

# 3. 运行 hello-world，验证能拉取镜像和运行容器
docker run hello-world

# 预期输出
# Hello from Docker!
# This message shows that your installation appears to be working correctly.
```

### 4.6 Docker Desktop 图形界面介绍

安装好 Docker Desktop 后，界面主要有这几个区域：

```text
Containers（容器列表）：查看所有容器的运行状态，可以启停、查看日志
Images（镜像列表）：查看本地所有镜像，可以删除和 push
Volumes（数据卷）：查看本地数据卷
Dev Environments：开发环境配置（高级功能，暂时不用关注）
Settings → Docker Engine：修改 Docker 配置（加速器等）
```

注意事项：图形界面适合入门期快速查看状态，正式工作中还是用命令行更高效。

## 5. 和前后知识的关系

这一节是纯环境准备，装好之后就可以进入 `03` 学概念、`04` 动手操作。如果安装过程遇到问题，查 `14_常见报错` 里的安装部分。

## 6. 实战任务

1. 完成 Docker 安装，运行 `docker version`，把输出截图或复制下来。
2. 运行 `docker run hello-world`，看到成功输出。
3. 配置镜像加速器，运行 `docker pull nginx`，看看拉取速度是否正常（正常应该在 1 分钟内完成）。

## 7. 检查自己是否学会

1. Docker Desktop 和 Docker Engine 的区别是什么？分别用在什么场景？
2. 为什么 Windows/Mac 上跑 Docker 需要一个 Linux 虚拟机？
3. 配置镜像加速器的目的是什么？配置在哪里？
4. Linux 上为什么要把用户加入 docker 组？不加会怎样？
5. `docker version` 和 `docker info` 分别显示什么信息？

## 8. 常见误区

1. 误区：Windows 家庭版不能用 Docker。  
   解释：老版本 Docker 要求 Hyper-V，家庭版没有。但现在基于 WSL2 的 Docker Desktop 家庭版完全支持。

2. 误区：装了 Docker Desktop 就不用管 Linux 了。  
   解释：Docker Desktop 里的容器还是 Linux 容器，你写的 Dockerfile 最终还是跑在 Linux 上。了解 Linux 基础命令仍然很重要。

3. 误区：不配加速器也能用。  
   解释：能用，但不配的话拉取镜像可能很慢，甚至超时失败。国内环境强烈建议配置。

## 9. 本节总结

Windows/Mac 用 Docker Desktop（基于 WSL2/HyperKit），Linux 用 apt/yum 安装 Docker Engine。安装完成后运行 `docker run hello-world` 验证。国内用户配置镜像加速器可以显著改善拉取速度。Linux 用户记得把自己加入 docker 组，避免每次都要 sudo。
