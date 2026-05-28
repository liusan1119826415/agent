import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from neo4j import AsyncGraphDatabase
from app.models.ecommerce_models import Customer, Product, Order, OrderItem, UserBehavior
from app.core.config import settings

logger = logging.getLogger(__name__)

class EcommerceDataSyncService:
    """电商平台数据同步到Neo4j服务"""
    
    def __init__(self):
        # MySQL连接配置
        self.mysql_engine = create_engine(
            f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@"
            f"{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.mysql_session = sessionmaker(bind=self.mysql_engine)
        
        # Neo4j连接配置
        self.neo4j_driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
    
    async def sync_all_data(self, batch_size: int = 1000):
        """全量同步所有电商数据"""
        try:
            logger.info("开始全量数据同步...")
            
            # 1. 同步客户数据
            await self.sync_customers(batch_size)
            
            # 2. 同步商品数据
            await self.sync_products(batch_size)
            
            # 3. 同步订单数据
            await self.sync_orders(batch_size)
            
            # 4. 同步用户行为数据
            await self.sync_user_behaviors(batch_size)
            
            # 5. 建立关系索引
            await self.create_indexes()
            
            logger.info("全量数据同步完成")
            
        except Exception as e:
            logger.error(f"数据同步失败: {str(e)}", exc_info=True)
            raise
        finally:
            await self.neo4j_driver.close()
    
    async def sync_incremental_data(self, hours_back: int = 24):
        """增量同步最近N小时的数据"""
        try:
            since_time = datetime.now() - timedelta(hours=hours_back)
            logger.info(f"开始增量数据同步，时间范围: {since_time} 至现在")
            
            # 同步增量数据
            await self.sync_customers(batch_size=500, since_time=since_time)
            await self.sync_products(batch_size=500, since_time=since_time)
            await self.sync_orders(batch_size=500, since_time=since_time)
            await self.sync_user_behaviors(batch_size=500, since_time=since_time)
            
            logger.info("增量数据同步完成")
            
        except Exception as e:
            logger.error(f"增量数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def sync_customers(self, batch_size: int = 1000, since_time: Optional[datetime] = None):
        """同步客户数据到Neo4j"""
        try:
            logger.info("开始同步客户数据...")
            
            # 构建查询语句
            query = """
                SELECT id, name, email, phone, created_at, updated_at 
                FROM customers
            """
            if since_time:
                query += " WHERE updated_at >= :since_time"
            
            # 从MySQL获取数据
            with self.mysql_engine.connect() as conn:
                result = conn.execute(text(query), 
                                    {"since_time": since_time} if since_time else {})
                customers = [Customer(**row._asdict()) for row in result]
            
            # 批量同步到Neo4j
            for i in range(0, len(customers), batch_size):
                batch = customers[i:i + batch_size]
                await self._batch_upsert_customers(batch)
                logger.info(f"已同步客户数据批次 {i//batch_size + 1}/{(len(customers)-1)//batch_size + 1}")
                
        except Exception as e:
            logger.error(f"客户数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def sync_products(self, batch_size: int = 1000, since_time: Optional[datetime] = None):
        """同步商品数据到Neo4j"""
        try:
            logger.info("开始同步商品数据...")
            
            query = """
                SELECT id, name, category, price, description, sku, created_at, updated_at 
                FROM products
            """
            if since_time:
                query += " WHERE updated_at >= :since_time"
            
            with self.mysql_engine.connect() as conn:
                result = conn.execute(text(query), 
                                    {"since_time": since_time} if since_time else {})
                products = [Product(**row._asdict()) for row in result]
            
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                await self._batch_upsert_products(batch)
                logger.info(f"已同步商品数据批次 {i//batch_size + 1}/{(len(products)-1)//batch_size + 1}")
                
        except Exception as e:
            logger.error(f"商品数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def sync_orders(self, batch_size: int = 1000, since_time: Optional[datetime] = None):
        """同步订单数据到Neo4j"""
        try:
            logger.info("开始同步订单数据...")
            
            # 同步订单主表
            order_query = """
                SELECT id, customer_id, total_amount, status, created_at, updated_at, completed_at
                FROM orders
            """
            if since_time:
                order_query += " WHERE updated_at >= :since_time"
            
            with self.mysql_engine.connect() as conn:
                order_result = conn.execute(text(order_query), 
                                          {"since_time": since_time} if since_time else {})
                orders = [Order(**row._asdict()) for row in order_result]
            
            # 同步订单项
            order_item_query = """
                SELECT id, order_id, product_id, quantity, unit_price, total_price
                FROM order_items
                WHERE order_id IN :order_ids
            """
            
            for i in range(0, len(orders), batch_size):
                batch = orders[i:i + batch_size]
                order_ids = [order.id for order in batch]
                
                await self._batch_upsert_orders(batch)
                
                # 同步相关订单项
                with self.mysql_engine.connect() as conn:
                    item_result = conn.execute(text(order_item_query), {"order_ids": order_ids})
                    order_items = [OrderItem(**row._asdict()) for row in item_result]
                    await self._batch_upsert_order_items(order_items)
                
                logger.info(f"已同步订单数据批次 {i//batch_size + 1}/{(len(orders)-1)//batch_size + 1}")
                
        except Exception as e:
            logger.error(f"订单数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def sync_user_behaviors(self, batch_size: int = 1000, since_time: Optional[datetime] = None):
        """同步用户行为数据到Neo4j"""
        try:
            logger.info("开始同步用户行为数据...")
            
            query = """
                SELECT id, customer_id, product_id, behavior_type, timestamp, metadata
                FROM user_behaviors
            """
            if since_time:
                query += " WHERE timestamp >= :since_time"
            
            with self.mysql_engine.connect() as conn:
                result = conn.execute(text(query), 
                                    {"since_time": since_time} if since_time else {})
                behaviors = []
                for row in result:
                    behavior_data = row._asdict()
                    # 处理metadata JSON字段
                    if behavior_data.get('metadata'):
                        import json
                        behavior_data['metadata'] = json.loads(behavior_data['metadata'])
                    behaviors.append(UserBehavior(**behavior_data))
            
            for i in range(0, len(behaviors), batch_size):
                batch = behaviors[i:i + batch_size]
                await self._batch_upsert_behaviors(batch)
                logger.info(f"已同步用户行为数据批次 {i//batch_size + 1}/{(len(behaviors)-1)//batch_size + 1}")
                
        except Exception as e:
            logger.error(f"用户行为数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def _batch_upsert_customers(self, customers: List[Customer]):
        """批量更新或插入客户节点"""
        async with self.neo4j_driver.session() as session:
            query = """
            UNWIND $customers AS customer
            MERGE (c:Customer {id: customer.id})
            SET c.name = customer.name,
                c.email = customer.email,
                c.phone = customer.phone,
                c.created_at = customer.created_at,
                c.updated_at = customer.updated_at
            """
            await session.run(query, customers=[{
                'id': c.id,
                'name': c.name,
                'email': c.email,
                'phone': c.phone,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None
            } for c in customers])
    
    async def _batch_upsert_products(self, products: List[Product]):
        """批量更新或插入商品节点"""
        async with self.neo4j_driver.session() as session:
            query = """
            UNWIND $products AS product
            MERGE (p:Product {id: product.id})
            SET p.name = product.name,
                p.category = product.category,
                p.price = product.price,
                p.description = product.description,
                p.sku = product.sku,
                p.created_at = product.created_at,
                p.updated_at = product.updated_at
            """
            await session.run(query, products=[{
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'price': float(p.price),
                'description': p.description,
                'sku': p.sku,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None
            } for p in products])
    
    async def _batch_upsert_orders(self, orders: List[Order]):
        """批量更新或插入订单节点"""
        async with self.neo4j_driver.session() as session:
            query = """
            UNWIND $orders AS order
            MERGE (o:Order {id: order.id})
            SET o.total_amount = order.total_amount,
                o.status = order.status,
                o.created_at = order.created_at,
                o.updated_at = order.updated_at,
                o.completed_at = order.completed_at
            WITH order
            MATCH (c:Customer {id: order.customer_id})
            MERGE (c)-[:ORDERED]->(o)
            """
            await session.run(query, orders=[{
                'id': o.id,
                'customer_id': o.customer_id,
                'total_amount': float(o.total_amount),
                'status': o.status,
                'created_at': o.created_at.isoformat(),
                'updated_at': o.updated_at.isoformat() if o.updated_at else None,
                'completed_at': o.completed_at.isoformat() if o.completed_at else None
            } for o in orders])
    
    async def _batch_upsert_order_items(self, order_items: List[OrderItem]):
        """批量更新订单项关系"""
        async with self.neo4j_driver.session() as session:
            query = """
            UNWIND $items AS item
            MATCH (o:Order {id: item.order_id})
            MATCH (p:Product {id: item.product_id})
            MERGE (o)-[r:CONTAINS]->(p)
            SET r.quantity = item.quantity,
                r.unit_price = item.unit_price,
                r.total_price = item.total_price
            """
            await session.run(query, items=[{
                'order_id': item.order_id,
                'product_id': item.product_id,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price)
            } for item in order_items])
    
    async def _batch_upsert_behaviors(self, behaviors: List[UserBehavior]):
        """批量更新用户行为关系"""
        async with self.neo4j_driver.session() as session:
            query = """
            UNWIND $behaviors AS behavior
            MATCH (c:Customer {id: behavior.customer_id})
            MATCH (p:Product {id: behavior.product_id})
            CALL apoc.create.relationship(c, behavior.behavior_type, {
                timestamp: behavior.timestamp,
                metadata: behavior.metadata
            }, p) YIELD rel
            RETURN count(rel)
            """
            await session.run(query, behaviors=[{
                'customer_id': b.customer_id,
                'product_id': b.product_id,
                'behavior_type': b.behavior_type.upper(),
                'timestamp': b.timestamp.isoformat(),
                'metadata': b.metadata
            } for b in behaviors])
    
    async def create_indexes(self):
        """创建图数据库索引以提升查询性能"""
        async with self.neo4j_driver.session() as session:
            # 节点索引
            indexes = [
                "CREATE INDEX customer_id_index IF NOT EXISTS FOR (c:Customer) ON (c.id)",
                "CREATE INDEX product_id_index IF NOT EXISTS FOR (p:Product) ON (p.id)",
                "CREATE INDEX order_id_index IF NOT EXISTS FOR (o:Order) ON (o.id)",
                "CREATE INDEX product_category_index IF NOT EXISTS FOR (p:Product) ON (p.category)",
                "CREATE INDEX order_status_index IF NOT EXISTS FOR (o:Order) ON (o.status)"
            ]
            
            for index_query in indexes:
                try:
                    await session.run(index_query)
                    logger.info(f"创建索引: {index_query}")
                except Exception as e:
                    logger.warning(f"索引创建失败: {index_query}, 错误: {str(e)}")
    
    async def close(self):
        """关闭数据库连接"""
        await self.neo4j_driver.close()
        self.mysql_engine.dispose()