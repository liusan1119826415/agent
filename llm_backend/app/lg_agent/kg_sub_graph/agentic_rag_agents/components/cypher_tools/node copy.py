from typing import Any, Callable, Coroutine, Dict, List
import asyncio
import os
from pathlib import Path
from pydantic import BaseModel, Field

# 导入GraphRAG相关模块
import app.graphrag.graphrag.api as api
from app.graphrag.graphrag.config.load_config import load_config
from app.graphrag.graphrag.callbacks.noop_query_callbacks import NoopQueryCallbacks
from app.graphrag.graphrag.utils.storage import load_table_from_storage
from app.graphrag.graphrag.storage.file_pipeline_storage import FilePipelineStorage
from app.lg_agent.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph
from app.core.logger import get_logger
from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek
from app.core.config import settings, ServiceType
from app.lg_agent.kg_sub_graph.agentic_rag_agents.retrievers.cypher_examples.northwind_retriever import NorthwindCypherRetriever
from app.lg_agent.kg_sub_graph.agentic_rag_agents.components.cypher_tools.utils import create_text2cypher_generation_node, create_text2cypher_validation_node, create_text2cypher_execution_node

#导入订单查询工具



# 获取日志记录器
logger = get_logger(service="cypher_tools")

# 定义GraphRAG查询的输入状态类型
class CypherQueryInputState(BaseModel):
    task: str
    query: str
    steps: List[str]

# 定义GraphRAG查询的输出状态类型
class CypherQueryOutputState(BaseModel):
    task: str
    query: str
    errors: List[str]
    records: Dict[str, Any]
    steps: List[str]

# 定义GraphRAG API包装器

def create_cypher_query_node(
) -> Callable[
    [CypherQueryInputState],
    Coroutine[Any, Any, Dict[str, List[CypherQueryOutputState] | List[str]]],
]:
    """
    创建 Text2Cypher 查询节点，用于LangGraph工作流。

    返回
    -------
    Callable[[CypherQueryInputState], Dict[str, List[CypherQueryOutputState] | List[str]]]
        名为`cypher_query`的LangGraph节点。
    """

    async def cypher_query(
        state: Dict[str, Any],
    ) -> Dict[str, List[CypherQueryOutputState] | List[str]]:
        """
        执行Text2Cypher查询并返回结果。
        """
        errors = list()
        # 获取查询文本
        query = state.get("task", "")
        if not query:
            errors.append("未提供查询文本")
 
        # 使用大模型执行查询/多跳/并行查询计划
        # 1. 根据.env文件中AGENT_SERVICE的设置，选择使用DeepSeek或Ollama启动的模型服务
        if settings.AGENT_SERVICE == ServiceType.DEEPSEEK:
            model = ChatDeepSeek(api_key=settings.DEEPSEEK_API_KEY, model_name=settings.DEEPSEEK_MODEL, temperature=0.7, tags=["research_plan"])
        else:
            model = ChatOllama(model=settings.OLLAMA_AGENT_MODEL, base_url=settings.OLLAMA_BASE_URL, temperature=0.7, tags=["research_plan"])

        # 2. 获取Neo4j图数据库连接
        try:
            neo4j_graph = get_neo4j_graph()
            logger.info("success to get Neo4j graph database connection")
        except Exception as e:
            logger.error(f"failed to get Neo4j graph database connection: {e}")

        # step 2. 创建自定义检索器实例，根据 Graph Schema 创建 Cypher 示例，用来引导大模型生成正确的Cypher 查询语句
        cypher_retriever = NorthwindCypherRetriever()

  

        # Step 3.根据自定义的 Cypher 示例，引导大模型生成 当前输入 问题的 Cypher 查询语句
        cypher_generation = create_text2cypher_generation_node(
            llm=model, graph=neo4j_graph, cypher_example_retriever=cypher_retriever
        )

        cypher_result = await cypher_generation(state)

        print("打印cypher_result信息===",cypher_result)
        #  TODO: Example 1. 直接使用大模型生成 Cypher 查询语句
        """
        # 安装依赖
        pip install neo4j-graphrag
        
        from neo4j_graphrag.retrievers import Text2CypherRetriever
        from neo4j_graphrag.llm import OpenAILLM
        import time
        import pandas as pd
        from neo4j import GraphDatabase

        NEO4J_URI="bolt://localhost"
        NEO4J_USERNAME="neo4j"
        NEO4J_PASSWORD="g1601522830"
        NEO4J_DATABASE="neo4j"

        driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )

        # 这里可以填写 DeepSeek 模型
        client = OpenAILLM(api_key="", base_url="https://api.deepseek.com", model_name='deepseek-chat')

        
        # 定义用户输入：
        examples = [
        "USER INPUT: 'Which actors starred in the Matrix?' QUERY: MATCH (p:Person)-[:ACTED_IN]->(m:Movie) WHERE m.title = 'The Matrix' RETURN p.name"
        ]

        # 初始化检索器
        retriever = Text2CypherRetriever(
            driver=driver,
            llm=client,
            neo4j_schema=neo4j_schema,  # 可以通过 retrieve_and_parse_schema_from_graph_for_prompts 获取动态的Schema
            examples=examples,
        )

        
        # 执行检索：
        query_text = "juju 都有哪些朋友？"
        print(retriever.search(query_text=query_text))
        """

        # step 4. 验证生成的 Cypher 查询语句是否正确
        validate_cypher = create_text2cypher_validation_node(
            llm=model,
            graph=neo4j_graph,
            llm_validation=True,
            cypher_statement=cypher_result
        )

        # step 5. 获取执行Cypher查询的全部信息
        execute_info = await validate_cypher(state=state)

        print("打印execute_info信息===",execute_info)

        # step 6. 执行 Cypher 查询语句
        #确保有有效的Cypher语句
        cypher_statement = execute_info.get("statement", "")
        if not cypher_statement:
            # 如果验证节点没有返回有效的语句，使用生成的语句
            cypher_statement = cypher_result.get("statement", "") if isinstance(cypher_result, dict) else str(cypher_result)
        
        # 修正生成的Cypher语句 - 基于实际数据库schema进行修正
        if cypher_statement:
            # 修正关系名
            cypher_statement = cypher_statement.replace("[:PLACED]", "[:PLACED_BY]")
            
            # 修正属性名
            cypher_statement = cypher_statement.replace(".CustomerID", ".UserID")
            cypher_statement = cypher_statement.replace(".OrderID", ".OrderID")  # 保持不变
            cypher_statement = cypher_statement.replace(".OrderDate", ".OrderDate")  # 保持不变
            cypher_statement = cypher_statement.replace(".ShippedDate", ".Status")  # 用Status替代
            cypher_statement = cypher_statement.replace(".Freight", ".TotalAmount")  # 用TotalAmount替代
            
            # 修正RETURN子句中的属性引用
            if "RETURN" in cypher_statement.upper():
                # 移除不存在的属性
                cypher_statement = cypher_statement.replace(", o.ShippedDate", "")
                cypher_statement = cypher_statement.replace(", o.Freight", "")
                # 添加实际存在的属性
                if "o.OrderID" in cypher_statement and "o.Status" not in cypher_statement:
                    cypher_statement = cypher_statement.replace("o.OrderID,", "o.OrderID, o.Status,")
                
            logger.info(f"修正后的Cypher语句: {cypher_statement}")
            
        # 创建符合执行节点期望的cypher字典
        cypher_dict = {
            "statement": cypher_statement,
            "errors": []
        }
        execute_cypher = create_text2cypher_execution_node(
            graph=neo4j_graph, cypher=cypher_dict
        )

        final_result = await execute_cypher(state)

        # 封装 单次子任务执行的 输出结果并通过Pydantic模型限定格式
        return {
            "cyphers": [
                CypherQueryOutputState(
                        **{
                            "task": state.get("task", ""),
                            "query": query,
                            "statement": "",
                            "parameters":"",
                            "errors": errors,
                            "records": {"result": final_result["cyphers"][0]["records"]} if final_result.get("cyphers") and len(final_result["cyphers"]) > 0 else {"result": []},
                            "steps": ["execute_cypher_query"],
                        }
                    )
                ],
                "steps": ["execute_cypher_query"],
            }
  
    return cypher_query

