#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.core.config import settings
from neo4j import GraphDatabase

def check_simple_schema():
    driver = GraphDatabase.driver(
        settings.NEO4J_URL, 
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )
    
    with driver.session(database=settings.NEO4J_DATABASE) as session:
        #检查Customer节点属性
        result = session.run('MATCH (c:Customer) RETURN keys(c) AS props LIMIT 1')
        props = result.single()['props']
        print('Customer属性:', props)
        
        # 查看几个Customer节点的数据
        result = session.run('MATCH (c:Customer) RETURN c LIMIT 3')
        for i, record in enumerate(result):
            print(f'Customer {i+1}:', dict(record['c']))
        
        #检查Order节点属性
        result = session.run('MATCH (o:Order) RETURN keys(o) AS props LIMIT 1')
        props = result.single()['props']
        print('Order属性:', props)
        
        #检查关系属性
        result = session.run('MATCH (c:Customer)-[r:PLACED_BY]->(o:Order) RETURN type(r) as rel_type, keys(r) as props LIMIT 1')
        record = result.single()
        print('PLACED_BY关系属性:', record['props'] if record['props'] else '无属性')
        
        #测试正确的查询
        print('\n测试正确查询:')
        result = session.run('MATCH (c:Customer {UserID: 1})-[:PLACED_BY]->(o:Order) RETURN o.OrderID, o.OrderDate, o.Status, o.TotalAmount ORDER BY o.OrderDate DESC LIMIT 3')
        orders = list(result)
        print(f'找到 {len(orders)} 个订单')
        for order in orders:
            print(f'  OrderID: {order["o.OrderID"]}, OrderDate: {order["o.OrderDate"]}, Status: {order["o.Status"]}, TotalAmount: {order["o.TotalAmount"]}')

    driver.close()

if __name__ == "__main__":
    check_simple_schema()