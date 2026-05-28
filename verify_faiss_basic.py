"""
验证 FAISS 基本功能（不测试搜索）
"""
import asyncio
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "llm_backend"))

async def verify_faiss():
    print("=" * 60)
    print("FAISS 基本功能验证")
    print("=" * 60)
    
    # 1. 创建测试文件
    test_file = Path("verify_test.txt")
    content = """智能家居产品说明

智能灯泡：支持语音控制，价格 59-199 元，可以调色和定时开关。

智能摄像头：360 度旋转，夜视功能，价格 299 元，支持手机查看。

智能门锁：指纹和密码开锁，价格 899-1599 元，免费安装。
"""
    
    print(f"\n📄 创建测试文件...")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("✓ 文件创建成功")
    
    # 2. 测试创建索引
    print("\n🧪 测试创建索引...")
    try:
        from app.services.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        
        result = await embedding_service.create_embeddings(
            file_path=str(test_file),
            index_dir="indexes"
        )
        
        print(f"✓ 索引创建成功！")
        print(f"  - 索引 ID: {result['index_id']}")
        print(f"  - 文本块数：{result['chunks']}")
        
        # 验证索引是否自动加载
        if embedding_service.current_index is not None:
            print(f"✓ 索引已自动加载到内存")
            print(f"  - 索引维度：{embedding_service.current_index.d}")
            print(f"  - 向量数量：{embedding_service.current_index.ntotal}")
        else:
            print("✗ 索引未加载到内存")
            
        # 验证文档数据
        if embedding_service.current_documents:
            print(f"✓ 文档数据已加载 ({len(embedding_service.current_documents)} 条)")
        else:
            print("✗ 文档数据未加载")
            
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 清理
    print("\n🧹 清理测试文件...")
    try:
        test_file.unlink()
        print("✓ 已删除测试文件")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("✅ 验证完成！")
    print("=" * 60)
    
    print("\n💡 下一步:")
    print("1. 重启 Python 进程")
    print("2. 运行完整测试（包含搜索功能）")
    print("   python simple_faiss_test.py")

if __name__ == "__main__":
    asyncio.run(verify_faiss())
