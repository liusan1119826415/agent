#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证导入的用户相关数据
检查订单、客户、用户行为等数据中的用户ID关联
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.core.config import settings

def verify_user_data():
    """验证用户相关数据"""
    try:
        # 使用原生neo4j驱动
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            settings.NEO4J_URL, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            print("🔍验证用户相关数据结构")
            print("=" * 50)
            
            # 1.验证客户数据（包含用户ID）
            print("\n👥客户数据验证:")
            customer_query = """
                MATCH (c:Customer)
                RETURN c.CustomerID AS customer_id, 
                       c.UserID AS user_id,
                       c.CompanyName AS company,
                       c.ContactName AS contact,
                       c.Email AS email
                ORDER BY c.CustomerID
            """
            customers = list(session.run(customer_query))
            print(f"共找到 {len(customers)} 个客户:")
            for customer in customers:
                print(f"  -客户ID: {customer['customer_id']}, 用户ID: {customer['user_id']}")
                print(f"   公司: {customer['company']}")
                print(f"   联系人: {customer['contact']}")
                print(f"  : {customer['email']}")
                print()
            
            # 2.验证订单数据（包含用户ID关联）
            print("\n📋订单数据验证:")
            order_query = """
                MATCH (o:Order)-[:PLACED_BY]->(c:Customer)
                RETURN o.OrderID AS order_id,
                       o.UserID AS user_id,
                       o.CustomerID AS customer_id,
                       o.Status AS status,
                       o.TotalAmount AS total_amount,
                       c.CompanyName AS company
                ORDER BY o.OrderID
            """
            orders = list(session.run(order_query))
            print(f"共找到 {len(orders)} 个订单:")
            for order in orders:
                print(f"  -订单ID: {order['order_id']}")
                print(f"   用户ID: {order['user_id']},客户ID: {order['customer_id']}")
                print(f"  状态: {order['status']}, 金额: ¥{order['total_amount']}")
                print(f"   公司: {order['company']}")
                print()
            
            # 3. 验证用户行为数据
            print("\n📱 用户行为数据验证:")
            behavior_query = """
                MATCH (ub:UserBehavior)
                RETURN ub.UserID AS user_id,
                       ub.CustomerID AS customer_id,
                       ub.ProductID AS product_id,
                       ub.BehaviorType AS behavior_type,
                       ub.Timestamp AS timestamp
                ORDER BY ub.UserID, ub.Timestamp
            """
            behaviors = list(session.run(behavior_query))
            print(f"共找到 {len(behaviors)} 个用户行为记录:")
            
            # 按用户分组显示
            user_behaviors = {}
            for behavior in behaviors:
                user_id = behavior['user_id']
                if user_id not in user_behaviors:
                    user_behaviors[user_id] = []
                user_behaviors[user_id].append(behavior)
            
            for user_id, user_actions in user_behaviors.items():
                print(f"  用户ID {user_id}: {len(user_actions)} 个行为")
                behavior_types = {}
                for action in user_actions:
                    behavior_type = action['behavior_type']
                    behavior_types[behavior_type] = behavior_types.get(behavior_type, 0) + 1
                for btype, count in behavior_types.items():
                    print(f"    - {btype}: {count}")
                print()
            
            # 4.验证完整的用户购物路径
            print("\n🛒 用户购物路径验证:")
            path_query = """
                MATCH (c:Customer)-[:PLACED_BY]->(o:Order)
                MATCH (o)-[r:CONTAINS]->(p:Product)
                RETURN c.UserID AS user_id,
                       c.CustomerID AS customer_id,
                       c.CompanyName AS company,
                       o.OrderID AS order_id,
                       collect({product: p.ProductName, quantity: r.Quantity, price: r.UnitPrice}) AS products
                ORDER BY c.UserID, o.OrderID
            """
            shopping_paths = list(session.run(path_query))
            print(f"共找到 {len(shopping_paths)} 个购物路径:")
            for path in shopping_paths:
                print(f"  用户ID: {path['user_id']} (客户ID: {path['customer_id']})")
                print(f" 公司: {path['company']}")
                print(f" 订单: {path['order_id']}")
                print("  商品:")
                for product in path['products']:
                    print(f"    - {product['product']} x{product['quantity']} @¥{product['price']}")
                print()
            
            # 5.统计信息
            print("\n📊 数据统计:")
            stats_query = """
                MATCH (c:Customer)
                OPTIONAL MATCH (c)-[:PLACED_BY]->(o:Order)
                OPTIONAL MATCH (ub:UserBehavior {UserID: c.UserID})
                RETURN c.UserID AS user_id,
                       count(DISTINCT o) AS order_count,
                       count(DISTINCT ub) AS behavior_count
                ORDER BY c.UserID
            """
            stats = list(session.run(stats_query))
            print("用户活动统计:")
            for stat in stats:
                print(f"  用户ID {stat['user_id']}: {stat['order_count']} 个订单, {stat['behavior_count']} 个行为")
            
            print("\n✅ 数据验证完成！")
            
        driver.close()
        
    except Exception as e:
        print(f"❌ 数据验证失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_user_data()