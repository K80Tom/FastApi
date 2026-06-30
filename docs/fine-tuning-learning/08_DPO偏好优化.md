# 08 DPO 偏好优化

## 1. 这一节要解决什么问题

这一节让你理解 DPO 为什么需要 chosen/rejected 数据，它和 SFT、RLHF 的区别是什么，以及什么时候该使用偏好优化。

## 2. 基础概念解释

### DPO

通俗解释：DPO 像给模型看两份答案，然后告诉它“这份更好，那份更差”，让它学会偏好。

技术解释：DPO 是 Direct Preference Optimization，使用同一 prompt 下的 chosen 和 rejected 回答对，直接优化模型更倾向 chosen。

例子：问题是“解释 QLoRA”，chosen 回答准确简洁，rejected 回答混乱夸张。

### Preference data 偏好数据

通俗解释：偏好数据像选择题，不是给唯一标准答案，而是给两个答案让你比较哪个好。

技术解释：偏好数据通常包含 `prompt`、`chosen`、`rejected` 三个部分。

例子：

```json
{
  "prompt": "解释 LoRA",
  "chosen": "LoRA 是一种参数高效微调方法，只训练少量新增参数。",
  "rejected": "LoRA 就是让模型随便调一下。"
}
```

### RLHF

通俗解释：RLHF 像先训练一个“评分老师”，再让模型根据老师打分不断改进。

技术解释：RLHF 是从人类反馈中进行强化学习，通常包括偏好收集、奖励模型训练和强化学习优化。

例子：Chatbot 对同一个问题生成多个答案，人类排序后训练奖励模型。

## 3. 为什么要学这个

SFT 让模型学会“像标准答案那样回答”，DPO 让模型学会“更偏好好答案，远离差答案”。当模型已经会回答，但回答风格、礼貌性、安全性、简洁性还有差距时，DPO 很有价值。

## 4. 关键知识点

### 4.1 DPO 解决什么问题

解释：DPO 适合优化“哪个答案更好”这种难以写成唯一标准答案的问题。

例子：

```text
prompt：请解释什么是微调。
chosen：先给生活类比，再给技术解释，适合初学者。
rejected：只写一堆英文缩写，初学者看不懂。
```

注意事项：DPO 不适合从零教模型基本任务。模型至少要已有基本指令能力。

### 4.2 DPO 数据格式

解释：DPO 数据必须成对比较，核心是同一个 prompt 下的好答案和差答案。

例子：

```jsonl
{"prompt":"什么是 SFT？","chosen":"SFT 是监督微调，用输入和标准答案训练模型。","rejected":"SFT 是一种数据库。"}
{"prompt":"显存不够怎么办？","chosen":"可以减小 batch size、缩短序列长度、使用 QLoRA。","rejected":"直接换最大模型就行。"}
```

注意事项：rejected 不一定要非常差，它可以是“可用但不如 chosen”。这样模型能学到更细的偏好。

### 4.3 DPO 和 SFT 的区别

解释：SFT 是模仿答案，DPO 是比较答案。

例子：

| 对比项 | SFT | DPO |
| --- | --- | --- |
| 数据 | instruction/output | prompt/chosen/rejected |
| 目标 | 学会标准回答 | 更喜欢好回答 |
| 阶段 | 基础后训练常用 | SFT 后进阶优化 |
| 难度 | 较低 | 较高 |

注意事项：很多项目流程是先 SFT，再 DPO，而不是直接 DPO。

### 4.4 DPO 和 RLHF 的区别

解释：DPO 简化了 RLHF，不需要单独训练奖励模型。

例子：RLHF 像先培养裁判，再让裁判指导选手训练。DPO 像直接拿比赛结果告诉选手哪个表现更好。

注意事项：DPO 虽然比 RLHF 简单，但仍需要高质量偏好数据。

### 4.5 最小 DPO 代码结构

解释：DPO 常用 `trl` 的 `DPOTrainer`。

例子：

```python
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig
from trl import DPOTrainer

model_name = "Qwen/Qwen2.5-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", trust_remote_code=True)

dataset = load_dataset("json", data_files="data/dpo.jsonl", split="train")

peft_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    task_type="CAUSAL_LM",
)

args = TrainingArguments(
    output_dir="./outputs/dpo-demo",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    num_train_epochs=1,
    logging_steps=1,
)

trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args=args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    peft_config=peft_config,
)

trainer.train()
```

注意事项：不同 `trl` 版本的 `DPOTrainer` 参数可能变化。DPO 比 SFT 更容易受版本影响，遇到报错先查本地版本。

## 5. 和前后知识的关系

DPO 是 SFT 后的进阶优化。你应该先理解 SFT 和 LoRA，再学 DPO。后面的评估章节会讲如何判断 DPO 是否真的改善了回答偏好。

## 6. 实战任务

写 5 条 DPO 偏好数据，主题是“微调学习助手”。要求：

1. 每条有同一个 prompt。
2. chosen 回答适合初学者。
3. rejected 回答存在明显问题，例如太抽象、事实错误、格式混乱或不礼貌。
4. 给每条写一句“为什么 chosen 更好”。

## 7. 检查自己是否学会

1. DPO 的三个核心字段是什么？
2. DPO 和 SFT 的训练目标有什么不同？
3. 为什么 DPO 通常放在 SFT 后？
4. rejected 是否必须完全错误？
5. DPO 为什么比 RLHF 简单？
6. 偏好数据质量差会导致什么问题？
7. 什么时候不建议使用 DPO？
8. DPO 可以和 LoRA 结合吗？

## 8. 常见误区

1. 误区：DPO 是更高级的 SFT，可以直接替代 SFT。  
   解释：DPO 适合偏好优化，不适合从零教基本任务。

2. 误区：rejected 越离谱越好。  
   解释：太离谱的 rejected 只能教模型分辨明显错误，不能学到细腻偏好。

3. 误区：DPO 不需要评估。  
   解释：偏好优化可能让模型变短、变保守或损失某些能力，必须评估。

4. 误区：DPO 一定需要全量微调。  
   解释：DPO 可以结合 LoRA 做低成本训练。

## 9. 本节总结

DPO 使用 prompt、chosen、rejected 数据，让模型更偏向好答案。它和 SFT 的区别在于“比较”而不是“模仿”。初学者应该先掌握 SFT 和 LoRA，再把 DPO 作为项目进阶亮点。

