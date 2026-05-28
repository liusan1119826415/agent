#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Neo4j知识图谱配置和连接（不依赖APOC）
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.core.config import settings
import asyncio

def test_neo4j_config():
    """测试Neo4j配置"""
    print("🔍 测试Neo4j配置")
    print(f"  URL: {settings.NEO4J_URL}")
    print(f"  Username: {settings.NEO4J_USERNAME}")
    print(f"  Database: {settings.NEO4J_DATABASE}")
    
    try:
        # 使用原生neo4j驱动测试连接
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            settings.NEO4J_URL, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            #测试基本连接
            result = session.run("RETURN 'Connection successful!' AS greeting")
            record = result.single()
            print(f"✅ Neo4j连接测试: {record['greeting']}")
            
            # 检查是否有Order节点
            order_result = session.run("MATCH (o:Order) RETURN count(o) AS order_count LIMIT 1")
            order_count = order_result.single()['order_count']
            print(f"📊 Order节点数量: {order_count}")
            
            if order_count > 0:
                # 获取一些示例订单数据
                sample_orders = session.run("MATCH (o:Order) RETURN o LIMIT 5")
                print("📋 示例订单数据:")
                for i, record in enumerate(sample_orders):
                    order = record['o']
                    print(f"  订单 {i+1}: {dict(order)}")
            else:
                print("⚠️ 没找到Order节点，需要导入示例数据")
            
            # 检查所有节点标签
            labels_result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
            labels = [record['label'] for record in labels_result]
            print(f"🏷️ 所有节点标签: {labels}")
            
            #特别检查与电商相关的标签
            ecommerce_labels = ['Order', 'Product', 'Customer', 'Supplier', 'Category']
            print("🔍检查电商相关节点类型:")
            for label in ecommerce_labels:
                count_result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
                count = count_result.single()['cnt']
                status = "✅" if count > 0 else "❌"
                print(f"  {status} {label}: {count}")
                
        driver.close()
        print("✅ Neo4j连接测试完成")
        
    except Exception as e:
        print(f"❌ Neo4j连接失败: {e}")
        print("💡 提示: 请确认Neo4j数据库正在运行且配置正确")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_neo4j_config()