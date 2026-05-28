#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试订单查询功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.core.config import settings
from neo4j import GraphDatabase

def test_order_queries():
    """测试订单查询功能"""
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URL, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            print("✅ 成功连接到Neo4j知识图谱")
            
            #测试用户101的订单查询
            print("\n🔍测试用户101的订单查询:")
            result = session.run('''
                MATCH (c:Customer {UserID: 1})-[:PLACED_BY]->(o:Order)
                RETURN o.OrderID as order_id, o.OrderDate as order_date, o.Status as status, o.TotalAmount as total_amount
                ORDER BY o.OrderDate DESC
            ''')
            orders = list(result)
            print(f"用户101的订单数: {len(orders)}")
            for order in orders:
                print(f"订单ID: {order['order_id']}, 日期: {order['order_date']},状态: {order['status']}, 金额: {order['total_amount']}")
                
            #测试新的预定义查询格式
            print("\n🧪测试预定义查询格式:")
            try:
                result = session.run('''
                    MATCH (c:Customer {UserID: 1})-[:PLACED_BY]->(o:Order) 
                    RETURN o.OrderID as orderId, o.OrderDate as orderDate, o.Status as status, o.TotalAmount as totalAmount 
                    ORDER BY o.OrderDate DESC
                ''')
                orders = list(result)
                print(f"预定义查询结果: {len(orders)} 个订单")
                for order in orders[:3]:  #只显示前3个
                    print(f"  {order['orderId']}: {order['orderDate']} - {order['status']} - ¥{order['totalAmount']}")
            except Exception as e:
                print(f"预定义查询测试失败: {e}")
                
            #测试参数化查询
            print("\n⚙️测试参数化查询:")
            try:
                user_id = 101
                result = session.run('''
                    MATCH (c:Customer {UserID: $user_id})-[:PLACED_BY]->(o:Order)
                    RETURN o.OrderID as order_id, o.OrderDate as order_date, o.Status as status, o.TotalAmount as total_amount
                    ORDER BY o.OrderDate DESC
                ''', user_id=user_id)
                orders = list(result)
                print(f"参数化查询结果 (UserID={user_id}): {len(orders)} 个订单")
                for order in orders:
                    print(f"  {order['order_id']}: {order['order_date']} - {order['status']} - ¥{order['total_amount']}")
            except Exception as e:
                print(f"参数化查询测试失败: {e}")
                
        driver.close()
        print("\n✅测试完成")
        
    except Exception as e:
        print(f"❌测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_order_queries()