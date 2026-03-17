# 第二阶段：ChromaDB 长期记忆 + FAISS RAG 集成

## 🎯 目标

1. ✅ **修复 FAISS RAG** - 让已有的 embedding_service 真正被使用
2. ✅ **添加 ChromaDB** - 实现长期记忆功能
3. ✅ **集成到 LangGraph** - 在工作流中自动检索相关上下文

---

## 📋 第一部分：修复 FAISS RAG 的使用

### 🔍 问题分析

当前状态：
- ✅ `embedding_service.py` 已创建（175 行代码）
- ✅ 支持 PDF 文档向量化
- ✅ 使用 FAISS 做相似度搜索
- ❌ **没有任何地方调用它！**

### ✅ 解决方案：创建 RAG 查询接口

#### 步骤 1: 创建 RAG 服务层

新建文件：`llm_backend/app/services/rag_service.py`

```python
from typing import List, Dict, Optional
from app.services.embedding_service import EmbeddingService
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(service="rag_service")

class RAGService:
    """文档 RAG 服务"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm = ChatDeepSeek(
            api_key=settings.DEEPSEEK_API_KEY,
            model_name=settings.DEEPSEEK_MODEL,
            temperature=0.7
        )
        
        # RAG 提示模板
        self.rag_prompt = ChatPromptTemplate.from_template("""
你是一个智能助手，基于提供的文档片段回答用户问题。

可用的文档片段：
{context}

用户问题：{question}

如果文档片段中有答案，请详细回答；如果没有相关信息，请诚实地说明。
""")
    
    async def load_index(self, index_id: str) -> bool:
        """加载指定的索引"""
        try:
            self.embedding_service._load_index(index_id)
            logger.info(f"成功加载索引：{index_id}")
            return True
        except Exception as e:
            logger.error(f"加载索引失败：{e}")
            return False
    
    async def query_documents(self, 
                             query: str, 
                             top_k: int = 3,
                             index_id: Optional[str] = None) -> Dict:
        """查询相关文档并生成回答"""
        
        # 1. 如果有指定索引 ID，先加载
        if index_id:
            await self.load_index(index_id)
        
        # 2. 搜索相关文档
        try:
            results = await self.embedding_service.search(query, top_k=top_k)
            
            if not results:
                return {
                    "answer": "抱歉，没有找到相关的文档信息。",
                    "sources": []
                }
            
            # 3. 构建上下文
            context = "\n\n".join([
                f"[片段{i+1}] (相关度：{r['score']:.4f})\n{r['content']}"
                for i, r in enumerate(results)
            ])
            
            # 4. 使用 LLM 生成回答
            rag_chain = self.rag_prompt | self.llm
            
            response = await rag_chain.ainvoke({
                "context": context,
                "question": query
            })
            
            # 5. 返回结果
            return {
                "answer": response.content,
                "sources": [
                    {
                        "content": r["content"],
                        "metadata": r["metadata"],
                        "score": r["score"]
                    }
                    for r in results
                ]
            }
            
        except Exception as e:
            logger.error(f"RAG 查询失败：{e}", exc_info=True)
            return {
                "answer": f"查询出错：{str(e)}",
                "sources": []
            }
    
    async def upload_document(self, file_path: str) -> Dict:
        """上传文档并创建索引"""
        try:
            result = await self.embedding_service.create_embeddings(
                file_path=file_path,
                index_dir="indexes"
            )
            
            logger.info(f"文档上传成功：{file_path}")
            return {
                "status": "success",
                "index_id": result["index_id"],
                "chunks": result["chunks"]
            }
            
        except Exception as e:
            logger.error(f"文档上传失败：{e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

# 全局单例
rag_service = RAGService()
```

#### 步骤 2: 添加 API 接口

修改文件：`llm_backend/main.py`

在适当位置添加以下接口（放在 `/api/langgraph/query` 后面）：

```python
from app.services.rag_service import rag_service

@app.post("/api/rag/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到 RAG 系统"""
    try:
        # 保存临时文件
        temp_path = Path("uploads/temp") / file.filename
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        # 创建索引
        result = await rag_service.upload_document(str(temp_path))
        
        # 清理临时文件
        temp_path.unlink()
        
        return result
        
    except Exception as e:
        logger.error(f"上传失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/query")
async def rag_query(
    query: str = Form(...),
    index_id: Optional[str] = Form(None),
    top_k: int = Form(default=3)
):
    """查询文档 RAG"""
    result = await rag_service.query_documents(query, top_k=top_k, index_id=index_id)
    return result
```

#### 步骤 3: 测试 FAISS RAG

创建测试脚本：`test_faiss_rag.py`

```python
import asyncio
from app.services.rag_service import rag_service

async def test_rag():
    # 1. 上传文档
    print("上传文档...")
    result = await rag_service.upload_document("test_doc.pdf")
    print(f"上传结果：{result}")
    
    # 2. 查询文档
    print("\n查询文档...")
    query_result = await rag_service.query_documents(
        query="你的问题",
        index_id=result["index_id"]
    )
    
    print(f"\n回答：{query_result['answer']}")
    print(f"\n来源数量：{len(query_result['sources'])}")

if __name__ == "__main__":
    asyncio.run(test_rag())
```

---

## 📋 第二部分：添加 ChromaDB 长期记忆

### 🛠️ 安装依赖

```bash
pip install chromadb langchain-chroma
```

### 步骤 1: 创建 ChromaDB 服务

新建文件：`llm_backend/app/services/chroma_memory_service.py`

```python
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from app.core.config import settings
from app.core.logger import get_logger
import hashlib

logger = get_logger(service="chroma_memory")

class ChromaMemoryService:
    """ChromaDB 长期记忆服务"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "conversation_history",
        embedding_model: str = "nomic-embed-text"
    ):
        # 初始化 ChromaDB
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )
        
        # 初始化嵌入模型
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=settings.OLLAMA_BASE_URL
        )
        
        logger.info(f"ChromaDB 初始化完成，集合：{collection_name}")
    
    def _generate_id(self, user_id: int, content: str, timestamp: str) -> str:
        """生成唯一的记忆 ID"""
        key = f"{user_id}:{content}:{timestamp}"
        return hashlib.md5(key.encode()).hexdigest()
    
    async def add_memory(
        self,
        user_id: int,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """添加一条记忆"""
        try:
            timestamp = datetime.now().isoformat()
            memory_id = self._generate_id(user_id, content, timestamp)
            
            # 准备元数据
            memory_metadata = {
                "user_id": str(user_id),
                "timestamp": timestamp,
                "type": "conversation",
                **(metadata or {})
            }
            
            # 添加到 ChromaDB
            self.collection.add(
                documents=[content],
                metadatas=[memory_metadata],
                ids=[memory_id]
            )
            
            logger.info(f"添加记忆：{memory_id[:8]}...")
            return memory_id
            
        except Exception as e:
            logger.error(f"添加记忆失败：{e}", exc_info=True)
            raise
    
    async def search_memories(
        self,
        user_id: int,
        query: str,
        top_k: int = 5,
        time_range_days: Optional[int] = None
    ) -> List[Dict]:
        """搜索相关记忆"""
        try:
            # 生成查询向量并搜索
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": str(user_id)}
            )
            
            # 处理结果
            memories = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    memory = {
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    }
                    
                    # 时间范围过滤
                    if time_range_days:
                        memory_time = datetime.fromisoformat(memory['metadata']['timestamp'])
                        cutoff_time = datetime.now() - timedelta(days=time_range_days)
                        if memory_time < cutoff_time:
                            continue
                    
                    memories.append(memory)
            
            logger.info(f"找到 {len(memories)} 条相关记忆")
            return memories
            
        except Exception as e:
            logger.error(f"搜索记忆失败：{e}", exc_info=True)
            return []
    
    async def get_user_memories(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """获取用户的所有记忆"""
        try:
            results = self.collection.get(
                where={"user_id": str(user_id)},
                limit=limit,
                offset=offset,
                include=["documents", "metadatas"]
            )
            
            memories = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    memories.append({
                        "content": doc,
                        "metadata": results['metadatas'][i],
                        "id": results['ids'][i]
                    })
            
            return memories
            
        except Exception as e:
            logger.error(f"获取记忆失败：{e}", exc_info=True)
            return []
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除指定记忆"""
        try:
            self.collection.delete(ids=[memory_id])
            logger.info(f"删除记忆：{memory_id[:8]}...")
            return True
        except Exception as e:
            logger.error(f"删除记忆失败：{e}")
            return False
    
    async def cleanup_old_memories(
        self,
        user_id: int,
        days_to_keep: int = 30,
        max_memories: int = 1000
    ) -> int:
        """清理过期记忆"""
        try:
            # 获取所有记忆
            all_memories = await self.get_user_memories(user_id, limit=max_memories * 2)
            
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 按时间排序
            sorted_memories = sorted(
                all_memories,
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=True
            )
            
            # 删除超期的记忆
            for memory in sorted_memories[max_memories:]:
                memory_time = datetime.fromisoformat(memory['metadata']['timestamp'])
                if memory_time < cutoff_date:
                    if await self.delete_memory(memory['id']):
                        deleted_count += 1
            
            logger.info(f"清理了 {deleted_count} 条过期记忆")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理记忆失败：{e}")
            return 0

# 全局单例
chroma_memory = ChromaMemoryService()
```

---

## 📋 第三部分：集成到 LangGraph 工作流

### 步骤 1: 创建记忆检索节点

新建文件：`llm_backend/app/lg_agent/kg_sub_graph/agentic_rag_agents/components/memory_retrieval/node.py`

```python
from typing import Any, Dict, List
from app.services.chroma_memory_service import chroma_memory
from app.core.logger import get_logger

logger = get_logger(service="memory_retrieval")

async def retrieve_relevant_memories(state: Dict[str, Any]) -> Dict[str, Any]:
    """检索相关的长期记忆"""
    try:
        # 从 state 中获取必要信息
        question = state.get("question", "")
        user_id = state.get("user_id")
        
        if not user_id:
            logger.warning("未提供 user_id，跳过记忆检索")
            return {"long_term_memories": []}
        
        # 搜索相关记忆
        memories = await chroma_memory.search_memories(
            user_id=user_id,
            query=question,
            top_k=3,
            time_range_days=30  # 只查找最近 30 天的记忆
        )
        
        # 提取记忆内容
        memory_contents = [m["content"] for m in memories]
        
        logger.info(f"为用户 {user_id} 检索到 {len(memory_contents)} 条相关记忆")
        
        return {
            "long_term_memories": memory_contents,
            "memory_context": "\n\n".join([
                f"[历史记忆] {content}"
                for content in memory_contents
            ])
        }
        
    except Exception as e:
        logger.error(f"记忆检索失败：{e}", exc_info=True)
        return {
            "long_term_memories": [],
            "memory_context": ""
        }
```

### 步骤 2: 修改工作流以包含记忆检索

修改文件：`llm_backend/app/lg_agent/lg_builder.py`

在 `create_research_plan` 函数中添加记忆检索：

```python
async def create_research_plan(
    state: AgentState, *, config: RunnableConfig
) -> Dict[str, List[str] | str]:
    """通过查询本地知识库回答客户问题"""
    logger.info("------execute local knowledge base query------")
    
    # ← 新增：在任务分解前先检索长期记忆
    from app.lg_agent.kg_sub_graph.agentic_rag_agents.components.memory_retrieval.node import retrieve_relevant_memories
    
    memory_result = await retrieve_relevant_memories(state)
    
    # 将记忆添加到 state 中
    enhanced_state = {**state, **memory_result}
    
    # ... 后续逻辑不变
    # 使用增强后的 state 进行任务分解
```

### 步骤 3: 在对话结束时保存记忆

修改文件：`llm_backend/main.py` 中的 `/api/langgraph/query` 接口

在保存对话的地方同时保存到 ChromaDB：

```python
from app.services.chroma_memory_service import chroma_memory

# 在保存对话后添加：
await ConversationService.save_message(...)

# ← 新增：保存到长期记忆
important_content = response_text  # AI 的回答
await chroma_memory.add_memory(
    user_id=user_id,
    content=important_content,
    metadata={
        "query": query,
        "conversation_id": str(thread_id),
        "type": "qa_pair"  # 标记为问答对
    }
)
```

---

## 📋 第四部分：API 接口和使用示例

### 添加记忆管理 API

修改文件：`llm_backend/main.py`

```python
@app.post("/api/memory/add")
async def add_memory(
    content: str = Form(...),
    user_id: int = Form(...)
):
    """添加记忆"""
    memory_id = await chroma_memory.add_memory(user_id, content)
    return {"memory_id": memory_id, "status": "success"}

@app.get("/api/memory/search")
async def search_memory(
    query: str,
    user_id: int,
    top_k: int = 5
):
    """搜索记忆"""
    memories = await chroma_memory.search_memories(user_id, query, top_k)
    return {"memories": memories}

@app.get("/api/memory/user/{user_id}")
async def get_user_memories(
    user_id: int,
    limit: int = 100
):
    """获取用户的所有记忆"""
    memories = await chroma_memory.get_user_memories(user_id, limit)
    return {"memories": memories}

@app.delete("/api/memory/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆"""
    success = await chroma_memory.delete_memory(memory_id)
    return {"status": "success" if success else "failed"}
```

---

## 🧪 测试和验证

### 1. 测试 FAISS RAG

```bash
# 1. 启动服务
cd llm_backend
python main.py

# 2. 上传文档
curl -X POST "http://localhost:8000/api/rag/upload" \
  -F "file=@/path/to/your/document.pdf"

# 3. 查询
curl -X POST "http://localhost:8000/api/rag/query" \
  -F "query=文档中的问题" \
  -F "index_id=返回的 index_id"
```

### 2. 测试 ChromaDB 记忆

```bash
# 1. 添加记忆
curl -X POST "http://localhost:8000/api/memory/add" \
  -F "content=用户说他想买智能灯泡，预算 200 元" \
  -F "user_id=101"

# 2. 搜索记忆
curl -X GET "http://localhost:8000/api/memory/search?query=想买什么&user_id=101&top_k=3"

# 3. 在 LangGraph 查询中自动使用记忆
curl -X POST "http://localhost:8000/api/langgraph/query" \
  -F "query=我之前说的那个东西怎么样？" \
  -F "user_id=101"
```

---

## 📊 完整架构图

```
┌─────────────────────────────────────────┐
│          用户请求                        │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   /api/langgraph/query                  │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   LangGraph 工作流                       │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 1. 记忆检索节点                 │   │
│  │    - 从 ChromaDB 检索相关记忆    │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │ 2. Planner 任务分解             │   │
│  │    - 结合短期记忆 + 长期记忆     │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │ 3. Tool Selection               │   │
│  │    - Cypher 查询                │   │
│  │    - FAISS RAG 查询 ←───────────┼───┤
│  │    - GraphRAG 查询              │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │ 4. 生成回答                     │   │
│  └──────────────┬──────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
                  ↓
      ┌───────────┴───────────┐
      │                       │
      ↓                       ↓
┌───────────┐         ┌───────────┐
│ 保存到 DB  │         │ 保存到    │
│ (对话表)  │         │ ChromaDB  │
└───────────┘         └───────────┘
```

---

## ✅ 检查清单

### FAISS RAG 部分
- [ ] 创建 `rag_service.py`
- [ ] 在 `main.py` 中添加 `/api/rag/upload` 和 `/api/rag/query` 接口
- [ ] 测试文档上传和查询
- [ ] 验证回答质量

### ChromaDB 部分
- [ ] 安装 `chromadb` 和 `langchain-chroma`
- [ ] 创建 `chroma_memory_service.py`
- [ ] 添加记忆管理 API
- [ ] 测试记忆的添加和检索

### LangGraph 集成
- [ ] 创建 `memory_retrieval/node.py`
- [ ] 修改 `lg_builder.py` 添加记忆检索节点
- [ ] 在 `main.py` 中保存对话时同步到 ChromaDB
- [ ] 端到端测试完整流程

---

## 🎯 预期效果

### 使用前：
```
用户："我上周说的那个产品"
Agent："请问您说的是什么产品？"
```

### 使用后：
```
用户："我上周说的那个产品"
Agent："您上次提到想购买智能灯泡，预算 200 元左右。
       我为您推荐以下几款..."
```

---

*实施时间：预计 1-2 天*  
*技术栈：FAISS + ChromaDB + LangGraph*
