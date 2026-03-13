#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证Text2Cypher修复效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

import asyncio
from llm_backend.app.lg_agent.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph
from llm_backend.app.lg_agent.kg_sub_graph.agentic_rag_agents.retrievers.cypher_examples.northwind_retriever import NorthwindCypherRetriever
from llm_backend.app.lg_agent.kg_sub_graph.agentic_rag_agents.components.cypher_tools.utils import create_text2cypher_generation_node, create_text2cypher_validation_node
from langchain_ollama import ChatOllama
from llm_backend.app.core.config import settings

async def test_text2cypher_validation():
    """测试Text2Cypher验证修复效果"""
    try:
        print("=== 验证Text2Cypher修复效果 ===")
        
        # 获取图数据库连接
        neo4j_graph = get_neo4j_graph()
        print("✅ 成功连接到Neo4j图数据库")
        
        # 检查schema信息
        print(f"\n=== Schema信息 ===")
        print(f"Schema长度: {len(neo4j_graph.schema)} 字符")
        print(f"Schema预览: {neo4j_graph.schema[:200]}...")
        
        # 检查结构化schema
        structured_schema = neo4j_graph.get_structured_schema
        print(f"\n=== 结构化Schema ===")
        print(f"节点标签: {list(structured_schema.get('node_props', {}).keys())}")
        print(f"关系类型: {list(structured_schema.get('rel_props', {}).keys())}")
        
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
        
        # 测试生成Cypher查询
        test_state = {
            "task": "查询我的客户ID的订单信息",
            "query": "查询我的客户ID的订单信息"
        }
        
        print("\n=== 生成Cypher查询 ===")
        cypher_result = await cypher_generation(test_state)
        print(f"生成的Cypher: {cypher_result}")
        
        # 创建验证节点
        validate_cypher = create_text2cypher_validation_node(
            llm=model,
            graph=neo4j_graph,
            llm_validation=True,
            cypher_statement=cypher_result
        )
        
        print("\n=== 验证Cypher查询 ===")
        execute_info = await validate_cypher(state=test_state)
        print(f"验证结果: {execute_info}")
        
        # 测试修正后的查询执行
        if execute_info.get("statement"):
            print(f"\n=== 执行修正后的查询 ===")
            try:
                result = neo4j_graph.query(execute_info["statement"])
                print(f"查询结果: {result}")
            except Exception as e:
                print(f"执行错误: {e}")
        
        print("\n✅ Text2Cypher验证测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_text2cypher_validation())