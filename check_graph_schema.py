#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.lg_agent.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph

def check_graph_schema():
    try:
        graph = get_neo4j_graph()
        print("=== 图数据库Schema信息 ===")
        print("Schema:")
        print(graph.schema)
        print("\n=== 结构化Schema信息 ===")
        print("Structured Schema:")
        print(graph.get_structured_schema)
        print("\n=== 测试正确的查询 ===")
        result = graph.query("MATCH (c:Customer {UserID: 1})-[:PLACED_BY]->(o:Order) RETURN o.OrderID, o.OrderDate, o.Status, o.TotalAmount ORDER BY o.OrderDate DESC LIMIT 3")
        print("查询结果:")
        for record in result:
            print(f"  {record}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_graph_schema()