#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Text2Cypher功能修复
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

from llm_backend.app.lg_agent.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph
from llm_backend.app.lg_agent.kg_sub_graph.agentic_rag_agents.retrievers.cypher_examples.northwind_retriever import NorthwindCypherRetriever
from llm_backend.app.lg_agent.kg_sub_graph.agentic_rag_agents.components.cypher_tools.utils import create_text2cypher_generation_node
from langchain_ollama import ChatOllama
from llm_backend.app.core.config import settings

async def test_text2cypher_fix():
    """测试Text2Cypher修复效果"""
    try:
        print("=== 测试Text2Cypher修复 ===")
        
        # 获取图数据库连接
        neo4j_graph = get_neo4j_graph()
        print("✅ 成功连接到Neo4j图数据库")
        
        #检查schema信息
        print(f"\n=== Schema信息 ===")
        schema = neo4j_graph.schema
        print(f"Schema长度: {len(schema)} 字符")
        print(f"Schema包含Customer: {'Customer' in schema}")
        print(f"Schema包含Order: {'Order' in schema}")
        print(f"Schema包含PLACED_BY: {'PLACED_BY' in schema}")
        
        # 创建模型
        model = ChatOllama(model=settings.OLLAMA_AGENT_MODEL, base_url=settings.OLLAMA_BASE_URL, temperature=0.7)
        print("✅ 成功创建语言模型")
        
        # 创建检索器
        cypher_retriever = NorthwindCypherRetriever()
        print("✅ 成功创建Cypher检索器")
        
        # 创建Text2Cypher生成节点
        cypher_generation = create_text2cypher_generation_node(
            llm=model, graph=neo4j_graph, cypher_example_retriever=cypher_retriever
        )
        print("✅ 成功创建Text2Cypher生成节点")
        
        #测试生成Cypher查询
        test_state = {
            "task": "查询用户1的订单信息",
            "query": "查询用户1的订单信息"
        }
        
        print("\n=== 生成Cypher查询 ===")
        cypher_result = await cypher_generation(test_state)
        print(f"生成的Cypher: {cypher_result}")
        
        print("\n✅ Text2Cypher测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_text2cypher_fix())