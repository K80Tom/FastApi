# 15 GraphRAG 评估与调优

GraphRAG 做出来以后，不能只看“回答像不像”。  
真正要判断它有没有用，需要评估检索、图质量、答案质量和成本。

---

## 本节学习目标

学完本节后，你应该能：

- 知道 GraphRAG 要评估哪些层面。
- 区分检索评估、生成评估、图质量评估。
- 设计一组测试问题集。
- 对比普通 RAG 和 GraphRAG。
- 知道常见调优方向。

---

## 核心概念解释

### 1. 检索质量

检索质量关注：

```text
系统有没有找到对回答有帮助的上下文？
```

普通 RAG 看 chunk 是否相关。  
GraphRAG 还要看：

```text
实体是否匹配正确？
关系是否扩展合理？
社区摘要是否相关？
```

### 2. 答案质量

答案质量关注：

```text
最终回答是否正确、完整、可读、有证据。
```

### 3. 图质量

图质量关注：

```text
实体有没有重复？
关系有没有错？
社区划分是否合理？
图里噪声多不多？
```

### 4. Faithfulness

Faithfulness 可以理解为“忠实度”。

意思是：

```text
答案是否忠实于检索到的资料，而不是模型自己编的。
```

### 5. Ablation

Ablation 是消融实验。

通俗理解：

```text
把系统中的某个模块关掉，看效果会不会变差。
```

例如：

```text
只用向量检索
只用图检索
图 + 向量混合
```

比较三者效果，就能知道图到底有没有带来价值。

---

## 通俗理解

评估 GraphRAG 像检查一条生产线：

```text
原料有没有问题？         -> 文档质量
中间加工有没有错？       -> 实体关系抽取质量
仓库整理得好不好？       -> 图和向量存储质量
取货有没有取对？         -> 检索质量
最后成品是否合格？       -> 答案质量
成本是否可接受？         -> 性能和费用
```

如果只看最后答案，你不知道问题出在哪里。

---

## 技术流程图

GraphRAG 评估链路：

```text
测试问题集
-> 执行普通 RAG
-> 执行 GraphRAG local
-> 执行 GraphRAG global
-> 执行 GraphRAG hybrid
-> 记录检索上下文
-> 记录答案
-> 记录引用来源
-> 人工或 LLM 评分
-> 分析失败案例
-> 调整抽取、图清洗、检索参数、prompt
```

评估维度：

```text
检索相关性
答案准确性
答案完整性
引用正确性
关系链路合理性
全局总结质量
响应时间
token 成本
```

---

## 关键代码/伪代码示例

### 1. 测试问题集

```python
eval_questions = [
    {
        "question": "这批合同有哪些主要风险？",
        "type": "global",
        "expected_points": ["付款风险", "违约责任", "交付延期"],
    },
    {
        "question": "供应商 A 涉及哪些合同和风险条款？",
        "type": "local",
        "expected_entities": ["供应商 A"],
    },
]
```

### 2. 运行多种检索模式

```python
def run_eval(question_item):
    question = question_item["question"]

    results = {
        "vector": ask_vector_rag(question),
        "local": ask_graphrag_local(question),
        "global": ask_graphrag_global(question),
        "hybrid": ask_graphrag_hybrid(question),
    }

    return results
```

### 3. 评分结构

```python
score = {
    "retrieval_relevance": 4,
    "answer_correctness": 4,
    "answer_completeness": 3,
    "source_accuracy": 5,
    "hallucination_risk": 1,
    "notes": "GraphRAG 找到了风险主题，但遗漏了保密条款。",
}
```

### 4. 失败案例记录

```python
failure_case = {
    "question": question,
    "mode": "hybrid",
    "problem": "实体匹配错误",
    "wrong_entity": "苹果",
    "expected_entity": "苹果公司",
    "fix": "增加实体类型和上下文消歧",
}
```

---

## 实际项目中怎么用

### 第一步：准备问题集

每类问题至少准备 5 个：

```text
事实问题
关系问题
全局总结问题
对比问题
路径问题
```

### 第二步：保存每次检索过程

建议保存：

```text
question
mode
matched_entities
retrieved_relations
retrieved_reports
retrieved_chunks
final_context
answer
sources
latency_ms
token_usage
```

### 第三步：对比普通 RAG 和 GraphRAG

重点看：

```text
跨文档问题 GraphRAG 是否更好？
全局总结问题 GraphRAG 是否更完整？
简单事实问题普通 RAG 是否更快？
```

### 第四步：按失败原因调优

常见失败原因和调优方向：

| 失败现象 | 可能原因 | 调优方向 |
| --- | --- | --- |
| 找错实体 | 实体消歧差 | 加 alias、加类型、加上下文判断 |
| 漏掉关系 | 抽取 prompt 太弱 | 改 prompt、增加关系类型示例 |
| 全局答案空泛 | 社区摘要太粗 | 调整社区粒度、摘要格式 |
| 答案编造 | 上下文证据不足 | 强化引用、要求基于证据回答 |
| 上下文太乱 | 召回太多 | 加重排、控制预算 |

---

## 容易混淆的点

### 1. 答案流畅不等于质量高

LLM 很会写顺滑文本，但可能没有事实依据。

### 2. 只评估最终答案不够

要同时看检索上下文。  
否则不知道是检索错了，还是生成错了。

### 3. GraphRAG 不一定每类问题都赢

简单事实问题上，普通 RAG 可能更快更准。

### 4. 评估集不能全是简单问题

如果只测简单事实问题，看不出 GraphRAG 的价值。  
要加入跨文档、全局总结、关系推理问题。

### 5. LLM 评分也需要人工抽查

LLM 评分方便，但不能完全替代人工检查。

---

## 学完后我应该能回答的问题

1. GraphRAG 要评估哪些层面？
2. 什么是检索质量？
3. 什么是答案忠实度？
4. 什么是图质量？
5. 什么是消融实验？
6. 为什么要对比普通 RAG 和 GraphRAG？
7. 测试问题集应该包含哪些类型？
8. 为什么要保存检索过程？
9. 全局答案空泛可能是什么原因？
10. 如何判断 GraphRAG 真的带来了价值？

下一篇：[16_FastAPI实现GraphRAG项目.md](16_FastAPI实现GraphRAG项目.md)

