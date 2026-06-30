# Redis 缓存与检索优化

> 第三阶段文档：理解缓存在检索链路中的作用，掌握 Redis 基础操作和缓存策略设计

---

## 学习目标

1. 理解为什么检索链路需要缓存层
2. 掌握 Redis 五大数据结构和常用命令
3. 能为搜索接口设计缓存策略
4. 理解缓存穿透/击穿/雪崩及解决方案

---

## 为什么需要 Redis

没有缓存时的问题：
```
用户搜索"古风仙女" → embedding(200ms) → Milvus检索(50ms) → 回查PG(30ms) = 280ms
如果1000人同时搜同一个热门词 → Milvus和PG各承受1000次请求
```

加了 Redis：
```
用户搜索"古风仙女" → Redis查缓存(1ms) → 命中！直接返回
第一个人的请求走完整链路(280ms)，后续999人直接读缓存(1ms)
```

**核心价值**：用内存换时间，用空间换并发能力。

---

## Redis 数据结构与 Agent 场景

| 结构 | 命令 | 在你项目中的用途 |
|------|------|-----------------|
| String | GET/SET/SETEX | 缓存搜索结果JSON、缓存embedding向量 |
| Hash | HSET/HGET/HGETALL | 缓存单个资产的多个字段 |
| List | LPUSH/LRANGE | 最近搜索历史 |
| Set | SADD/SISMEMBER | 已入库的source_id集合（防重复） |
| ZSet | ZADD/ZRANGEBYSCORE | 资产热度排行榜 |

---

## 在检索链路中的缓存设计

```python
import redis
import json
import hashlib

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def search_with_cache(query: str, asset_kind: str = None, top_k: int = 10):
    # 1. 生成缓存key（对query+过滤条件做hash）
    cache_input = f"{query}:{asset_kind}:{top_k}"
    cache_key = f"search:{hashlib.md5(cache_input.encode()).hexdigest()}"
    
    # 2. 查缓存
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)  # 命中，直接返回
    
    # 3. 未命中，走完整检索链路
    results = full_search_pipeline(query, asset_kind, top_k)
    
    # 4. 结果写入缓存，TTL 5分钟
    r.setex(cache_key, 300, json.dumps(results, ensure_ascii=False))
    
    return results
```

### 缓存 Embedding 结果（省钱）

```python
def get_embedding_cached(text: str) -> list:
    """embedding API按token计费，缓存避免重复调用"""
    cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
    
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    vector = call_embedding_api(text)
    r.setex(cache_key, 86400, json.dumps(vector))  # 缓存24小时
    return vector
```

### 缓存失效策略

| 事件 | 操作 |
|------|------|
| 资产被修改 | 删除该资产相关的所有搜索缓存 |
| 资产被删除 | 同上 |
| 定时过期 | TTL 5分钟自动失效 |
| 全量重跑入库 | 清空所有 search:* 缓存 |

```python
def invalidate_asset_cache(asset_id: str):
    """资产更新时清除相关缓存"""
    # 方案1：清除所有搜索缓存（简单粗暴）
    keys = r.keys("search:*")
    if keys:
        r.delete(*keys)
    
    # 方案2：只清除包含该资产的缓存（需要维护反向索引，复杂但精准）
```

---

## 缓存三大经典问题

| 问题 | 场景 | 解决 |
|------|------|------|
| **穿透** | 搜索一个肯定不存在的东西，每次都打到Milvus+PG | 缓存空结果(TTL短)；布隆过滤器预判 |
| **击穿** | 热门搜索词缓存刚好过期，瞬间大量请求打到后端 | 互斥锁(只让一个请求回源)；热点key永不过期 |
| **雪崩** | 大量key同时过期，后端被打爆 | TTL加随机偏移(300±60s)；多级缓存 |

```python
# 防击穿：互斥锁方案
def search_with_mutex(query: str):
    cache_key = f"search:{hash(query)}"
    lock_key = f"lock:{cache_key}"
    
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 尝试获取锁（只有一个请求能拿到）
    if r.set(lock_key, "1", nx=True, ex=10):
        try:
            results = full_search_pipeline(query)
            r.setex(cache_key, 300, json.dumps(results))
            return results
        finally:
            r.delete(lock_key)
    else:
        # 没拿到锁，等一下再读缓存
        time.sleep(0.1)
        return json.loads(r.get(cache_key) or "[]")
```

---

## 高并发注意事项

1. **连接池**：用 redis.ConnectionPool，不要每次请求新建连接
2. **Pipeline**：批量操作时用pipeline减少网络往返
3. **大key避免**：搜索结果JSON不要太大（>1MB拆分或压缩）
4. **内存监控**：设置 maxmemory + 淘汰策略(allkeys-lru)
5. **序列化**：用 json 而不是 pickle，兼容性好且可调试

---

## 常见坑

1. **忘记设TTL**：缓存永不过期，数据更新后一直返回旧结果
2. **缓存和DB不一致**：更新PG后忘记清Redis → 用户看到过时数据
3. **key命名混乱**：没有统一前缀，无法批量管理 → 规范如 `search:{hash}`, `emb:{hash}`
4. **热key打爆单节点**：一个超热门搜索词 → 本地缓存(进程内)+Redis双层

---

## 实战练习

1. 为搜索接口加 Redis 缓存，对比加缓存前后的响应时间
2. 实现 embedding 缓存，统计命中率
3. 模拟缓存击穿场景，实现互斥锁方案
4. 设计缓存key命名规范文档

---

## 学完应能回答

- 检索链路中 Redis 缓存放在哪一层？缓存什么？
- 缓存穿透和缓存击穿有什么区别？分别怎么解决？
- 资产数据更新后缓存怎么处理？
- 为什么要缓存 embedding 结果？能省多少钱？
- Redis 的 TTL 设多长合适？怎么决定？
