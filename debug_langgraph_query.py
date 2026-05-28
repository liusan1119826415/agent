#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试LangGraph查询接口
模拟API调用过程，帮助定位问题
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'llm_backend'))

# 修正导入路径
from llm_backend.app.lg_agent.lg_states import AgentState, InputState
from llm_backend.app.lg_agent.utils import new_uuid
from llm_backend.app.lg_agent.lg_builder import graph
from langgraph.types import Command

async def debug_query(query_text: str, user_id: int = 1, conversation_id: str = None):
    """调试查询执行过程"""
    try:
        print(f"🔍 调试查询: {query_text}")
        print(f"👤 用户ID: {user_id}")
        print(f"💬 会话ID: {conversation_id or '新会话'}")
        print("=" * 50)
        
        # 准备输入状态
        input_state = InputState(messages=query_text)
        
        # 配置线程
        thread_id = conversation_id if conversation_id else new_uuid()
        thread_config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id
            }
        }
        
        print("🚀 开始执行查询...")
        
        # 执行查询并捕获详细信息
        async for chunk, metadata in graph.astream(
            input=input_state,
            stream_mode="messages",
            config=thread_config
        ):
            print(f"\n📥 收到响应块:")
            print(f"  内容类型: {type(chunk.content)}")
            print(f"  内容长度: {len(str(chunk.content)) if chunk.content else 0}")
            print(f"  标签: {metadata.get('tags', [])}")
            print(f"  工具调用: {chunk.additional_kwargs.get('tool_calls', '无')}")
            
            if chunk.content:
                print(f"  实际内容: {repr(chunk.content)}")
                
                # 如果是工具调用相关信息，详细记录
                if chunk.additional_kwargs.get("tool_calls"):
                    tool_calls = chunk.additional_kwargs["tool_calls"]
                    for i, tool_call in enumerate(tool_calls):
                        print(f"  工具调用 {i+1}:")
                        print(f"    函数名: {tool_call.get('function', {}).get('name', '未知')}")
                        print(f"    参数: {tool_call.get('function', {}).get('arguments', '无')}")
            
            print("-" * 30)
        
        # 检查最终状态
        print("\n📊 查询执行状态检查:")
        final_state = graph.get_state(thread_config)
        print(f"  状态长度: {len(final_state)}")
        if len(final_state) > 0 and len(final_state[-1]) > 0:
            print(f"  中断数量: {len(final_state[-1][0].interrupts)}")
            if final_state[-1][0].interrupts:
                print(f"  中断详情: {final_state[-1][0].interrupts}")
        
        print("\n✅ 调试完成")
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

async def main():
    # 测试几种不同的查询语句
    test_queries = [
        "通过Cypher查询获取智能音箱类产品信息，包括产品名称、价格和库存数量",
        "查询知识图谱中所有智能音箱产品的详细信息",
        "获取智能音箱类别下的所有产品及其价格库存",
        "检索Product节点中CategoryName为'智能音箱'的所有记录"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"测试查询 {i}: {query}")
        print('='*60)
        await debug_query(query, user_id=1, conversation_id=f"test_{i}")
        await asyncio.sleep(1)  # 避免请求过于频繁

if __name__ == "__main__":
    asyncio.run(main())