#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查知识图谱数据模式和订单数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.core.config import settings
from neo4j import GraphDatabase

def check_data_schema():
    """检查数据模式和订单数据"""
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URL, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            print("✅ 成功连接到Neo4j知识图谱")
            
            #检查节点标签
            result = session.run('CALL db.labels()')
            labels = [record['label'] for record in result]
            print('现有节点标签:', labels)
            
            # 检查关系类型
            result = session.run('CALL db.relationshipTypes()')
            rel_types = [record['relationshipType'] for record in result]
            print('现有关系类型:', rel_types)
            
            #检查用户订单数据
            print('\n🔍 用户订单数据检查:')
            result = session.run('''
                MATCH (c:Customer)-[r]->(o:Order) 
                RETURN c.UserID, c.CompanyName, type(r) as rel_type, count(o) as order_count 
                LIMIT 5
            ''')
            print('用户订单关系模式:')
            for record in result:
                print(f'  UserID: {record["UserID"]},公: {record["CompanyName"]}, 关系: {record["rel_type"]},订单数: {record["order_count"]}')
                
            # 检查预定义Cypher查询中的模式匹配
            print('\n🧪查询模式测试:')
            
            #测试PLACED关系模式
            try:
                result = session.run('MATCH (c:Customer)-[:PLACED]->(o:Order) WHERE c.UserID = 101 RETURN count(o) as order_count')
                count = result.single()['order_count']
                print(f'  PLACED 关系模式: {count} 个订单')
            except Exception as e:
                print(f'  PLACED 关系模式不匹配: {e}')
                
            #测试PLACED_BY关系模式
            try:
                result = session.run('MATCH (c:Customer)-[:PLACED_BY]->(o:Order) WHERE c.UserID = 101 RETURN count(o) as order_count')
                count = result.single()['order_count']
                print(f'  PLACED_BY 关系模式: {count} 个订单')
            except Exception as e:
                print(f'  PLACED_BY 关系模式不匹配: {e}')
                
            #测试实际的订单查询
            print('\n📋 实际订单查询测试:')
            try:
                result = session.run('''
                    MATCH (c:Customer {UserID: 101})-[:PLACED_BY]->(o:Order)
                    RETURN o.OrderID, o.OrderDate, o.Status, o.TotalAmount
                    ORDER BY o.OrderDate DESC
                ''')
                orders = list(result)
                print(f'  用户101的订单数: {len(orders)}')
                for order in orders:
                    print(f'   订单ID: {order["OrderID"]}, 日期: {order["OrderDate"]},状态: {order["Status"]}, 金额: {order["TotalAmount"]}')
            except Exception as e:
                print(f'  订单查询失败: {e}')
                
            #检查用户行为数据
            print('\n📱 用户行为数据:')
            try:
                result = session.run('MATCH (ub:UserBehavior) WHERE ub.UserID = 101 RETURN count(ub) as behavior_count')
                count = result.single()['behavior_count']
                print(f'  用户101的行为记录数: {count}')
            except Exception as e:
                print(f'  用户行为数据查询失败: {e}')
                
        driver.close()
        
    except Exception as e:
        print(f"❌连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_data_schema()