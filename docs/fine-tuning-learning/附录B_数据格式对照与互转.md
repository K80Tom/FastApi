# 附录B 数据格式对照与互转脚本（建议配合 09 数据集准备一起看）

## 1. 这一节要解决什么问题

让你彻底分清 Alpaca、ShareGPT、OpenAI messages 三种主流微调数据格式长什么样、各自用在什么场景，并能用脚本在它们之间互相转换，不再因为“格式不对”跑不起来。

## 2. 基础概念解释

### 指令数据格式

通俗解释：训练数据就是“题目 + 标准答案”。不同框架对“题目和答案怎么摆放”有不同约定，这些约定就是数据格式。

技术解释：微调数据格式规定了字段名和结构，训练框架按格式把数据拼成模型输入(prompt)和训练目标(label)。

例子：同一条“解释 LoRA”的问答，用 Alpaca 写和用 ShareGPT 写，字段完全不一样，但表达的是同一件事。

### 单轮 vs 多轮

通俗解释：单轮是“一问一答”，多轮是“一段连续聊天，有好几个来回”。

技术解释：单轮数据只有一组 instruction/output；多轮数据包含多组 user/assistant 交替的对话历史。

例子：客服场景常是多轮(用户追问)，知识问答常是单轮。

## 3. 为什么要学这个

09 讲了数据清洗的思路，但实操时第一件事是“把数据整成框架要的格式”。LLaMA-Factory、trl 等工具支持的格式各不相同，格式错就直接报错或训练目标错位。看懂这三种格式，你才能拿别人的数据集为己所用，也能把自己的数据喂进任意框架。

## 4. 关键知识点

### 4.1 Alpaca 格式（最简单，单轮首选）

解释：斯坦福 Alpaca 项目带火的格式，三个字段：`instruction`(指令)、`input`(可选的补充输入)、`output`(答案)。

例子：

```json
{"instruction": "解释什么是 LoRA", "input": "", "output": "LoRA 是一种参数高效微调方法，只训练少量新增的低秩矩阵。"}
{"instruction": "翻译成英文", "input": "今天天气很好", "output": "The weather is nice today."}
```

注意事项：`input` 可以为空字符串。第二条展示了 `input` 的用法——指令是“翻译”，具体翻译内容放 `input`。Alpaca 不适合表达多轮对话。

### 4.2 ShareGPT 格式（多轮对话首选）

解释：用一个 `conversations` 数组，里面每个元素有 `from`(谁说的)和 `value`(说了什么)。`from` 常见取值：`human`(用户)、`gpt`(助手)，有时还有 `system`。

例子：

```json
{"conversations": [
  {"from": "human", "value": "什么是微调？"},
  {"from": "gpt", "value": "微调是在已有大模型上用特定数据继续训练。"},
  {"from": "human", "value": "那它和 RAG 有什么区别？"},
  {"from": "gpt", "value": "微调改模型参数，RAG 不改参数而是外挂检索。"}
]}
```

注意事项：多轮训练时，通常只对 `gpt`(助手)的回答计算 loss，用户的话只作为上下文。框架会自动处理，但你要知道这个原理。

### 4.3 OpenAI messages 格式（API 风格，越来越主流）

解释：和调用 OpenAI/Claude API 一样的结构，用 `messages` 数组，每条有 `role`(`system`/`user`/`assistant`)和 `content`。

例子：

```json
{"messages": [
  {"role": "system", "content": "你是一个新手友好的 AI 学习导师。"},
  {"role": "user", "content": "什么是 QLoRA？"},
  {"role": "assistant", "content": "QLoRA 是在 4bit 量化的模型上做 LoRA 训练，进一步省显存。"}
]}
```

注意事项：`system` 用来设定角色和风格，对微调“说话风格”很有用。新版 trl 的 `SFTTrainer` 对这种格式支持很好。

### 4.4 三种格式速记对照

| 维度 | Alpaca | ShareGPT | OpenAI messages |
| --- | --- | --- | --- |
| 顶层字段 | instruction/input/output | conversations | messages |
| 角色字段名 | 无(隐含) | from: human/gpt | role: user/assistant/system |
| 内容字段名 | 无(直接) | value | content |
| 多轮支持 | 弱 | 强 | 强 |
| 有 system | 否 | 偶尔 | 是 |
| 常见框架 | LLaMA-Factory、早期教程 | LLaMA-Factory、Vicuna | trl 新版、API 微调 |

注意事项：这三种是“形不同神相同”，都是问答对，转换本质是改字段名和嵌套结构。

## 5. 和前后知识的关系

03 讲了 JSONL 是什么(一行一条样例)，09 讲数据清洗。这一节把“清洗好的内容”塞进正确的格式壳子。05/06 的 Demo 里 `dataset_text_field` 或 messages 处理，都依赖你这里整对格式。

## 6. 实战任务

下面给你**可直接运行的互转脚本**，用它把一种格式转成另一种。任务：拿你自己的 5 条数据，先写成 Alpaca，再用脚本转成 messages。

### 脚本 1：Alpaca → OpenAI messages

```python
import json

def alpaca_to_messages(in_path, out_path, system_prompt=""):
    with open(in_path, "r", encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            # 把 instruction 和 input 拼成用户的问题
            user_content = row["instruction"]
            if row.get("input"):
                user_content += "\n" + row["input"]
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_content})
            messages.append({"role": "assistant", "content": row["output"]})
            fout.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")

alpaca_to_messages("alpaca.jsonl", "messages.jsonl", system_prompt="你是新手友好的学习导师。")
```

### 脚本 2：ShareGPT → OpenAI messages

```python
import json

# from 字段到 role 的映射
ROLE_MAP = {"human": "user", "gpt": "assistant", "system": "system"}

def sharegpt_to_messages(in_path, out_path):
    with open(in_path, "r", encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            messages = []
            for turn in row["conversations"]:
                role = ROLE_MAP.get(turn["from"], "user")
                messages.append({"role": role, "content": turn["value"]})
            fout.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")

sharegpt_to_messages("sharegpt.jsonl", "messages.jsonl")
```

### 脚本 3：messages → Alpaca（只取单轮，多轮会丢历史）

```python
import json

def messages_to_alpaca(in_path, out_path):
    with open(in_path, "r", encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            msgs = json.loads(line)["messages"]
            # 找最后一组 user->assistant
            user = next((m["content"] for m in msgs if m["role"] == "user"), "")
            assistant = next((m["content"] for m in reversed(msgs) if m["role"] == "assistant"), "")
            fout.write(json.dumps(
                {"instruction": user, "input": "", "output": assistant},
                ensure_ascii=False) + "\n")

messages_to_alpaca("messages.jsonl", "alpaca.jsonl")
```

完成后回答：转换前后样例条数是否一致？多轮数据转成 Alpaca 丢了什么？

## 7. 检查自己是否学会

1. Alpaca 格式的三个字段分别是什么？
2. ShareGPT 里 `from` 的常见取值有哪些，对应什么角色？
3. OpenAI messages 的三种 role 分别干什么用？
4. 哪种格式最适合表达多轮对话，哪种最不适合？
5. 多轮训练时通常只对谁的内容算 loss？
6. 为什么把多轮 messages 转成 Alpaca 会丢信息？
7. `system` 字段对微调说话风格有什么帮助？
8. `ensure_ascii=False` 在写中文 JSON 时为什么重要？

## 8. 常见误区

1. 误区：三种格式是三种完全不同的数据。  
   解释：本质都是问答对，只是字段名和结构不同，可互转。

2. 误区：Alpaca 也能很好地表达多轮对话。  
   解释：Alpaca 是单轮设计，硬塞多轮会让上下文混乱。

3. 误区：用户的话也要让模型学着生成。  
   解释：通常只对助手回答算 loss，用户输入只作上下文，否则模型会学着替用户提问。

4. 误区：格式对了就万事大吉。  
   解释：格式只是壳，内容质量(09 讲的清洗)才决定效果。

## 9. 本节总结

主流微调数据格式三种：Alpaca(单轮、最简单)、ShareGPT(多轮、conversations/from/value)、OpenAI messages(API 风格、messages/role/content，带 system)。它们形不同神相同，都是问答对，可用几行脚本互转。选格式看两点：是否多轮、目标框架支持哪种。格式整对只是第一步，内容质量才是关键。
