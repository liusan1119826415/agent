#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专门的订单查询工具 -直使用使用预定义的正确Cypher查询
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.core.config import settings
from neo4j import GraphDatabase
from typing import List, Dict, Any

class OrderQueryTool:
    """订单查询工具类"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URL, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
    
    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户订单列表"""
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run('''
                    MATCH (c:Customer {UserID: $user_id})-[:PLACED_BY]->(o:Order)
                    RETURN o.OrderID as order_id, 
                           o.OrderDate as order_date, 
                           o.Status as status, 
                           o.TotalAmount as total_amount
                    ORDER BY o.OrderDate DESC
                ''', user_id=user_id)
                
                orders = []
                for record in result:
                    orders.append({
                        'order_id': record['order_id'],
                        'order_date': record['order_date'],
                        'status': record['status'],
                        'total_amount': record['total_amount']
                    })
                return orders
        except Exception as e:
            print(f"查询用户订单失败: {e}")
            return []
    
    def get_order_details(self, order_id: str) -> List[Dict[str, Any]]:
        """获取订单详情"""
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run('''
                    MATCH (o:Order {OrderID: $order_id})-[contains:CONTAINS]->(p:Product)
                    RETURN p.ProductName as product_name,
                           contains.Quantity as quantity,
                           contains.UnitPrice as unit_price,
                           toFloat(contains.Quantity) * toFloat(contains.UnitPrice) as total_price
                ''', order_id=order_id)
                
                details = []
                for record in result:
                    details.append({
                        'product_name': record['product_name'],
                        'quantity': record['quantity'],
                        'unit_price': record['unit_price'],
                        'total_price': record['total_price']
                    })
                return details
        except Exception as e:
            print(f"查询订单详情失败: {e}")
            return []
    
    def get_user_purchase_history(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户购买历史"""
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run('''
                    MATCH (c:Customer {UserID: $user_id})-[:PLACED_BY]->(o:Order)-[:CONTAINS]->(p:Product)
                    RETURN p.ProductName as product_name,
                           o.OrderDate as order_date,
                           p.UnitPrice as unit_price
                    ORDER BY o.OrderDate DESC
                ''', user_id=user_id)
                
                history = []
                for record in result:
                    history.append({
                        'product_name': record['product_name'],
                        'order_date': record['order_date'],
                        'unit_price': record['unit_price']
                    })
                return history
        except Exception as e:
            print(f"查询购买历史失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        self.driver.close()

# 便捷函数
def query_user_orders(user_id: int) -> List[Dict[str, Any]]:
    """查询用户订单的便捷函数"""
    tool = OrderQueryTool()
    try:
        return tool.get_user_orders(user_id)
    finally:
        tool.close()

def query_order_details(order_id: str) -> List[Dict[str, Any]]:
    """查询订单详情的便捷函数"""
    tool = OrderQueryTool()
    try:
        return tool.get_order_details(order_id)
    finally:
        tool.close()

def query_user_purchase_history(user_id: int) -> List[Dict[str, Any]]:
    """查询用户购买历史的便捷函数"""
    tool = OrderQueryTool()
    try:
        return tool.get_user_purchase_history(user_id)
    finally:
        tool.close()

if __name__ == "__main__":
    #测试代码
    print("=== 订单查询工具测试 ===")
    
    # 测试用户订单查询
    print("\n1. 查询用户1的订单:")
    orders = query_user_orders(1)
    print(f"找到 {len(orders)} 个订单")
    for order in orders:
        print(f" 订单ID: {order['order_id']}, 日期: {order['order_date']},状态: {order['status']}, 金额: {order['total_amount']}")
    
    #测试购买历史
    print("\n2. 查询用户1的购买历史:")
    history = query_user_purchase_history(1)
    print(f"找到 {len(history)}条记录")
    for item in history[:5]:  #只显示前5条
        print(f"  产品: {item['product_name']}, 日期: {item['order_date']}, 价格: {item['unit_price']}")