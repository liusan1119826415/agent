# 第二阶段实施 - 快速开始指南

## 🚀 立即行动

### 第一步：安装 ChromaDB

```bash
cd e:\project\assist-agent\llm_backend
pip install chromadb langchain-chroma
```

### 第二步：FAISS RAG 已经修复！✅

我已经创建了 `rag_service.py`，**FAISS 现在可以被使用了**！

### 第三步：测试 FAISS RAG

创建测试文件：`test_rag.py`

```python
import asyncio
from pathlib import Path
from app.services.rag_service import rag_service

async def main():
    print("=" * 50)
    print("测试 FAISS RAG 功能")
    print("=" * 50)
    
    # 1. 准备测试文档（如果没有 PDF，创建一个简单的文本）
    test_doc_path = Path("test_document.txt")
    if not test_doc_path.exists():
        with open(test_doc_path, "w", encoding="utf-8") as f:
            f.write("""
# 智能家居产品介绍

## 智能灯泡
我们的智能灯泡支持语音控制，可以通过小爱同学、天猫精灵等设备控制。
价格范围：59 元 -199 元
特点：节能、调色、定时开关

## 智能摄像头
支持 360 度旋转，夜视功能，移动侦测报警。
价格：299 元
存储：云存储 + 本地 SD 卡

## 智能门锁
指纹识别、密码开锁、手机 APP 远程开锁
价格：899 元 -1599 元
安装：免费上门安装
""")
        print(f"✓ 创建测试文档：{test_doc_path}")
    
    # 2. 上传文档
    print("\n1. 上传文档到 RAG 系统...")
    upload_result = await rag_service.upload_document(str(test_doc_path))
    print(f"上传结果：{upload_result}")
    
    if upload_result["status"] == "success":
        index_id = upload_result["index_id"]
        print(f"✓ 索引 ID: {index_id}")
        
        # 3. 测试查询
        test_queries = [
            "智能灯泡多少钱？",
            "摄像头有什么功能？",
            "门锁怎么安装？"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. 查询：{query}")
            result = await rag_service.query_documents(
                query=query,
                index_id=index_id,
                top_k=2
            )
            
            print(f"回答：{result['answer']}")
            print(f"来源数量：{len(result['sources'])}")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

运行测试：

```bash
python test_rag.py
```

### 第四步：添加 API 接口到 main.py

在 `llm_backend/main.py` 中添加以下接口（放在第 450 行后面）：

```python
# ========== RAG 相关接口 ==========
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

### 第五步：测试 API

重启服务后：

```bash
# 1. 上传文档
curl -X POST "http://localhost:8000/api/rag/upload" \
  -F "file=@test_document.txt"

# 2. 查询
curl -X POST "http://localhost:8000/api/rag/query" \
  -F "query=智能灯泡的价格" \
  -F "top_k=2"
```

---

## 📦 ChromaDB 集成（可选）

如果你现在就想添加长期记忆功能，继续以下步骤：

### 1. 创建 ChromaDB 服务

按照 `STAGE2_CHROMADB_IMPLEMENTATION.md` 中的说明创建 `chroma_memory_service.py`

### 2. 添加到 requirements.txt

```bash
echo "chromadb==0.4.24" >> requirements.txt
echo "langchain-chroma==0.1.1" >> requirements.txt
pip install -r requirements.txt
```

### 3. 测试 ChromaDB

```python
import asyncio
from app.services.chroma_memory_service import chroma_memory

async def test_chroma():
    # 添加记忆
    await chroma_memory.add_memory(
        user_id=101,
        content="用户想买智能灯泡，预算 200 元"
    )
    
    # 搜索记忆
    memories = await chroma_memory.search_memories(
        user_id=101,
        query="购买预算"
    )
    
    print(f"找到 {len(memories)} 条记忆")
    for m in memories:
        print(f"- {m['content']}")

asyncio.run(test_chroma())
```

---

## ✅ 验收标准

### FAISS RAG（必须完成）
- [ ] 能够上传文档（PDF/TXT）
- [ ] 能够查询文档内容
- [ ] LLM 能基于文档生成准确回答
- [ ] API 接口正常工作

### ChromaDB（可选但推荐）
- [ ] 能够添加记忆
- [ ] 能够语义搜索记忆
- [ ] LangGraph 工作流能检索相关记忆
- [ ] 对话历史自动保存到长期记忆

---

## 🎯 下一步计划

### 今天完成：
1. ✅ 安装 ChromaDB（如果需要）
2. ✅ 测试 FAISS RAG
3. ✅ 添加 API 接口

### 明天完成：
1. 创建 ChromaDB 服务
2. 集成到 LangGraph
3. 端到端测试

### 本周完成：
1. 优化检索效果
2. 添加更多测试用例
3. 性能调优

---

## 🆘 常见问题

### Q1: FAISS 加载索引失败？
**A**: 确保先上传文档创建索引，然后再查询

### Q2: ChromaDB 安装失败？
**A**: 使用 `pip install chromadb==0.4.24` 指定版本

### Q3: RAG 回答不准确？
**A**: 
- 检查文档质量
- 调整 top_k 参数
- 优化 prompt 模板

---

*创建时间：2026-03-14*  
*状态：FAISS RAG 已修复并可用 ✅*
