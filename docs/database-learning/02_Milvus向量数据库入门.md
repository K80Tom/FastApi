# Milvus 向量数据库入门

> 第二阶段核心文档：理解向量检索原理，掌握 Milvus 基本操作，为入库任务打基础

---

## 学习目标

1. 理解"文本→向量→相似度搜索"的完整概念
2. 掌握 Milvus 的 Collection/Field/Index/Search 操作
3. 能用 pymilvus 完成创建集合、插入数据、搜索的全流程
4. 理解 Milvus 和 PG 通过 source_id 关联的设计模式

---

## 向量检索是什么

**核心思想**：把文本/图片变成一组数字（向量），意思相近的内容在数学空间中距离近。

```
"古风仙女角色" → [0.12, -0.45, 0.78, ..., 0.33]  (1536个数字)
"仙侠风格女性" → [0.11, -0.43, 0.76, ..., 0.31]  (距离很近 → 相似！)
"现代都市男性" → [0.89, 0.23, -0.56, ..., -0.12]  (距离很远 → 不相似)
```

**和关键词搜索的区别**：
| | 关键词搜索(PG/ES) | 语义搜索(Milvus) |
|---|---|---|
| 搜"仙女" | 只找包含"仙女"二字的 | 能找到"飘逸的女性仙侠角色" |
| 原理 | 字面匹配 | 理解含义 |
| 依赖 | 分词/倒排索引 | Embedding模型 |

---

## 核心概念

| 概念 | 解释 | 类比PG |
|------|------|--------|
| Collection | 存储向量的集合 | 表(Table) |
| Field | 集合中的字段 | 列(Column) |
| Schema | 集合的结构定义 | 表结构 |
| Vector Field | 存向量的字段(float数组) | 无对应(PG没有) |
| Primary Key | 唯一标识(int64/varchar) | 主键 |
| Index | 加速向量搜索的算法结构 | B-tree索引 |
| Metric Type | 相似度计算方式(余弦/L2/IP) | 无对应 |
| Partition | 数据分区，加速过滤 | 分区表 |

### 索引类型选择

| 索引 | 特点 | 适合场景 |
|------|------|---------|
| FLAT | 暴力搜索，100%准确 | 数据<1万条，开发测试 |
| IVF_FLAT | 聚类后搜索，较快较准 | 10万-100万条，平衡型 |
| HNSW | 图算法，快且准但内存大 | 需要高召回率，内存充足 |
| IVF_SQ8 | 量化压缩，省内存 | 数据量大，内存有限 |

### 相似度度量

| 类型 | 含义 | 使用场景 |
|------|------|---------|
| COSINE | 余弦相似度（方向相似性） | 文本语义检索（最常用） |
| L2 | 欧氏距离（绝对距离） | 图像特征 |
| IP | 内积 | 已归一化的向量 |

---

## 为你的项目设计 Milvus Schema

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

fields = [
    # 主键
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    # 向量字段（维度取决于embedding模型，OpenAI=1536, BGE=1024）
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),
    # 关联PG的关键字段
    FieldSchema(name="source_table", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="source_id", dtype=DataType.VARCHAR, max_length=64),
    # metadata（用于过滤）
    FieldSchema(name="asset_kind", dtype=DataType.VARCHAR, max_length=32),
    FieldSchema(name="source_project_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=256),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2048),
]

schema = CollectionSchema(fields, description="短剧资产向量集合")
```

**为什么这样设计：**
- `source_table + source_id`：检索后回查 PG 的桥梁
- `asset_kind`：过滤条件（只搜角色/只搜场景）
- `source_project_id`：按项目过滤
- `name + text`：Milvus 里存一份轻量文本，避免简单场景还要回查 PG

---

## 基础操作（pymilvus）

### 创建集合 + 索引

```python
from pymilvus import connections, Collection, utility

# 连接 Milvus
connections.connect(host="localhost", port="19530")

# 创建集合
collection = Collection(name="asset_vectors", schema=schema)

# 创建索引（必须在搜索前建好）
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {"M": 16, "efConstruction": 256}
}
collection.create_index(field_name="vector", index_params=index_params)

# 加载到内存（搜索前必须load）
collection.load()
```

### 插入数据

```python
import numpy as np

# 假设已经从PG取了数据并做了embedding
data = [
    # vector, source_table, source_id, asset_kind, source_project_id, name, text
    [[0.12, -0.45, ...],  # 1536维向量
    "asset_entities",
    "uuid-001",
    "character",
    "proj-001",
    "白衣仙女",
    "一个身穿白衣的古风仙女角色，气质飘逸"]
]

# 批量插入
collection.insert([
    [d[0] for d in data],  # vectors
    [d[1] for d in data],  # source_table
    [d[2] for d in data],  # source_id
    [d[3] for d in data],  # asset_kind
    [d[4] for d in data],  # source_project_id
    [d[5] for d in data],  # name
    [d[6] for d in data],  # text
])

# 插入后要flush才能被搜到
collection.flush()
```

### 搜索

```python
# 用户query转向量
query_vector = get_embedding("帮我找一个古风仙女")

# 搜索
results = collection.search(
    data=[query_vector],
    anns_field="vector",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=10,  # topK
    # 可选：metadata过滤
    expr='asset_kind == "character"',
    output_fields=["source_table", "source_id", "name", "text"]
)

# 解析结果
for hits in results:
    for hit in hits:
        print(f"分数: {hit.score:.4f}")
        print(f"名称: {hit.entity.get('name')}")
        print(f"source_id: {hit.entity.get('source_id')}")
        # 用 source_id 回查PG拿完整信息
```

### 删除与更新

```python
# 按source_id删除（资产从PG删除时同步删Milvus）
collection.delete(expr='source_id == "uuid-001"')

# 更新 = 先删后插（Milvus没有原生update）
collection.delete(expr='source_id == "uuid-001"')
collection.insert([new_data])
collection.flush()
```

---

## 和 PG 的关联模式

```
搜索请求 → Milvus返回: [{source_id: "uuid-001", score: 0.95}, ...]
                              ↓
PG回查: SELECT * FROM asset_entities WHERE id IN ('uuid-001', ...)
                              ↓
拼装完整结果返回前端
```

**关键设计**：Milvus 不存完整业务数据，只存向量+轻量metadata+source_id。完整信息永远从 PG 取。

---

## 高并发注意事项

1. **分片(Shard)**：数据量大时分多个shard并行搜索
2. **副本(Replica)**：读多写少时加副本分担搜索压力
3. **nprobe/ef 调优**：值越大越准但越慢，需要平衡
4. **预热**：collection.load() 后第一次搜索较慢，生产环境要预热
5. **批量操作**：插入时攒一批再insert，不要一条一条插

---

## 常见坑

1. **维度不匹配**：schema定义dim=1536，插入的向量不是1536维 → 报错
2. **忘记 load()**：创建完collection不load就搜索 → 报错
3. **忘记建索引**：没索引也能搜但极慢（暴力扫描）
4. **忘记 flush()**：插入后不flush，数据在内存没落盘，搜不到
5. **expr 语法错误**：过滤表达式的字符串值要用双引号
6. **数据量太小**：几十条数据时向量检索没优势，效果看起来差

---

## 实战练习

1. 用 pymilvus 创建 asset_vectors 集合（按上面的schema）
2. 手动插入5条测试数据（可以用随机向量），验证搜索能返回结果
3. 加上 expr 过滤，只搜 character 类型的资产
4. 实现删除：给定 source_id，从 Milvus 删除对应记录

---

## 学完应能回答

- 向量检索和关键词搜索的区别是什么？
- Milvus 的 Collection/Field/Index 分别对应 PG 的什么？
- 为什么 Milvus 里要存 source_table 和 source_id？
- HNSW 和 IVF_FLAT 索引怎么选？
- 为什么搜索前必须 load()？插入后必须 flush()？
- 如果要更新一条已入库的资产向量，步骤是什么？
