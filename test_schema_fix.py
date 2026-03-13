#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试schema修复效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.lg_agent.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph

def test_schema_fix():
    """测试schema修复效果"""
    try:
        print("=== 测试schema修复 ===")
        
        # 获取图数据库连接
        graph = get_neo4j_graph()
        print("✅ 成功连接到Neo4j图数据库")
        
        #检查schema信息
        print("\n=== Schema信息 ===")
        schema = graph.schema
        print(f"Schema长度: {len(schema)} 字符")
        print(f"Schema预览: {schema[:200]}...")
        
        #检查结构化schema
        print("\n=== 结构化Schema ===")
        structured_schema = graph.get_structured_schema
        print(f"节点标签: {list(structured_schema.get('node_labels', []))}")
        print(f"关系类型: {list(structured_schema.get('rel_types', []))}")
        
        #测试正确的查询
        print("\n=== 测试正确查询 ===")
        test_query = "MATCH (c:Customer {UserID: 1})-[:PLACED_BY]->(o:Order) RETURN o.OrderID, o.OrderDate, o.Status, o.TotalAmount ORDER BY o.OrderDate DESC LIMIT 3"
        result = graph.query(test_query)
        print(f"查询结果: {len(result)}条")
        for record in result:
            print(f"  {record}")
            
        print("\n✅ Schema修复测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_schema_fix()