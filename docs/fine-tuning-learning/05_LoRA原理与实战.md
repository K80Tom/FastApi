# 05 LoRA 原理与实战

## 1. 这一节要解决什么问题

这一节让你理解 LoRA 为什么省显存、训练时到底训练了什么，并能读懂一个最小 LoRA 微调 Demo。

## 2. 基础概念解释

### LoRA

通俗解释：LoRA 像在一本厚教材旁边贴小便签。原教材不改，只训练这些便签，最后看书时把教材和便签一起用。

技术解释：LoRA 是 Low-Rank Adaptation，冻结基础模型原参数，在部分线性层旁边加入可训练的低秩矩阵，用少量参数学习任务适配。

例子：基础模型是通用聊天助手，LoRA 训练后可以让它更像“Fine-tuning 学习导师”。

### 冻结参数

通俗解释：冻结参数像规定“大厨原来的手艺不许改”，只允许他看你写的专项菜谱便签。

技术解释：冻结参数表示训练时不更新基础模型权重，只更新 LoRA 新增参数。

例子：训练日志里可训练参数可能只占总参数的 0.1% 到 2%。

### Merge LoRA 合并 LoRA

通俗解释：合并 LoRA 像把便签内容正式抄回教材里，之后不需要单独拿便签。

技术解释：Merge LoRA 是把 LoRA 权重合并进基础模型权重，得到一个独立可推理模型。

例子：部署时可以选择“基础模型 + LoRA adapter”动态加载，也可以先 merge 成一个模型目录。

## 3. 为什么要学这个

LoRA 是初学者最适合上手的微调方法。它成本低、训练快、保存文件小，能让你把重点放在数据、参数、日志和评估上，而不是一开始就被全量微调的显存问题卡住。

## 4. 关键知识点

### 4.1 LoRA 的核心思想

解释：大模型原参数很多，全部训练成本高。LoRA 假设任务适配不需要改动全部参数，只需要在关键层旁边加一些小矩阵。

例子：一个老师已经会讲课，你只需要给他一份“本班学生特点说明”，不用重新培养他成为老师。

注意事项：LoRA 适合窄任务和风格适配。如果基础模型本身完全不会某种能力，LoRA 的提升有限。

### 4.2 LoRA 常见参数

解释：LoRA 训练配置里常见 `r`、`lora_alpha`、`lora_dropout`、`target_modules`。

例子：

| 参数 | 通俗理解 | 常见取值 | 注意事项 |
| --- | --- | --- | --- |
| r | 便签容量大小 | 4、8、16、32 | 越大可训练参数越多 |
| lora_alpha | LoRA 影响强度 | 16、32、64 | 通常和 r 搭配调整 |
| lora_dropout | 训练时随机丢一点信息 | 0.05、0.1 | 防止过拟合 |
| target_modules | 便签贴在哪些层 | q_proj、v_proj 等 | 不同模型名称不同 |

注意事项：不要一次改很多参数。新手每次只改一个变量，然后记录效果。

### 4.3 最小可运行 Demo

解释：下面代码展示“加载模型 -> 加载数据 -> 配 LoRA -> SFT 训练 -> 保存”的最小流程。它需要 Python、PyTorch、transformers、datasets、peft、trl、accelerate。GPU 会更现实，CPU 也能读懂流程但训练非常慢。

例子：

```python
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    trust_remote_code=True,
)

rows = [
    {
        "text": "用户：什么是 LoRA？\n助手：LoRA 是一种参数高效微调方法，只训练少量新增参数。"
    },
    {
        "text": "用户：微调适合解决什么问题？\n助手：微调适合让模型学习稳定格式、风格和任务行为。"
    },
]
dataset = Dataset.from_list(rows)

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    task_type="CAUSAL_LM",
)

training_args = TrainingArguments(
    output_dir="./outputs/lora-demo",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=1,
    save_steps=20,
    fp16=True,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=dataset,
    peft_config=lora_config,
    dataset_text_field="text",
    max_seq_length=512,
)

trainer.train()
trainer.save_model("./outputs/lora-demo/final")
```

注意事项：不同版本的 `trl` 参数可能有差异。如果报 `SFTTrainer` 参数错误，先查看你本地安装版本的文档或把 `trl` 升级到教程匹配版本。

### 4.4 逐行理解 Demo

解释：先不要背代码，按流程理解。

例子：

```text
AutoTokenizer：把文字变成 token id。
AutoModelForCausalLM：加载因果语言模型，也就是根据前文预测后文的模型。
Dataset.from_list：临时创建一个小训练集。
LoraConfig：告诉 PEFT 在哪里插 LoRA、训练多大。
TrainingArguments：训练参数，例如 batch、学习率、保存目录。
SFTTrainer：TRL 提供的监督微调训练器。
trainer.train：开始训练。
trainer.save_model：保存 LoRA 权重。
```

注意事项：初学看代码先找五件事：模型在哪里加载、数据在哪里读、LoRA 怎么配、训练参数在哪、模型保存到哪。

### 4.5 如何换成自己的数据

解释：把 `rows` 换成读取 JSONL 文件即可。

例子：

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="data/train.jsonl", split="train")
```

其中 `data/train.jsonl` 每行可以是：

```jsonl
{"text":"用户：什么是 FastAPI？\n助手：FastAPI 是一个高性能 Python Web 框架。"}
```

注意事项：先用 5 条数据跑通，再扩大到 100 条、1000 条。不要一开始就上大数据，报错定位会很痛苦。

### 4.6 常见报错

解释：LoRA Demo 常见问题集中在环境、显存、target_modules 和数据字段。

例子：

| 报错现象 | 可能原因 | 解决方向 |
| --- | --- | --- |
| CUDA out of memory | 显存不够 | batch 改 1，缩短 max_seq_length，用 QLoRA |
| target module not found | 模型层名字不匹配 | 打印模型结构，换 q_proj、v_proj、k_proj 等 |
| dataset_text_field not found | 数据字段名不对 | 确认 JSONL 里有 text 字段 |
| loss 不下降 | 数据太少或学习率不合适 | 检查样例质量，降低 learning rate |

注意事项：报错时先保存完整错误信息，不要只看最后一行。

## 5. 和前后知识的关系

LoRA 建立在前面的微调和 PEFT 概念上。下一节 QLoRA 会在 LoRA 基础上加入量化，进一步降低显存。后面的训练参数、日志、评估都会用 LoRA Demo 作为实践对象。

## 6. 实战任务

做一个纸面 LoRA 实验记录，不一定马上跑代码：

1. 选择一个小模型名称。
2. 写 5 条 `text` 字段训练样例。
3. 设置 `r=8`、`lora_alpha=16`、`batch_size=1`。
4. 说明训练输出保存在哪。
5. 写出如果显存不够，你准备改哪三个参数。

## 7. 检查自己是否学会

1. LoRA 为什么比全量微调省显存？
2. 冻结基础模型是什么意思？
3. `r` 变大可能带来什么影响？
4. `target_modules` 为什么会报错？
5. LoRA 保存的是完整模型吗？
6. Merge LoRA 适合什么时候做？
7. 为什么先用 5 条数据跑通流程？
8. LoRA 适合学习新知识还是稳定行为？

## 8. 常见误区

1. 误区：LoRA 文件就是完整模型。  
   解释：LoRA 通常只保存 adapter 权重，推理时还需要基础模型。

2. 误区：r 越大效果一定越好。  
   解释：r 太大可能更占显存，也可能在小数据上过拟合。

3. 误区：LoRA 可以弥补所有数据问题。  
   解释：数据错，模型会学错。LoRA 只是训练方式，不会自动清洗数据。

4. 误区：Demo 跑通就等于项目完成。  
   解释：项目还需要数据准备、评估、部署和复盘。

## 9. 本节总结

LoRA 的核心是冻结基础模型，只训练少量新增参数，因此非常适合初学者做微调实战。你需要重点看懂模型加载、数据字段、LoRA 配置、训练参数和保存目录。跑通最小 Demo 后，再逐步换成自己的数据和评估流程。

