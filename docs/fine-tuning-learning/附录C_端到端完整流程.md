# 附录C 端到端完整微调流程（从加载到推理，照抄能跑）

## 1. 这一节要解决什么问题

把分散在 05、06、13 里的代码片段，串成一条从 0 到 1 的完整流水线：下载模型 → 准备数据 → QLoRA 训练 → 合并权重 → 推理验证。给你一份可照抄、按顺序执行的脚本清单。

## 2. 基础概念解释

### 端到端流水线

通俗解释：像做一道菜的完整流程——买菜、洗菜、切菜、下锅、装盘、试吃。前面每节教的是单个步骤，这节把它们连起来一次走完。

技术解释：端到端流程指从原始模型和数据出发，经过数据处理、训练、权重合并、加载推理，最终得到可用模型的完整工程链路。

例子：你照着这份清单执行五个脚本，最后能用微调后的模型回答你的领域问题。

## 3. 为什么要学这个

初学者最大的痛点是“每段代码都看懂了，但连不起来”。跑通一次完整闭环，你才真正拥有“做过一个微调项目”的能力，也才有底气写进简历。这一节就是你 30 天项目的代码骨架。

## 4. 关键知识点

### 4.1 目录结构约定

解释：先约定一个项目结构，后面脚本都按这个路径来。

```text
my-finetune/
├── data/
│   └── train.jsonl          # 你的训练数据（messages 格式）
├── outputs/
│   └── qlora-adapter/       # 训练产出的 LoRA adapter
├── merged/                  # 合并后的完整模型
├── 1_prepare_data.py
├── 2_train_qlora.py
├── 3_merge.py
└── 4_inference.py
```

注意事项：跑之前先 `mkdir -p data outputs merged`（Windows 用资源管理器建也行）。

### 4.2 步骤一：准备数据（1_prepare_data.py）

解释：先造一份最小可用数据，确认格式和读取没问题。真实项目把这里换成你的数据。

```python
import json

# 用 messages 格式，至少先写 10 条；这里给 3 条示例
rows = [
    {"messages": [
        {"role": "system", "content": "你是新手友好的微调学习导师。"},
        {"role": "user", "content": "什么是 LoRA？"},
        {"role": "assistant", "content": "LoRA 是一种参数高效微调方法，冻结原模型，只训练少量低秩矩阵。"}]},
    {"messages": [
        {"role": "system", "content": "你是新手友好的微调学习导师。"},
        {"role": "user", "content": "什么是 QLoRA？"},
        {"role": "assistant", "content": "QLoRA 在 4bit 量化的模型上做 LoRA 训练，进一步降低显存。"}]},
    {"messages": [
        {"role": "system", "content": "你是新手友好的微调学习导师。"},
        {"role": "user", "content": "微调和 RAG 的区别？"},
        {"role": "assistant", "content": "微调修改模型参数学习风格行为，RAG 不改参数而是外挂检索知识。"}]},
]

with open("data/train.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"已写入 {len(rows)} 条数据到 data/train.jsonl")
```

注意事项：真实训练至少几百条才有意义，这里 3 条只为先跑通管道。

### 4.3 步骤二：QLoRA 训练（2_train_qlora.py）

解释：这是核心。4bit 加载基础模型 + LoRA 训练。需要 GPU 和 bitsandbytes（见附录A）。

```python
import torch
from datasets import load_dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, TrainingArguments)
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

# 4bit 量化配置：这是 QLoRA 省显存的关键
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                      # 用 4bit 加载
    bnb_4bit_quant_type="nf4",              # nf4 是 QLoRA 论文推荐的量化类型
    bnb_4bit_compute_dtype=torch.float16,   # 计算时用 fp16
    bnb_4bit_use_double_quant=True,         # 双重量化，再省一点
)

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
# 量化模型训练前的必要准备
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=8, lora_alpha=16, lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    task_type="CAUSAL_LM",
)

dataset = load_dataset("json", data_files="data/train.jsonl", split="train")

training_args = TrainingArguments(
    output_dir="./outputs/qlora-adapter",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=1,
    save_strategy="epoch",
    fp16=True,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=dataset,
    peft_config=lora_config,
    max_seq_length=512,
)

trainer.train()
trainer.save_model("./outputs/qlora-adapter/final")
print("训练完成，adapter 已保存")
```

注意事项：新版 `trl` 的 `SFTTrainer` 能自动识别 `messages` 字段并套用对话模板。如果你的 `trl` 版本报参数错误，按 05 节提示对照本地版本文档调整。这里 0.5B + 4bit，消费级小显存也能跑。

### 4.4 步骤三：合并 LoRA（3_merge.py）

解释：训练产出的是 adapter（小补丁），合并后得到一个独立完整模型，部署更方便。

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model_name = "Qwen/Qwen2.5-0.5B-Instruct"
adapter_path = "./outputs/qlora-adapter/final"

# 合并时用 fp16 全精度加载基础模型（不要再 4bit）
base = AutoModelForCausalLM.from_pretrained(
    base_model_name, torch_dtype=torch.float16,
    device_map="auto", trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)

# 贴上 adapter 再合并
model = PeftModel.from_pretrained(base, adapter_path)
model = model.merge_and_unload()

model.save_pretrained("./merged")
tokenizer.save_pretrained("./merged")
print("已合并保存到 ./merged")
```

注意事项：**合并要用全精度(fp16)加载基础模型，不要用 4bit**，否则合并的权重会有问题。合并后 `./merged` 是一个普通模型目录，可直接被 transformers / vLLM / Ollama 使用。

### 4.5 步骤四：推理验证（4_inference.py）

解释：加载合并后的模型，问它训练过的问题，看效果。

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_dir = "./merged"
tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_dir, torch_dtype=torch.float16,
    device_map="auto", trust_remote_code=True)

messages = [
    {"role": "system", "content": "你是新手友好的微调学习导师。"},
    {"role": "user", "content": "什么是 QLoRA？"},
]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)

with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=200, do_sample=False)
print(tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

注意事项：`apply_chat_template` 会按模型自带的对话模板拼好 prompt，这一步很关键，漏了输出会变差。对比微调前后同一问题的回答，就是最直观的评估(见 12)。

### 4.6 执行顺序与排错入口

解释：严格按顺序跑。

```bash
python 1_prepare_data.py   # 几秒
python 2_train_qlora.py    # 几分钟（小模型小数据）
python 3_merge.py          # 1 分钟内
python 4_inference.py      # 几秒
```

注意事项：任何一步报错，去 16 节常见报错表查关键词。最常见的三类：CUDA out of memory(降 batch / 缩 max_seq_length)、bitsandbytes 装不上(见附录A)、target_modules 不匹配(打印模型结构找层名)。

## 5. 和前后知识的关系

这节是 05(LoRA)、06(QLoRA)、10(参数)、13(部署)的合体实操。附录A 保证环境就绪，附录B 保证数据格式正确，这节把它们跑成闭环，12 节负责评估这个闭环的产出。

## 6. 实战任务

1. 按 4.1 建好目录。
2. 依次跑四个脚本，记录每步耗时和是否报错。
3. 把 `1_prepare_data.py` 的 3 条数据换成你领域的 10 条。
4. 对比微调前(直接加载基础模型)和微调后(merged)对同一问题的回答，写下差异。
5. 把跑通过程中踩的坑记进你的 16 节排查表。

## 7. 检查自己是否学会

1. 完整流程分哪四大步？
2. 4bit 量化配置里 `nf4` 和 `double_quant` 各是什么作用？
3. `prepare_model_for_kbit_training` 为什么要调用？
4. 为什么合并 LoRA 时要用 fp16 而不是 4bit 加载基础模型？
5. adapter 和 merged 模型有什么区别，部署各有什么优劣？
6. `apply_chat_template` 漏掉会怎样？
7. 训练数据只有 3 条能说明什么、不能说明什么？
8. 哪一步最可能爆显存，怎么救？

## 8. 常见误区

1. 误区：训练完的 adapter 就能直接当模型用。  
   解释：adapter 需要配合基础模型，或先 merge 成完整模型。

2. 误区：合并时也用 4bit 加载更省事。  
   解释：合并必须全精度，否则权重不准，效果受损。

3. 误区：3 条数据跑通就算项目完成。  
   解释：那只验证了管道通畅，真实效果需要足量数据和评估。

4. 误区：推理时不用对话模板也行。  
   解释：Instruct 模型依赖特定模板，不套模板输出会明显变差。

## 9. 本节总结

一个微调闭环就四步：准备数据(messages 格式) → QLoRA 训练(4bit 加载 + LoRA) → 合并权重(fp16 加载后 merge) → 加载推理(套 chat template)。先用极少数据跑通管道，再换成真实数据放大。这套四脚本就是你简历项目的代码骨架，跑通它你就真正“做过微调”了。
