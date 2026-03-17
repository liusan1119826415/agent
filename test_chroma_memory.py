"""
测试 ChromaDB 长期记忆功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent / "llm_backend"
sys.path.insert(0, str(root_dir))

import asyncio
from app.services.chroma_memory_service import chroma_memory

async def test_chroma_memory():
    print("=" * 60)
    print("ChromaDB 长期记忆功能测试")
    print("=" * 60)
    
    # 1. 添加记忆
    print("\n📝 测试 1: 添加记忆")
    print("-" * 60)
    
    test_memories = [
        (101, "用户想买智能灯泡，预算 200 元左右"),
        (101, "用户喜欢小米品牌的智能家居产品"),
        (101, "用户对价格比较敏感，经常询问优惠活动"),
        (101, "用户住在北京市朝阳区，需要快递配送"),
        (102, "用户想购买智能摄像头，关注夜视功能"),
    ]
    
    memory_ids = []
    for user_id, content in test_memories:
        try:
            memory_id = await chroma_memory.add_memory(
                user_id=user_id,
                content=content,
                metadata={"source": "test", "importance": "high"}
            )
            memory_ids.append(memory_id)
            print(f"✓ 添加成功：{memory_id[:8]}... | 用户：{user_id}")
        except Exception as e:
            print(f"✗ 添加失败：{e}")
    
    # 2. 搜索记忆
    print("\n🔍 测试 2: 语义搜索记忆")
    print("-" * 60)
    
    search_queries = [
        (101, "购买预算"),
        (101, "品牌偏好"),
        (101, "配送地址"),
        (102, "摄像头"),
    ]
    
    for user_id, query in search_queries:
        print(f"\n查询：用户 {user_id} - \"{query}\"")
        memories = await chroma_memory.search_memories(
            user_id=user_id,
            query=query,
            top_k=2
        )
        
        if memories:
            for i, memory in enumerate(memories, 1):
                print(f"  {i}. [{memory['distance']:.4f}] {memory['content']}")
        else:
            print("  没有找到相关记忆")
    
    # 3. 获取用户所有记忆
    print("\n📋 测试 3: 获取用户所有记忆")
    print("-" * 60)
    
    user_101_memories = await chroma_memory.get_user_memories(user_id=101, limit=10)
    print(f"用户 101 共有 {len(user_101_memories)} 条记忆:")
    for mem in user_101_memories:
        print(f"  - {mem['content'][:50]}...")
    
    # 4. 统计信息
    print("\n📊 测试 4: 统计信息")
    print("-" * 60)
    
    stats = await chroma_memory.get_stats()
    print(f"集合名称：{stats.get('collection_name', 'N/A')}")
    print(f"总记忆数：{stats.get('total_memories', 0)}")
    print(f"状态：{stats.get('status', 'unknown')}")
    
    # 5. 删除记忆（可选）
    print("\n🗑️ 测试 5: 删除记忆")
    print("-" * 60)
    
    if memory_ids:
        test_id = memory_ids[-1]
        print(f"准备删除：{test_id[:8]}...")
        success = await chroma_memory.delete_memory(test_id)
        if success:
            print("✓ 删除成功")
        else:
            print("✗ 删除失败")
    
    # 6. 清理过期记忆
    print("\n🧹 测试 6: 清理过期记忆")
    print("-" * 60)
    
    deleted = await chroma_memory.cleanup_old_memories(
        user_id=101,
        days_to_keep=30,
        max_memories=100
    )
    print(f"清理了 {deleted} 条过期记忆")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    
    # 7. 演示实际应用场景
    print("\n💡 实际应用场景演示")
    print("-" * 60)
    
    print("""
场景：用户再次访问时，自动检索历史记忆
    
用户问："我之前说的那个东西怎么样？"

系统自动：
1. 从 ChromaDB 检索用户的历史对话
2. 找到"智能灯泡，预算 200 元"的记忆
3. 结合记忆生成个性化回答：
   "您上次提到想购买智能灯泡，预算 200 元左右。
    我为您推荐以下几款..."
    
这就是长期记忆的力量！✨
    """)

if __name__ == "__main__":
    asyncio.run(test_chroma_memory())
