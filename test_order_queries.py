#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Neo4j知识图谱中的订单数据查询
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.lg_agent.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph
from llm_backend.app.lg_agent.kg_sub_graph.agentic_rag_agents.components.predefined_cypher.cypher_dict import predefined_cypher_dict
import asyncio

async def test_order_queries():
    """测试订单相关查询"""
    try:
        # 获取Neo4j连接
        graph = get_neo4j_graph()
        print("✅ 成功连接到Neo4j知识图谱")
        
        # 测试1: 查询最近的订单
        print("\n🔍 测试1: 查询最近的订单")
        try:
            recent_orders_query = predefined_cypher_dict["recent_orders"]
            recent_orders = graph.query(recent_orders_query)
            print(f"返回 {len(recent_orders)} 个最近订单:")
            for order in recent_orders:
                print(f"  - 订单ID: {order.get('o.orderId', order.get('orderId', 'N/A'))}, "
                      f"日期: {order.get('o.OrderDate', order.get('OrderDate', 'N/A'))}, "
                      f"客户: {order.get('o.CustomerName', order.get('CustomerName', 'N/A'))}")
        except Exception as e:
            print(f"❌ 查询最近订单失败: {e}")
        
        # 测试2: 查询所有订单总数
        print("\n🔍 测试2: 查询订单总数")
        try:
            order_count = graph.query("MATCH (o:Order) RETURN count(o) as total_orders")
            print(f"订单总数: {order_count[0]['total_orders'] if order_count else 0}")
        except Exception as e:
            print(f"❌ 查询订单总数失败: {e}")
            
        # 测试3: 查询特定订单详情（如果有订单ID）
        print("\n🔍 测试3: 查询订单详情示例")
        try:
            sample_orders = graph.query("MATCH (o:Order) RETURN o.orderId as orderId LIMIT 1")
            if sample_orders:
                sample_order_id = sample_orders[0]['orderId']
                print(f"使用示例订单ID: {sample_order_id}")
                
                # 查询该订单的产品详情
                order_details_query = predefined_cypher_dict["order_details"]
                # 替换查询中的参数
                order_details_query = order_details_query.replace("$order_id", f"'{sample_order_id}'")
                
                order_details = graph.query(order_details_query)
                print(f"订单 {sample_order_id} 包含 {len(order_details)} 个产品:")
                for detail in order_details:
                    print(f"  - 产品: {detail.get('p.ProductName', detail.get('ProductName', 'N/A'))}, "
                          f"数量: {detail.get('contains.Quantity', detail.get('Quantity', 'N/A'))}, "
                          f"单价: {detail.get('contains.UnitPrice', detail.get('UnitPrice', 'N/A'))}")
            else:
                print("  没有找到任何订单数据")
        except Exception as e:
            print(f"❌ 查询订单详情失败: {e}")
            
        # 测试4: 查看所有节点类型统计
        print("\n🔍 测试4: 知识图谱节点统计")
        try:
            node_counts = graph.query("""
                CALL db.labels() YIELD label
                WITH label
                CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as cnt', {}) 
                YIELD value
                RETURN label, value.cnt as count
                ORDER BY count DESC
            """)
            print("各类型节点数量:")
            for item in node_counts:
                print(f"  - {item['label']}: {item['count']}")
        except Exception as e:
            # 如果APOC插件不可用，使用简单查询
            try:
                print("  尝试简单查询...")
                labels = graph.query("CALL db.labels()")
                for label_item in labels:
                    label = label_item['label']
                    count = graph.query(f"MATCH (n:{label}) RETURN count(n) as cnt")[0]['cnt']
                    print(f"  - {label}: {count}")
            except Exception as e2:
                print(f"  统计查询失败: {e2}")
                
        print("\n✅ 订单数据查询测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_order_queries())