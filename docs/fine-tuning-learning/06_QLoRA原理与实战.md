# 06 QLoRA 原理与实战

## 1. 这一节要解决什么问题

这一节让你理解 QLoRA 如何在更低显存下训练 LoRA，并知道它的环境要求、代码改法和常见坑。

## 2. 基础概念解释

### QLoRA

通俗解释：QLoRA 像把厚教材压缩成便携版，再在旁边贴 LoRA 便签，桌面小也能学习。

技术解释：QLoRA 是 Quantized LoRA，在低比特量化加载的基础模型上训练 LoRA adapter，常见是 4bit 量化。

例子：原本普通 LoRA 跑不动 7B 模型，QLoRA 可能让它在更小显存上跑起来。

### 4bit 量化

通俗解释：4bit 量化像把高清照片压缩成更小尺寸，虽然细节少一点，但占用明显变小。

技术解释：4bit 量化把模型权重用更低精度表示，从而减少显存占用。

例子：使用 `BitsAndBytesConfig(load_in_4bit=True)` 加载模型。

### bitsandbytes

通俗解释：bitsandbytes 像一个专门负责“省显存计算”的工具箱。

技术解释：bitsandbytes 是支持低比特量化和优化器的库，常用于 8bit、4bit 加载和 QLoRA。

例子：QLoRA 代码通常会安装并导入 `bitsandbytes`。

## 3. 为什么要学这个

很多初学者的电脑显存有限，普通 LoRA 仍然可能爆显存。QLoRA 的价值是降低入门硬件门槛。但它对 GPU、CUDA、Linux/WSL、库版本更敏感，所以需要先理解再上手。

## 4. 关键知识点

### 4.1 QLoRA 和 LoRA 的关系

解释：QLoRA 不是替代 LoRA，而是“量化基础模型 + LoRA 训练”的组合。

例子：

```text
LoRA：基础模型按 fp16/bf16 加载，冻结原模型，训练 LoRA。
QLoRA：基础模型按 4bit 加载，冻结原模型，训练 LoRA。
```

注意事项：QLoRA 省的是基础模型加载显存，LoRA adapter 仍然以可训练参数形式存在。

### 4.2 最小 QLoRA 代码改法

解释：在 LoRA Demo 基础上，核心是增加 `BitsAndBytesConfig`。

例子：

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
```

注意事项：这段只展示 QLoRA 的模型加载部分，训练器和 LoRA 配置可以沿用上一节 Demo。

### 4.3 QLoRA 环境要求

解释：QLoRA 通常更依赖 GPU 和底层 CUDA 环境。

例子：

```text
适合：
1. Linux 或 WSL2
2. NVIDIA GPU
3. CUDA 与 torch 版本匹配
4. bitsandbytes 安装正常

不适合：
1. 纯 CPU 训练
2. CUDA 环境混乱
3. Windows 原生环境中 bitsandbytes 不兼容
```

注意事项：如果你的电脑基础一般，可以先理论学习 QLoRA，在云 GPU 或 WSL 环境中实践。

### 4.4 QLoRA 参数解释

解释：`nf4`、`double quant`、`compute dtype` 是 QLoRA 常见词。

例子：

| 参数 | 通俗理解 | 技术含义 | 注意事项 |
| --- | --- | --- | --- |
| load_in_4bit | 用很小盒子装权重 | 4bit 加载权重 | 省显存 |
| nf4 | 更适合神经网络权重的压缩方式 | NormalFloat4 | QLoRA 常用 |
| double quant | 再压缩一次压缩信息 | 二重量化 | 进一步省空间 |
| compute dtype | 计算时用什么精度 | fp16 或 bf16 | 取决于 GPU 支持 |

注意事项：新手不要随意改这些底层参数。先用常见配置跑通。

### 4.5 显存不够怎么办

解释：QLoRA 不是唯一省显存手段，还可以组合其他办法。

例子：

```text
1. per_device_train_batch_size 改成 1。
2. gradient_accumulation_steps 增大。
3. max_seq_length 从 2048 降到 512 或 1024。
4. 使用 4bit QLoRA。
5. 减小 LoRA r。
6. 使用更小模型。
7. 开启 gradient checkpointing。
```

注意事项：降低显存通常会牺牲速度或效果，要记录每次改动。

### 4.6 QLoRA 不适合解决什么

解释：QLoRA 只是省显存，不会自动提升数据质量或任务效果。

例子：如果数据里答案互相矛盾，QLoRA 训练后模型仍然会混乱。

注意事项：不要把 QLoRA 当成“效果增强器”。它首先是“资源节省器”。

## 5. 和前后知识的关系

QLoRA 建立在 LoRA 之上，因此应先学 `05_LoRA原理与实战.md`。后面的训练参数和报错排查会继续使用 QLoRA 场景解释显存、量化和环境问题。

## 6. 实战任务

把上一节 LoRA Demo 改成 QLoRA 纸面配置：

1. 加入 `BitsAndBytesConfig`。
2. 写出你选择 `load_in_4bit=True` 的原因。
3. 把 `max_seq_length` 设置为 512。
4. 说明如果 `bitsandbytes` 安装失败，你会怎么处理。

## 7. 检查自己是否学会

1. QLoRA 比 LoRA 多了哪一步？
2. 4bit 量化为什么能省显存？
3. bitsandbytes 在 QLoRA 中做什么？
4. QLoRA 会不会自动让模型效果更好？
5. Windows 原生环境为什么可能更麻烦？
6. 显存不够时可以先改哪三个参数？
7. `max_seq_length` 变大会影响什么？
8. QLoRA 保存的通常是完整模型还是 LoRA adapter？

## 8. 常见误区

1. 误区：QLoRA 是 LoRA 的高级版，所以一定更好。  
   解释：QLoRA 主要优势是省显存，效果取决于模型、数据和参数。

2. 误区：4bit 量化没有任何代价。  
   解释：量化可能带来精度损失，只是很多场景可接受。

3. 误区：显存不够只要用 QLoRA 就行。  
   解释：序列长度、batch size、优化器和中间激活也占显存。

4. 误区：环境报错说明代码一定错。  
   解释：QLoRA 报错常常是 CUDA、torch、bitsandbytes 版本不匹配。

## 9. 本节总结

QLoRA 是“4bit 量化基础模型 + LoRA 训练”的低显存方案。它适合显存有限的微调实验，但环境要求更高。初学者应该先会 LoRA，再把模型加载部分替换成 QLoRA，并记录显存和效果变化。

