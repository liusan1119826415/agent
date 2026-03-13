#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入示例电商数据到Neo4j知识图谱
包括订单、产品、客户、供应商等数据
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.core.config import settings

def import_sample_ecommerce_data():
    """导入示例电商数据"""
    try:
        # 使用原生neo4j驱动
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            settings.NEO4J_URL, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            print("✅ 成功连接到Neo4j知识图谱")
            
            #清空现有数据（可选）
            print("🗑️ 清空现有数据...")
            session.run("MATCH (n) DETACH DELETE n")
            print("✅ 数据清空完成")
            
            #导入产品类别数据
            print("📦导入产品类别数据...")
            categories_data = [
                {"category_id": 4001, "name": "智能音箱", "description": "支持语音控制的智能音箱设备"},
                {"category_id": 4002, "name": "智能照明", "description": "可调节亮度和色温的智能灯具"},
                {"category_id": 4003, "name": "智能安防", "description": "家庭安全监控设备"},
                {"category_id": 4004, "name": "智能厨电", "description": "智能化厨房电器"},
                {"category_id": 4005, "name": "智能清洁", "description": "自动清洁设备"}
            ]
            
            for category in categories_data:
                session.run("""
                    CREATE (c:Category {
                        CategoryID: $category_id,
                        CategoryName: $name, 
                        Description: $description
                    })
                """, category_id=category["category_id"], name=category["name"], description=category["description"])
            print(f"✅导入了 {len(categories_data)} 个产品类别")
            
            #导入供应商数据
            print("🏢导入供应商数据...")
            suppliers_data = [
                {"supplier_id": 2001, "company": "智能科技有限公司", "contact": "张经理", "phone": "010-12345678", "country": "中国", "email": "zhang@smarttech.com"},
                {"supplier_id": 2002, "company": "家居智能设备厂", "contact": "李主管", "phone": "021-87654321", "country": "中国", "email": "li@homeauto.com"},
                {"supplier_id": 2003, "company": "安全设备供应商", "contact": "王总监", "phone": "0755-11111111", "country": "中国", "email": "wang@security.com"},
                {"supplier_id": 2004, "company": "清洁设备制造厂", "contact": "赵厂长", "phone": "0512-22222222", "country": "中国", "email": "zhao@clean.com"},
                {"supplier_id": 2005, "company": "厨房电器公司", "contact": "孙经理", "phone": "0571-33333333", "country": "中国", "email": "sun@kitchen.com"}
            ]
            
            for supplier in suppliers_data:
                session.run("""
                    CREATE (s:Supplier {
                        SupplierID: $supplier_id,
                        CompanyName: $company,
                        ContactName: $contact,
                        Phone: $phone,
                        Country: $country,
                        Email: $email
                    })
                """, supplier_id=supplier["supplier_id"], company=supplier["company"], contact=supplier["contact"], 
                    phone=supplier["phone"], country=supplier["country"], email=supplier["email"])
            print(f"✅导入了 {len(suppliers_data)} 个供应商")
            
            #导入产品数据（包含产品ID）
            print("🛍️导入产品数据...")
            products_data = [
                #音箱
                {"product_id": 3001, "name": "小度智能音箱Pro", "price": 299.0, "stock": 50, "category": "智能音箱", "sku": "SPK-BD-001"},
                {"product_id": 3002, "name": "天猫精灵X1", "price": 199.0, "stock": 30, "category": "智能音箱", "sku": "SPK-TM-001"},
                {"product_id": 3003, "name": "小米AI音箱", "price": 169.0, "stock": 45, "category": "智能音箱", "sku": "SPK-XM-001"},
                
                #照明
                {"product_id": 3004, "name": "飞利浦智能灯泡", "price": 89.0, "stock": 100, "category": "智能照明", "sku": "LGT-PH-001"},
                {"product_id": 3005, "name": "Yeelight智能台灯", "price": 159.0, "stock": 25, "category": "智能照明", "sku": "LGT-YL-001"},
                {"product_id": 3006, "name": "欧普智能吸顶灯", "price": 399.0, "stock": 15, "category": "智能照明", "sku": "LGT-OP-001"},
                
                #安防
                {"product_id": 3007, "name": "小米智能门锁", "price": 1299.0, "stock": 20, "category": "智能安防", "sku": "SEC-XM-001"},
                {"product_id": 3008, "name": "360智能摄像头", "price": 199.0, "stock": 35, "category": "智能安防", "sku": "SEC-360-001"},
                {"product_id": 3009, "name": "萤石智能门铃", "price": 259.0, "stock": 18, "category": "智能安防", "sku": "SEC-YZ-001"},
                
                #智能厨电
                {"product_id": 3010, "name": "美的智能电饭煲", "price": 399.0, "stock": 40, "category": "智能厨电", "sku": "KIT-MD-001"},
                {"product_id": 3011, "name": "苏泊尔智能压力锅", "price": 599.0, "stock": 22, "category": "智能厨电", "sku": "KIT-SB-001"},
                
                #智能清洁
                {"product_id": 3012, "name": "科沃斯扫地机器人", "price": 1599.0, "stock": 12, "category": "智能清洁", "sku": "CLN-KE-001"},
                {"product_id": 3013, "name": "石头扫地机器人", "price": 1899.0, "stock": 8, "category": "智能清洁", "sku": "CLN-ST-001"}
            ]
            
            for product in products_data:
                session.run("""
                    MATCH (c:Category {CategoryName: $category})
                    CREATE (p:Product {
                        ProductID: $product_id,
                        ProductName: $name,
                        SKU: $sku,
                        UnitPrice: $price,
                        UnitsInStock: $stock,
                        CategoryName: $category
                    })-[:BELONGS_TO]->(c)
                """, product_id=product["product_id"], name=product["name"], sku=product["sku"],
                    price=product["price"], stock=product["stock"], category=product["category"])
            print(f"✅导入了 {len(products_data)} 个产品")
            
            #导入供应商-产品关系
            print("🔗 导入供应商产品关系...")
            supplier_products = [
                {"supplier_id": 2001, "product_id": 3001, "supplier": "智能科技有限公司", "product": "小度智能音箱Pro"},
                {"supplier_id": 2001, "product_id": 3002, "supplier": "智能科技有限公司", "product": "天猫精灵X1"},
                {"supplier_id": 2002, "product_id": 3004, "supplier": "家居智能设备厂", "product": "飞利浦智能灯泡"},
                {"supplier_id": 2002, "product_id": 3005, "supplier": "家居智能设备厂", "product": "Yeelight智能台灯"},
                {"supplier_id": 2003, "product_id": 3007, "supplier": "安全设备供应商", "product": "小米智能门锁"},
                {"supplier_id": 2003, "product_id": 3008, "supplier": "安全设备供应商", "product": "360智能摄像头"},
                {"supplier_id": 2003, "product_id": 3009, "supplier": "安全设备供应商", "product": "萤石智能门铃"},
                {"supplier_id": 2004, "product_id": 3012, "supplier": "清洁设备制造厂", "product": "科沃斯扫地机器人"},
                {"supplier_id": 2004, "product_id": 3013, "supplier": "清洁设备制造厂", "product": "石头扫地机器人"},
                {"supplier_id": 2005, "product_id": 3010, "supplier": "厨房电器公司", "product": "美的智能电饭煲"},
                {"supplier_id": 2005, "product_id": 3011, "supplier": "厨房电器公司", "product": "苏泊尔智能压力锅"}
            ]
            
            for sp in supplier_products:
                session.run("""
                    MATCH (s:Supplier {SupplierID: $supplier_id})
                    MATCH (p:Product {ProductID: $product_id})
                    CREATE (p)-[:SUPPLIED_BY]->(s)
                """, supplier_id=sp["supplier_id"], product_id=sp["product_id"])
            print(f"✅导入了 {len(supplier_products)} 个供应商产品关系")
            
            #导入客户数据（包含用户ID）
            print("👥导入客户数据...")
            customers_data = [
                {"customer_id": 1001, "user_id": 1, "company": "北京科技有限公司", "contact": "王总", "phone": "010-11111111", "country": "中国", "email": "wang@bjtech.com"},
                {"customer_id": 1002, "user_id": 1, "company": "上海贸易公司", "contact": "李经理", "phone": "021-22222222", "country": "中国", "email": "li@shtrade.com"},
                {"customer_id": 1003, "user_id": 103, "company": "广州电子公司", "contact": "张主任", "phone": "020-33333333", "country": "中国", "email": "zhang@gztech.com"},
                {"customer_id": 1004, "user_id": 104, "company": "深圳智能科技", "contact": "陈总", "phone": "0755-44444444", "country": "中国", "email": "chen@szsmart.com"},
                {"customer_id": 1005, "user_id": 105, "company": "杭州电商公司", "contact": "刘经理", "phone": "0571-55555555", "country": "中国", "email": "liu@hzec.com"}
            ]
            
            for customer in customers_data:
                session.run("""
                    CREATE (c:Customer {
                        CustomerID: $customer_id,
                        UserID: $user_id,
                        CompanyName: $company,
                        ContactName: $contact,
                        Phone: $phone,
                        Country: $country,
                        Email: $email
                    })
                """, customer_id=customer["customer_id"], user_id=customer["user_id"],
                    company=customer["company"], contact=customer["contact"], 
                    phone=customer["phone"], country=customer["country"], email=customer["email"])
            print(f"✅导入了 {len(customers_data)} 个客户")
            
            #导入订单数据（包含用户ID关联）
            print("📋导入订单数据...")
            orders_data = [
                {
                    "order_id": "ORD001",
                    "customer_id": 1001,
                    "user_id": 1,
                    "order_date": "2024-01-15",
                    "required_date": "2024-01-20",
                    "shipped_date": "2024-01-18",
                    "status": "completed",
                    "total_amount": 1043.0
                },
                {
                    "order_id": "ORD002", 
                    "customer_id": 1002,
                    "user_id": 1,
                    "order_date": "2024-01-16",
                    "required_date": "2024-01-21",
                    "shipped_date": "2024-01-19",
                    "status": "completed",
                    "total_amount": 1498.0
                },
                {
                    "order_id": "ORD003",
                    "customer_id": 1003,
                    "user_id": 103,
                    "order_date": "2024-01-17",
                    "required_date": "2024-01-22", 
                    "shipped_date": None,
                    "status": "pending",
                    "total_amount": 1599.0
                },
                {
                    "order_id": "ORD004",
                    "customer_id": 1004,
                    "user_id": 104,
                    "order_date": "2024-01-18",
                    "required_date": "2024-01-23",
                    "shipped_date": "2024-01-20",
                    "status": "shipped",
                    "total_amount": 2197.0
                },
                {
                    "order_id": "ORD005",
                    "customer_id": 1005,
                    "user_id": 105,
                    "order_date": "2024-01-19",
                    "required_date": "2024-01-24",
                    "shipped_date": None,
                    "status": "pending",
                    "total_amount": 798.0
                }
            ]
            
            for order in orders_data:
                session.run("""
                    MATCH (c:Customer {CustomerID: $customer_id})
                    CREATE (c)-[:PLACED_BY]->(o:Order {
                        OrderID: $order_id,
                        CustomerID: $customer_id,
                        UserID: $user_id,
                        OrderDate: $order_date,
                        RequiredDate: $required_date,
                        ShippedDate: $shipped_date,
                        Status: $status,
                        TotalAmount: $total_amount
                    })
                """, order_id=order["order_id"], customer_id=order["customer_id"],
                    user_id=order["user_id"], order_date=order["order_date"],
                    required_date=order["required_date"], shipped_date=order["shipped_date"],
                    status=order["status"], total_amount=order["total_amount"])
            print(f"✅导入了 {len(orders_data)} 个订单")
            
            #导入订单详情（产品关联）
            print("📄导入订单详情...")
            order_details = [
                #订单1
                {"order_id": "ORD001", "product_id": 3001, "product": "小度智能音箱Pro", "quantity": 2, "unit_price": 299.0, "total_price": 598.0},
                {"order_id": "ORD001", "product_id": 3004, "product": "飞利浦智能灯泡", "quantity": 5, "unit_price": 89.0, "total_price": 445.0},
                
                #订单2
                {"order_id": "ORD002", "product_id": 3002, "product": "天猫精灵X1", "quantity": 1, "unit_price": 199.0, "total_price": 199.0},
                {"order_id": "ORD002", "product_id": 3007, "product": "小米智能门锁", "quantity": 1, "unit_price": 1299.0, "total_price": 1299.0},
                
                #订单3
                {"order_id": "ORD003", "product_id": 3012, "product": "科沃斯扫地机器人", "quantity": 1, "unit_price": 1599.0, "total_price": 1599.0},
                
                # 订单4
                {"order_id": "ORD004", "product_id": 3013, "product": "石头扫地机器人", "quantity": 1, "unit_price": 1899.0, "total_price": 1899.0},
                {"order_id": "ORD004", "product_id": 3005, "product": "Yeelight智能台灯", "quantity": 2, "unit_price": 159.0, "total_price": 318.0},
                {"order_id": "ORD004", "product_id": 3008, "product": "360智能摄像头", "quantity": 1, "unit_price": 199.0, "total_price": 199.0},
                
                #订单5
                {"order_id": "ORD005", "product_id": 3003, "product": "小米AI音箱", "quantity": 3, "unit_price": 169.0, "total_price": 507.0},
                {"order_id": "ORD005", "product_id": 3006, "product": "欧普智能吸顶灯", "quantity": 1, "unit_price": 399.0, "total_price": 399.0},
                {"order_id": "ORD005", "product_id": 3009, "product": "萤石智能门铃", "quantity": 1, "unit_price": 259.0, "total_price": 259.0}
            ]
            
            for detail in order_details:
                session.run("""
                    MATCH (o:Order {OrderID: $order_id})
                    MATCH (p:Product {ProductID: $product_id})
                    CREATE (o)-[:CONTAINS {
                        Quantity: $quantity,
                        UnitPrice: $unit_price,
                        TotalPrice: $total_price
                    }]->(p)
                """, order_id=detail["order_id"], product_id=detail["product_id"], product=detail["product"],
                    quantity=detail["quantity"], unit_price=detail["unit_price"],
                    total_price=detail["total_price"])
            print(f"✅导入了 {len(order_details)} 个订单详情")
            
            #导入用户行为数据
            print("📱导入用户行为数据...")
            user_behaviors = [
                #用户101的行为
                {"user_id": 101, "customer_id": 1001, "product_id": 3001, "behavior_type": "view", "timestamp": "2024-01-10T10:30:00"},
                {"user_id": 101, "customer_id": 1001, "product_id": 3001, "behavior_type": "cart", "timestamp": "2024-01-12T14:20:00"},
                {"user_id": 101, "customer_id": 1001, "product_id": 3001, "behavior_type": "purchase", "timestamp": "2024-01-15T09:15:00"},
                {"user_id": 101, "customer_id": 1001, "product_id": 3004, "behavior_type": "view", "timestamp": "2024-01-11T16:45:00"},
                {"user_id": 101, "customer_id": 1001, "product_id": 3004, "behavior_type": "cart", "timestamp": "2024-01-14T11:30:00"},
                {"user_id": 101, "customer_id": 1001, "product_id": 3004, "behavior_type": "purchase", "timestamp": "2024-01-15T09:15:00"},
                
                #用户102的行为
                {"user_id": 102, "customer_id": 1002, "product_id": 3002, "behavior_type": "view", "timestamp": "2024-01-11T09:20:00"},
                {"user_id": 102, "customer_id": 1002, "product_id": 3002, "behavior_type": "favorite", "timestamp": "2024-01-13T15:10:00"},
                {"user_id": 102, "customer_id": 1002, "product_id": 3002, "behavior_type": "cart", "timestamp": "2024-01-15T13:45:00"},
                {"user_id": 102, "customer_id": 1002, "product_id": 3002, "behavior_type": "purchase", "timestamp": "2024-01-16T10:30:00"},
                {"user_id": 102, "customer_id": 1002, "product_id": 3007, "behavior_type": "view", "timestamp": "2024-01-12T11:20:00"},
                {"user_id": 102, "customer_id": 1002, "product_id": 3007, "behavior_type": "cart", "timestamp": "2024-01-15T16:50:00"},
                {"user_id": 102, "customer_id": 1002, "product_id": 3007, "behavior_type": "purchase", "timestamp": "2024-01-16T10:30:00"},
                
                #用户103的行为
                {"user_id": 103, "customer_id": 1003, "product_id": 3012, "behavior_type": "view", "timestamp": "2024-01-12T14:30:00"},
                {"user_id": 103, "customer_id": 1003, "product_id": 3012, "behavior_type": "cart", "timestamp": "2024-01-16T10:15:00"},
                {"user_id": 103, "customer_id": 1003, "product_id": 3012, "behavior_type": "purchase", "timestamp": "2024-01-17T11:20:00"},
                
                #用户104的行为
                {"user_id": 104, "customer_id": 1004, "product_id": 3013, "behavior_type": "view", "timestamp": "2024-01-13T09:45:00"},
                {"user_id": 104, "customer_id": 1004, "product_id": 3013, "behavior_type": "cart", "timestamp": "2024-01-17T15:30:00"},
                {"user_id": 104, "customer_id": 1004, "product_id": 3013, "behavior_type": "purchase", "timestamp": "2024-01-18T14:20:00"},
                {"user_id": 104, "customer_id": 1004, "product_id": 3005, "behavior_type": "view", "timestamp": "2024-01-14T11:10:00"},
                {"user_id": 104, "customer_id": 1004, "product_id": 3005, "behavior_type": "cart", "timestamp": "2024-01-17T16:45:00"},
                {"user_id": 104, "customer_id": 1004, "product_id": 3005, "behavior_type": "purchase", "timestamp": "2024-01-18T14:20:00"},
                
                #用户105的行为
                {"user_id": 105, "customer_id": 1005, "product_id": 3003, "behavior_type": "view", "timestamp": "2024-01-14T13:20:00"},
                {"user_id": 105, "customer_id": 1005, "product_id": 3003, "behavior_type": "cart", "timestamp": "2024-01-18T10:45:00"},
                {"user_id": 105, "customer_id": 1005, "product_id": 3003, "behavior_type": "purchase", "timestamp": "2024-01-19T09:30:00"},
                {"user_id": 105, "customer_id": 1005, "product_id": 3006, "behavior_type": "view", "timestamp": "2024-01-15T15:10:00"},
                {"user_id": 105, "customer_id": 1005, "product_id": 3006, "behavior_type": "cart", "timestamp": "2024-01-18T11:20:00"},
                {"user_id": 105, "customer_id": 1005, "product_id": 3006, "behavior_type": "purchase", "timestamp": "2024-01-19T09:30:00"}
            ]
            
            for behavior in user_behaviors:
                session.run("""
                    CREATE (ub:UserBehavior {
                        UserID: $user_id,
                        CustomerID: $customer_id,
                        ProductID: $product_id,
                        BehaviorType: $behavior_type,
                        Timestamp: datetime($timestamp)
                    })
                """, user_id=behavior["user_id"], customer_id=behavior["customer_id"],
                    product_id=behavior["product_id"], behavior_type=behavior["behavior_type"],
                    timestamp=behavior["timestamp"])
            print(f"✅导入了 {len(user_behaviors)} 个用户行为记录")
            
            #验证导入结果
            print("\n🔍 验证导入结果:")
            validation_queries = [
                ("Order", "MATCH (o:Order) RETURN count(o) AS cnt"),
                ("Product", "MATCH (p:Product) RETURN count(p) AS cnt"),
                ("Customer", "MATCH (c:Customer) RETURN count(c) AS cnt"),
                ("Supplier", "MATCH (s:Supplier) RETURN count(s) AS cnt"),
                ("Category", "MATCH (cat:Category) RETURN count(cat) AS cnt")
            ]
            
            for label, query in validation_queries:
                result = session.run(query)
                count = result.single()['cnt']
                status = "✅" if count > 0 else "❌"
                print(f"  {status} {label}: {count}")
                
            print("\n✅ 数据导入完成！")
            
        driver.close()
        
    except Exception as e:
        print(f"❌ 数据导入失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_sample_ecommerce_data()