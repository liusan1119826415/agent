"""
快速测试 FAISS RAG 功能
"""
import asyncio
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "llm_backend"))

from app.services.rag_service import rag_service

async def quick_test():
    print("=" * 60)
    print("FAISS RAG 快速测试")
    print("=" * 60)
    
    # 1. 创建测试文档（使用 TXT 避免 PDF 解析问题）
    test_doc_path = Path("test_document.txt")
    print(f"\n📄 1. 创建测试文档：{test_doc_path}")
    
    content = """
# 智能家居产品介绍

## 智能灯泡
我们的智能灯泡支持语音控制，可以通过小爱同学、天猫精灵等设备控制。
价格范围：59 元 -199 元
特点：节能 LED、1600 万色调色、定时开关、远程控制

## 智能摄像头
支持 360 度旋转，红外夜视功能，移动侦测报警。
价格：299 元
存储：云存储 + 本地 SD 卡（最大 128GB）
特点：高清 1080P、双向语音、手机 APP 查看

## 智能门锁
指纹识别、密码开锁、手机 APP 远程开锁、IC 卡开锁
价格：899 元 -1599 元
安装：免费上门安装
保修：3 年质保
"""
    
    with open(test_doc_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✓ 文档创建成功")
    
    # 2. 上传文档
    print("\n📤 2. 上传文档到 RAG 系统...")
    try:
        upload_result = await rag_service.upload_document(str(test_doc_path))
        print(f"上传结果：{upload_result}")
        
        if upload_result["status"] != "success":
            print(f"✗ 上传失败：{upload_result.get('message', 'Unknown error')}")
            return
        
        index_id = upload_result["index_id"]
        chunks = upload_result["chunks"]
        print(f"✓ 上传成功！")
        print(f"  - 索引 ID: {index_id}")
        print(f"  - 文档块数：{chunks}")
        
    except Exception as e:
        print(f"✗ 上传失败：{e}")
        return
    
    # 3. 测试查询
    print("\n🔍 3. 测试查询功能")
    print("-" * 60)
    
    test_queries = [
        "智能灯泡多少钱？",
        "摄像头有什么功能？",
        "门锁怎么安装？保修多久？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n【查询{i}】{query}")
        try:
            result = await rag_service.query_documents(
                query=query,
                index_id=index_id,
                top_k=2
            )
            
            print(f"回答：{result['answer']}")
            print(f"来源数量：{len(result['sources'])}")
            
            # 显示来源信息
            if result['sources']:
                print("\n来源片段:")
                for j, source in enumerate(result['sources'], 1):
                    score = source.get('score', 0)
                    content_preview = source['content'][:100].replace('\n', ' ')
                    print(f"  [{j}] (相关度：{score:.4f}) {content_preview}...")
            
        except Exception as e:
            print(f"✗ 查询失败：{e}")
    
    # 4. 清理测试文件
    print("\n" + "=" * 60)
    print("🧹 清理测试文件...")
    try:
        test_doc_path.unlink()
        print(f"✓ 已删除：{test_doc_path}")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    
    print("\n💡 下一步:")
    print("1. 启动服务：cd llm_backend && python main.py")
    print("2. 使用 curl 测试 API 接口")
    print("3. 在前端集成 RAG 功能")

if __name__ == "__main__":
    asyncio.run(quick_test())
