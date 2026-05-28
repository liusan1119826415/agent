from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Customer:
    """客户实体"""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class Product:
    """商品实体"""
    id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None
    sku: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class Order:
    """订单实体"""
    id: int
    customer_id: int
    total_amount: float
    status: str  # pending, paid, shipped, completed, cancelled
    created_at: datetime
    updated_at: datetime = None
    completed_at: Optional[datetime] = None

@dataclass
class OrderItem:
    """订单项实体"""
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float

@dataclass
class UserBehavior:
    """用户行为实体"""
    id: int
    customer_id: int
    product_id: int
    behavior_type: str  # view, cart, purchase, favorite, review
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

# 图数据库节点标签定义
NEO4J_LABELS = {
    'CUSTOMER': 'Customer',
    'PRODUCT': 'Product', 
    'ORDER': 'Order',
    'CATEGORY': 'Category',
    'SUPPLIER': 'Supplier'
}

# 图数据库关系类型定义
NEO4J_RELATIONSHIPS = {
    'PURCHASED': 'PURCHASED',      # 客户购买商品
    'ORDERED': 'ORDERED',          # 客户下单
    'CONTAINS': 'CONTAINS',        # 订单包含商品
    'BELONGS_TO': 'BELONGS_TO',    # 商品属于分类
    'SUPPLIED_BY': 'SUPPLIED_BY',  # 商品由供应商提供
    'VIEWED': 'VIEWED',            # 用户浏览商品
    'ADDED_TO_CART': 'ADDED_TO_CART', # 用户加购商品
    'FAVORITED': 'FAVORITED'       # 用户收藏商品
}