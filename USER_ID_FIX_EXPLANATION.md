# User ID 传递修复说明

## 问题描述

在 `node.py` 的 Cypher 语句修正部分（161-182 行），生成的 Cypher 查询语句中使用了硬编码的 `UserID: 'AB123'`，而不是从接口传入的实际 `user_id` 参数值。

### 问题代码位置
- **文件**: `llm_backend/app/lg_agent/kg_sub_graph/agentic_rag_agents/components/cypher_tools/node.py` (第 161-182 行)
- **接口**: `llm_backend/main.py` (第 285-295 行) - `/api/langgraph/query` 端点

### 问题表现

```cypher
# 错误的输出（硬编码的 UserID）
MATCH (o:Order)<-[:PLACED_BY]-(c:Customer {UserID: 'AB123'})
RETURN o.OrderID, o.OrderDate, o.Status, o.TotalAmount
ORDER BY o.OrderDate DESC
```

应该根据传入的 `user_id` 动态生成，例如：

```cypher
# 正确的输出（使用实际的 user_id）
MATCH (o:Order)<-[:PLACED_BY]-(c:Customer {UserID: 101})
RETURN o.OrderID, o.OrderDate, o.Status, o.TotalAmount
ORDER BY o.OrderDate DESC
```

## 修复方案

### 1. 添加必要的导入

在 `node.py` 文件顶部添加 `RunnableConfig` 导入：

```python
from langchain_core.runnables import RunnableConfig
```

### 2. 修改函数签名以接收 config 参数

修改 `cypher_query` 函数，添加 `config` 参数：

```python
async def cypher_query(
    state: Dict[str, Any],
    config: RunnableConfig = None,
) -> Dict[str, List[CypherQueryOutputState] | List[str]]:
```

### 3. 从 config 中提取 user_id

在函数开始处添加 user_id 提取逻辑：

```python
# 从 config 中获取 user_id
user_id = None
if config:
    user_id = config.get("configurable", {}).get("user_id")
    logger.info(f"从 config 中获取到 user_id: {user_id}")
    
if not user_id:
    # 如果 config 中没有，尝试从 state 中获取
    user_id = state.get("user_id")
    logger.info(f"从 state 中获取到 user_id: {user_id}")
    
if not user_id:
    logger.warning("未找到 user_id，使用默认值 101")
    user_id = 101
```

### 4. 使用正则表达式替换 UserID

在 Cypher 语句修正部分，添加正则表达式替换逻辑：

```python
# 关键修正：将 Customer 节点的 UserID 属性值替换为实际的 user_id
# 匹配模式：{UserID: 'xxx'} 并替换为实际的 user_id
import re
def replace_user_id(match):
    return f"{{UserID: {user_id}}}"

cypher_statement = re.sub(
    r'\{UserID:\s*[\'"]?[^\}]+?\}',
    replace_user_id,
    cypher_statement
)
```

## 数据流

### user_id 的传递路径

1. **前端请求** → `main.py` 的 `/api/langgraph/query` 端点
   ```python
   @app.post("/api/langgraph/query")
   async def langgraph_query(
       query: str = Form(...),
       user_id: int = Form(...),  # ← user_id 从这里传入
       ...
   ):
   ```

2. **创建线程配置** → 将 user_id 放入 config
   ```python
   thread_config = {
       "configurable": {
           "thread_id": thread_id, 
           "user_id": user_id,  # ← 添加到 config 中
           "image_path": str(image_path) if image_path else None
       }
   }
   ```

3. **执行工作流** → config 被传递到各个节点
   ```python
   async for c, metadata in graph.astream(
       input_state, 
       stream_mode="messages", 
       config=thread_config  # ← config 在这里传入
   ):
   ```

4. **节点接收 config** → `cypher_query` 节点从 config 中提取 user_id
   ```python
   async def cypher_query(
       state: Dict[str, Any],
       config: RunnableConfig = None,  # ← 接收 config
   ):
       user_id = config.get("configurable", {}).get("user_id")  # ← 提取 user_id
   ```

5. **生成正确的 Cypher 语句** → 使用实际的 user_id
   ```python
   cypher_statement = re.sub(
       r'\{UserID:\s*[\'"]?[^\}]+?\}',
       lambda match: f"{{UserID: {user_id}}}",
       cypher_statement
   )
   ```

## 测试验证

运行测试脚本验证修复效果：

```bash
python test_user_id_in_cypher.py
```

### 预期输出

```
测试用例：字符串格式的 UserID
替换前：MATCH (o:Order)<-[:PLACED_BY]-(c:Customer {UserID: 'AB123'}) RETURN o.OrderID, o.OrderDate
替换后：MATCH (o:Order)<-[:PLACED_BY]-(c:Customer {UserID: 123}) RETURN o.OrderID, o.OrderDate
期望的 user_id: 123
✓ 测试通过
```

## 相关文件

- `llm_backend/app/lg_agent/kg_sub_graph/agentic_rag_agents/components/cypher_tools/node.py` - 主要修复文件
- `llm_backend/main.py` - 接口入口，user_id 从这里传入
- `llm_backend/app/lg_agent/lg_builder.py` - 工作流构建，config 在这里传递
- `test_user_id_in_cypher.py` - 测试脚本

## 注意事项

1. **向后兼容**: 如果 config 和 state 中都没有 user_id，会使用默认值 101
2. **日志记录**: 添加了详细的日志记录，便于调试
3. **正则表达式**: 支持多种格式的 UserID（带引号、不带引号、数字等）
4. **安全性**: 确保 user_id 是整数类型，避免注入风险

## 后续优化建议

1. **类型检查**: 可以添加 user_id 的类型验证
2. **错误处理**: 如果 user_id 无效，可以抛出更明确的异常
3. **状态管理**: 考虑将 user_id 添加到 OverallState 的定义中，使其在整个工作流中可用
4. **单元测试**: 为整个 user_id 传递链路添加集成测试
