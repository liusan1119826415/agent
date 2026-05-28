"""
最简单的 FAISS RAG 测试
"""
import asyncio
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "llm_backend"))

async def simple_test():
    print("=" * 60)
    print("简单 FAISS RAG 测试")
    print("=" * 60)
    
    # 1. 创建简单的文本文件
    test_file = Path("simple_test.txt")
    content = """
智能家居产品说明

智能灯泡：支持语音控制，价格 59-199 元，可以调色和定时开关。

智能摄像头：360 度旋转，夜视功能，价格 299 元，支持手机查看。

智能门锁：指纹和密码开锁，价格 899-1599 元，免费安装。
"""
    
    print(f"\n📄 创建测试文件：{test_file}")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("✓ 文件创建成功")
    
    # 2. 直接测试 EmbeddingService
    print("\n🧪 测试 EmbeddingService...")
    try:
        from app.services.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        
        # 创建索引
        result = await embedding_service.create_embeddings(
            file_path=str(test_file),
            index_dir="indexes"
        )
        
        print(f"✓ 索引创建成功！")
        print(f"  - 索引 ID: {result['index_id']}")
        print(f"  - 文本块数：{result['chunks']}")
        
        # 测试搜索
        print("\n🔍 测试搜索功能...")
        search_results = await embedding_service.search(
            query="智能灯泡多少钱",
            top_k=2
        )
        
        if search_results:
            print(f"✓ 搜索成功，找到 {len(search_results)} 条结果")
            for i, r in enumerate(search_results, 1):
                print(f"\n[{i}] 相关度：{r['score']:.4f}")
                print(f"内容：{r['content'][:100]}...")
        else:
            print("✗ 搜索失败")
            
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    # 3. 清理
    print("\n🧹 清理测试文件...")
    try:
        test_file.unlink()
        print("✓ 已删除测试文件")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(simple_test())
