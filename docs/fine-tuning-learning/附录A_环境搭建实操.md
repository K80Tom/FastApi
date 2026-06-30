# 附录A 环境搭建实操（建议在 05 LoRA 实战之前看）

## 1. 这一节要解决什么问题

让你在动手跑微调之前，先搞清楚自己这台电脑能做什么、不能做什么，并知道没有 GPU 时去哪里借 GPU，怎么把环境一步步装好，不在第一道坎上卡死。

## 2. 基础概念解释

### GPU 和 CUDA

通俗解释：GPU 像一个有几千个小工人的工厂，特别擅长同时算大量乘法。CUDA 是英伟达给这个工厂配的“工作语言”，深度学习框架靠它指挥 GPU 干活。

技术解释：GPU 是显卡上的并行计算芯片，深度学习的矩阵运算高度并行，所以用 GPU 比 CPU 快几十到上百倍。CUDA 是 NVIDIA 的并行计算平台和驱动接口，PyTorch 通过对应 CUDA 版本调用显卡。

例子：同样训练一个 0.5B 模型 3 个 epoch，CPU 可能要几小时，单张消费级 GPU 可能几分钟。

### 虚拟环境（conda / venv）

通俗解释：虚拟环境像给每个项目单独开一个房间，装的东西互不打架。不建房间直接装，迟早把系统 Python 搞乱。

技术解释：虚拟环境是隔离的 Python 包安装空间，每个项目可以有自己独立的依赖版本。

例子：A 项目要 `transformers==4.40`，B 项目要 `4.30`，分别建两个环境就不冲突。

### bitsandbytes

通俗解释：负责“4bit/8bit 量化”的库，是 QLoRA 省显存的关键工具。它对系统和显卡比较挑。

技术解释：bitsandbytes 提供低比特量化和优化器实现，QLoRA 加载 4bit 模型依赖它。它对 CUDA 版本、操作系统敏感，Windows 原生支持历史上较弱。

例子：很多初学者在 Windows 上装 QLoRA 失败，根因往往就是 bitsandbytes。

## 3. 为什么要学这个

前面所有 Demo 都默认“环境已就绪”。但基础差的同学 80% 的时间会浪费在环境上：装不上、版本冲突、CUDA 不匹配、Windows 跑不了。先把这一关想清楚，后面才能专注学微调本身。

## 4. 关键知识点

### 4.1 先判断：我这台电脑能做什么

| 你的情况 | 能做的事 | 不能做的事 | 建议 |
| --- | --- | --- | --- |
| 只有 CPU（普通笔记本） | 读代码、理解流程、写数据、用极小模型(0.5B)勉强跑通流程看 loss | 真正训练、QLoRA 量化、跑出有效果的模型 | 理论 + 云 GPU |
| 有 NVIDIA 显卡 6-8GB | 0.5B/1.5B 模型 LoRA、QLoRA 小实验 | 7B 全量微调 | 本地练手够用 |
| 有 NVIDIA 显卡 12-24GB | 7B QLoRA、3B LoRA | 大模型全量 | 主力机 |
| 苹果 M 芯片 Mac | 部分 MPS 加速实验、推理 | bitsandbytes(QLoRA)基本不支持 | 推理可以，QLoRA 用云 |

注意事项：**bitsandbytes / QLoRA 在 Windows 原生和 Mac 上经常装不上**。最稳的训练环境是 Linux + NVIDIA GPU。Windows 用户强烈建议用 WSL2(Windows 里的 Linux 子系统)或直接用云 GPU。

### 4.2 没有 GPU 怎么办：三条借 GPU 的路

解释：初学者完全不必买显卡，租云 GPU 性价比更高。

| 方案 | 特点 | 适合谁 |
| --- | --- | --- |
| Google Colab | 免费档有 T4 GPU，开箱即用，国外网络 | 跑最小 Demo、学流程 |
| AutoDL（国内） | 按小时租，便宜，镜像现成，中文友好 | 国内学习者主力 |
| 阿里云/腾讯云 GPU | 正式、稳定、稍贵 | 做正式项目 |

例子：在 AutoDL 上租一张 3090(24GB)，选 PyTorch 镜像，按小时几块钱，几分钟就能开始跑 QLoRA。

注意事项：云 GPU 按时计费，**跑完记得关机**，否则持续扣费。

### 4.3 标准安装流程（Linux / WSL2 / 云 GPU）

解释：下面是一套能跑 LoRA/QLoRA 的最小环境。先建虚拟环境，再按顺序装。

例子：

```bash
# 1. 建并激活 conda 环境
conda create -n ft python=3.10 -y
conda activate ft

# 2. 先装 PyTorch（一定要按你的 CUDA 版本选命令，去 pytorch.org 查）
#    下面是 CUDA 12.1 的示例
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 3. 装微调全家桶
pip install transformers datasets peft trl accelerate

# 4. QLoRA 需要的量化库（CPU/Mac 可能装不上，正常）
pip install bitsandbytes

# 5. 国内下模型用 modelscope 更快
pip install modelscope
```

注意事项：**PyTorch 必须先单独装，而且 CUDA 版本要和你的显卡驱动匹配**。不要直接 `pip install torch` 撞运气，去 pytorch.org 选你的系统和 CUDA 版本，复制官方命令。

### 4.4 验证环境是否装好

解释：装完先跑这段，确认 GPU 真的被认出来。

例子：

```python
import torch
print("PyTorch:", torch.__version__)
print("CUDA 可用:", torch.cuda.is_available())   # True 才算 GPU 就绪
if torch.cuda.is_available():
    print("显卡:", torch.cuda.get_device_name(0))
```

注意事项：如果 `torch.cuda.is_available()` 是 `False`，说明 PyTorch 没装对 CUDA 版本，或驱动有问题，回到 4.3 重装 PyTorch。

### 4.5 下载模型：HuggingFace vs ModelScope

解释：模型要从仓库下载。HuggingFace 是国际主流，国内访问慢；ModelScope(魔搭)是阿里的，国内快。

例子：

```python
# 方式一：HuggingFace（需要科学上网或镜像）
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

# 方式二：ModelScope（国内推荐）
from modelscope import snapshot_download
model_dir = snapshot_download("Qwen/Qwen2.5-0.5B-Instruct")
# 再把 model_dir 传给 from_pretrained
```

注意事项：国内同学如果 HuggingFace 下载卡住，可设镜像环境变量 `HF_ENDPOINT=https://hf-mirror.com`，或直接用 ModelScope。

## 5. 和前后知识的关系

这一节是 05 LoRA、06 QLoRA 实战的前置条件。03 讲了显存、量化是什么，这里告诉你怎么把那些概念落到一台真实机器上。装好环境后，回到 05 跑 Demo 就顺了。

## 6. 实战任务

不需要马上训练，先完成环境自查：

1. 写下你的情况属于 4.1 表里哪一类。
2. 如果没有 GPU，注册一个 Colab 或 AutoDL 账号。
3. 在你的环境(本地或云)里建一个 conda 环境 `ft`。
4. 跑 4.4 的验证脚本，记录 `torch.cuda.is_available()` 的结果。
5. 用 ModelScope 或 HuggingFace 下载 `Qwen2.5-0.5B-Instruct`，确认能下下来。

## 7. 检查自己是否学会

1. GPU 比 CPU 快在哪里？
2. 为什么要用 conda 虚拟环境，不直接装到系统 Python？
3. 为什么 PyTorch 要按 CUDA 版本单独装？
4. 为什么 Windows 原生跑 QLoRA 容易失败？
5. 没有 GPU 时有哪三条路可以走？
6. `torch.cuda.is_available()` 返回 False 说明什么？
7. 国内下模型用什么仓库更快？
8. 云 GPU 用完为什么要记得关机？

## 8. 常见误区

1. 误区：必须买一张好显卡才能学微调。  
   解释：云 GPU 按小时租几块钱，学习阶段完全够用。

2. 误区：`pip install torch` 装上就行。  
   解释：不指定 CUDA 版本可能装成 CPU 版，或和驱动不匹配，GPU 用不上。

3. 误区：bitsandbytes 装不上是我代码写错了。  
   解释：很可能是系统不支持(Windows 原生/Mac)，换 WSL2 或云 GPU 即可。

4. 误区：环境装一次就一劳永逸。  
   解释：不同教程依赖版本不同，建议一个项目一个环境，避免互相污染。

## 9. 本节总结

先判断自己的机器属于哪一类，没 GPU 就用 Colab 或 AutoDL。装环境的铁律是：先建 conda 环境，再按 CUDA 版本单独装 PyTorch，再装 transformers/peft/trl/accelerate，最后才装 bitsandbytes。装完一定跑验证脚本确认 GPU 被识别。这一关过了，后面的 LoRA/QLoRA 实战才跑得起来。
