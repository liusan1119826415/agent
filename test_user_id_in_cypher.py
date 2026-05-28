"""
测试 user_id 在 Cypher 查询中的正确传递
"""
import asyncio
import re

# 测试正则表达式替换逻辑
def test_user_id_replacement():
    """测试 UserID 替换逻辑"""
    
    # 模拟生成的 Cypher 语句（包含错误的 UserID）
    test_cases = [
        {
            "input": "MATCH (o:Order)<-[:PLACED_BY]-(c:Customer {UserID: 'AB123'}) RETURN o.OrderID, o.OrderDate",
            "expected_user_id": 123,
            "description": "字符串格式的 UserID"
        },
        {
            "input": "MATCH (o:Order)<-[:PLACED_BY]-(c:Customer {UserID: 'USER456'}) RETURN o.OrderID",
            "expected_user_id": 456,
            "description": "另一个字符串格式的 UserID"
        },
        {
            "input": "MATCH (o:Order)<-[:PLACED_BY]-(c:Customer {UserID: 789}) RETURN o.OrderID",
            "expected_user_id": 789,
            "description": "数字格式的 UserID"
        }
    ]
    
    for test_case in test_cases:
        cypher_statement = test_case["input"]
        user_id = test_case["expected_user_id"]
        
        print(f"\n测试用例：{test_case['description']}")
        print(f"替换前：{cypher_statement}")
        
        # 应用替换逻辑
        def replace_user_id(match):
            return f"{{UserID: {user_id}}}"
        
        cypher_statement = re.sub(
            r'\{UserID:\s*[\'"]?[^\}]+?\}',
            replace_user_id,
            cypher_statement
        )
        
        print(f"替换后：{cypher_statement}")
        print(f"期望的 user_id: {user_id}")
        
        # 验证结果
        if f"UserID: {user_id}" in cypher_statement:
            print("✓ 测试通过")
        else:
            print("✗ 测试失败")
            
if __name__ == "__main__":
    test_user_id_replacement()
