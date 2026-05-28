# LangGraph 接口对话保存修复

## 🔍 问题描述

### 现象
访问 `/api/langgraph/query` 接口后，聊天窗口的数据没有被保存到数据库，而 `/api/chat` 接口可以正常保存。

### 原因分析

**对比两个接口的实现：**

#### ✅ `/api/chat` (正常工作)
```python
@app.post("/api/chat")
async def chat_endpoint(request: ChatMessage):
    chat_service = LLMFactory.create_chat_service()
    
    return StreamingResponse(
        chat_service.generate_stream(
            messages=request.messages,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            on_complete=ConversationService.save_message  # ← 有关键的回调函数
        ),
        media_type="text/event-stream"
    )
```

**关键点：** 通过 `on_complete=ConversationService.save_message` 参数，在流式响应完成后自动保存对话。

#### ❌ `/api/langgraph/query` (修复前)
```python
@app.post("/api/langgraph/query")
async def langgraph_query(...):
    # ... 处理逻辑
    
    async def process_stream():
        async for c, metadata in graph.astream(...):
            # 流式输出内容
            yield f"data: {content_json}\n\n"
    
    return StreamingResponse(process_stream(), media_type="text/event-stream")
```

**问题：** 
- ❌ 没有调用 `ConversationService.save_message`
- ❌ 没有收集完整的响应内容
- ❌ 没有在响应完成后保存数据

---

## ✅ 修复方案

### 核心思路

1. **收集响应**: 在流式输出时收集完整的 AI 回复内容
2. **保存数据**: 在响应完成后调用 `ConversationService.save_message`
3. **异常处理**: 添加 try-except 确保保存失败不影响主流程

### 修复代码

#### 1. 现有会话（resume 模式）

```python
if state_history and len(state_history) > 0 and len(state_history[-1]) > 0:
    logger.info("Using existing conversation state")
    
    # 收集完整响应内容
    full_response = []
    
    async def process_stream():
        async for c, metadata in graph.astream(
            Command(resume=query), 
            stream_mode="messages", 
            config=thread_config
        ):
            if c.content and "research_plan" not in metadata.get("tags", []) and not c.additional_kwargs.get("tool_calls"):
                content_json = json.dumps(c.content, ensure_ascii=False)
                full_response.append(c.content)  # ← 收集响应
                yield f"data: {content_json}\n\n"
                
            elif c.additional_kwargs.get("tool_calls"):
                tool_data = c.additional_kwargs.get("tool_calls")[0]["function"].get("arguments")
                logger.debug(f"Tool call: {tool_data}")
        
        # 处理中断情况
        state = graph.get_state(thread_config)
        if len(state) > 0 and len(state[-1]) > 0:
            if len(state[-1][0].interrupts) > 0:
                interrupt_json = json.dumps({"interruption": True, "conversation_id": thread_id})
                yield f"data: {interrupt_json}\n\n"
        
        # ← 新增：保存对话到数据库
        if full_response:
            try:
                messages = [{"role": "user", "content": query}]
                response_text = "".join(full_response)
                
                await ConversationService.save_message(
                    user_id=user_id,
                    conversation_id=int(thread_id),
                    messages=messages,
                    response=response_text
                )
                logger.info(f"Saved LangGraph conversation for user {user_id}, conversation {thread_id}")
            except Exception as e:
                logger.error(f"Failed to save LangGraph conversation: {e}")
```

#### 2. 新会话（初始模式）

```python
else:
    logger.info("Creating new conversation state")
    
    from langchain_core.messages import HumanMessage
    input_messages = [HumanMessage(content=query)]
    input_state = InputState(messages=input_messages)
    
    # 收集完整响应内容
    full_response = []
    
    async def process_stream():
        async for c, metadata in graph.astream(
            input_state, 
            stream_mode="messages", 
            config=thread_config
        ):
            if c.content and "research_plan" not in metadata.get("tags", []) and not c.additional_kwargs.get("tool_calls"):
                content_json = json.dumps(c.content, ensure_ascii=False)
                full_response.append(c.content)  # ← 收集响应
                yield f"data: {content_json}\n\n"
                
            elif c.additional_kwargs.get("tool_calls"):
                tool_data = c.additional_kwargs.get("tool_calls")[0]["function"].get("arguments")
                logger.debug(f"Tool call: {tool_data}")
        
        # 处理中断情况
        state = graph.get_state(thread_config)
        if len(state) > 0 and len(state[-1]) > 0:
            if len(state[-1][0].interrupts) > 0:
                interrupt_json = json.dumps({"interruption": True, "conversation_id": thread_id})
                yield f"data: {interrupt_json}\n\n"
        
        # ← 新增：保存对话到数据库
        if full_response:
            try:
                messages = [{"role": "user", "content": query}]
                response_text = "".join(full_response)
                
                await ConversationService.save_message(
                    user_id=user_id,
                    conversation_id=int(thread_id),
                    messages=messages,
                    response=response_text
                )
                logger.info(f"Saved LangGraph conversation for user {user_id}, conversation {thread_id}")
            except Exception as e:
                logger.error(f"Failed to save LangGraph conversation: {e}")
```

---

## 📊 数据流对比

### 修复前

```
用户请求 → LangGraph 处理 → 流式返回前端
                          ↓
                      ❌ 没有保存
```

### 修复后

```
用户请求 → LangGraph 处理 → 流式返回前端
                          ↓
                    收集完整响应
                          ↓
                    保存到数据库
                          ↓
                      ✅ 完成
```

---

## 🔧 关键改动

### 1. 添加响应收集器

```python
full_response = []  # ← 初始化列表用于收集响应

# 在流式处理中
full_response.append(c.content)  # ← 逐块收集
```

### 2. 在流式完成后保存

```python
# 在 process_stream 函数的最后
if full_response:
    try:
        # 构建消息
        messages = [{"role": "user", "content": query}]
        response_text = "".join(full_response)  # ← 拼接完整响应
        
        # 调用保存服务
        await ConversationService.save_message(
            user_id=user_id,
            conversation_id=int(thread_id),
            messages=messages,
            response=response_text
        )
    except Exception as e:
        logger.error(f"Failed to save LangGraph conversation: {e}")
```

### 3. 类型转换

```python
conversation_id=int(thread_id)  # ← thread_id 是字符串，需要转换为 int
```

---

## 🧪 测试验证

### 测试步骤

1. **启动后端服务**
   ```bash
   cd llm_backend
   python main.py
   ```

2. **发送测试请求**
   ```bash
   curl -X POST "http://localhost:8000/api/langgraph/query" \
     -F "query=我的订单状态" \
     -F "user_id=101" \
     -F "conversation_id="
   ```

3. **检查数据库**
   ```sql
   -- 查看会话表
   SELECT * FROM conversations WHERE user_id = 101 ORDER BY created_at DESC LIMIT 1;
   
   -- 查看消息表
   SELECT * FROM messages WHERE conversation_id = (
       SELECT id FROM conversations WHERE user_id = 101 ORDER BY created_at DESC LIMIT 1
   );
   ```

4. **预期结果**
   - ✅ conversations 表中创建了新记录
   - ✅ messages 表中有两条记录（用户问题和 AI 回答）
   - ✅ 前端聊天窗口显示完整对话历史

---

## 📝 注意事项

### 1. 线程安全

```python
# full_response 在异步函数中使用是安全的
# 因为每个请求都有独立的 process_stream 实例
full_response = []
```

### 2. 错误处理

```python
# 保存失败不应该影响主流程
try:
    await ConversationService.save_message(...)
except Exception as e:
    logger.error(f"Failed to save: {e}")  # ← 只记录日志，不抛出异常
```

### 3. 性能考虑

```python
# 保存操作在流式完成后执行，不会阻塞流式输出
# 异步数据库操作，不会阻塞其他请求
await ConversationService.save_message(...)
```

### 4. 会话 ID 处理

```python
# thread_id 可能是 UUID 字符串，需要转换为 int
conversation_id=int(thread_id)

# 如果 thread_id 不是有效的整数，可能需要特殊处理
# 例如使用 hash 或者单独存储 UUID 映射
```

---

## 🎯 与 /api/chat 的对比

| 特性 | /api/chat | /api/langgraph/query (修复后) |
|------|-----------|-------------------------------|
| 流式输出 | ✅ | ✅ |
| 自动保存 | ✅ (通过回调) | ✅ (手动实现) |
| 保存时机 | 回调函数 | 流式完成后 |
| 错误处理 | 内置 | 自定义 |
| 支持多轮 | ✅ | ✅ |
| 支持工具调用 | ❌ | ✅ |
| 支持 GraphRAG | ❌ | ✅ |

---

## 💡 优化建议

### 1. 统一保存逻辑

可以提取一个公共的保存函数：

```python
async def save_langgraph_conversation(
    user_id: int,
    conversation_id: str,
    query: str,
    full_response: List[str]
):
    """统一的 LangGraph 对话保存函数"""
    if not full_response:
        return
    
    try:
        messages = [{"role": "user", "content": query}]
        response_text = "".join(full_response)
        
        await ConversationService.save_message(
            user_id=user_id,
            conversation_id=int(conversation_id),
            messages=messages,
            response=response_text
        )
        logger.info(f"Saved conversation for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to save: {e}")
```

然后在两个地方调用：

```python
# 在 process_stream 结束时
await save_langgraph_conversation(user_id, thread_id, query, full_response)
```

### 2. 支持历史消息

如果需要保存完整的对话历史（包括之前的多轮对话）：

```python
# 从 state 中获取历史消息
history_messages = []
if state_history:
    # 提取历史消息
    for msg in state_history[-1].values:
        if hasattr(msg, 'content'):
            history_messages.append({
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content
            })

# 添加当前查询和回答
history_messages.append({"role": "user", "content": query})
history_messages.append({"role": "assistant", "content": response_text})

# 保存完整历史
await ConversationService.save_message(
    user_id=user_id,
    conversation_id=int(thread_id),
    messages=history_messages,
    response=response_text
)
```

### 3. 批量保存优化

对于高频使用的场景，可以考虑批量保存：

```python
# 使用队列缓冲多个请求
from asyncio import Queue

save_queue = Queue(maxsize=100)

async def batch_save_worker():
    """批量保存工作协程"""
    while True:
        batch = []
        while not save_queue.empty() and len(batch) < 10:
            batch.append(await save_queue.get())
        
        if batch:
            await bulk_save_to_database(batch)
```

---

## 📋 总结

### 问题根源
- `/api/langgraph/query` 没有保存对话数据的逻辑

### 解决方案
- 在流式响应过程中收集完整内容
- 在响应完成后调用 `ConversationService.save_message`

### 关键代码
- `full_response.append(c.content)` - 收集响应
- `await ConversationService.save_message(...)` - 保存数据

### 测试验证
- 检查数据库表是否有新记录
- 前端是否正确显示对话历史

---

*修复日期：2026-03-14*  
*涉及文件：llm_backend/main.py*  
*影响接口：/api/langgraph/query*
