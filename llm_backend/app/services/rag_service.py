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
