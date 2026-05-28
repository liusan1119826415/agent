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
        # 初始化 ChromaDB 客户端
        try:
            self.client = chromadb.Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                is_persistent=True
            ))
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
            
            logger.info(f"ChromaDB 初始化成功，集合：{collection_name}")
        except Exception as e:
            logger.error(f"ChromaDB 初始化失败：{e}", exc_info=True)
            raise
        
        # 初始化嵌入模型（使用 Ollama）
        try:
            self.embeddings = OllamaEmbeddings(
                model=embedding_model,
                base_url=settings.OLLAMA_BASE_URL
            )
            logger.info(f"嵌入模型初始化成功：{embedding_model}")
        except Exception as e:
            logger.warning(f"Ollama 嵌入模型初始化失败，将使用备用方案：{e}")
            # 备用方案：使用 SentenceTransformer
            from sentence_transformers import SentenceTransformer
            self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.embeddings = None
    
    def _generate_id(self, user_id: int, content: str, timestamp: str) -> str:
        """生成唯一的记忆 ID"""
        key = f"{user_id}:{content[:50]}:{timestamp}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_embedding_vector(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        if self.embeddings:
            # 使用 Ollama
            return self.embeddings.embed_query(text)
        else:
            # 使用 SentenceTransformer（备用方案）
            vector = self.embeddings_model.encode(text)
            return vector.tolist()
    
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
            
            logger.info(f"✓ 添加记忆：{memory_id[:8]}... | 用户：{user_id} | 内容：{content[:30]}...")
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
                        try:
                            memory_time = datetime.fromisoformat(memory['metadata']['timestamp'])
                            cutoff_time = datetime.now() - timedelta(days=time_range_days)
                            if memory_time < cutoff_time:
                                continue
                        except:
                            pass  # 如果时间解析失败，不过滤
                    
                    memories.append(memory)
            
            logger.info(f"🔍 为用户 {user_id} 找到 {len(memories)} 条相关记忆 (查询：{query[:20]}...)")
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
            logger.info(f"✓ 删除记忆：{memory_id[:8]}...")
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
                try:
                    memory_time = datetime.fromisoformat(memory['metadata']['timestamp'])
                    if memory_time < cutoff_date:
                        if await self.delete_memory(memory['id']):
                            deleted_count += 1
                except:
                    pass
            
            logger.info(f"🧹 清理了 {deleted_count} 条过期记忆 (用户：{user_id})")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理记忆失败：{e}")
            return 0
    
    async def get_stats(self) -> Dict:
        """获取统计信息"""
        try:
            collection_data = self.collection.get(include=[])
            total_count = len(collection_data['ids']) if collection_data else 0
            
            return {
                "total_memories": total_count,
                "collection_name": self.collection.name,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"获取统计信息失败：{e}")
            return {"error": str(e)}

# 全局单例
chroma_memory = ChromaMemoryService()
