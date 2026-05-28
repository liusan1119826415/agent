#!/usr/bin/env python3
"""
电商数据同步部署和使用示例
"""

import asyncio
import logging
from app.services.ecommerce_sync_service import EcommerceDataSyncService
from app.api.sync_api import router as sync_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """主函数示例"""
    print("=== 电商知识图谱数据同步系统 ===")
    
    # 1. 创建同步服务实例
    sync_service = EcommerceDataSyncService()
    
    try:
        # 2. 执行全量同步
        print("开始全量数据同步...")
        await sync_service.sync_all_data(batch_size=500)
        
        # 3. 执行增量同步
        print("开始增量数据同步...")
        await sync_service.sync_incremental_data(hours_back=1)
        
        print("数据同步完成！")
        
    except Exception as e:
        print(f"同步过程中出现错误: {e}")
    finally:
        await sync_service.close()

# 使用示例
if __name__ == "__main__":
    # 运行同步任务
    asyncio.run(main())
    
    # API使用示例:
    """
    # 启动全量同步
    curl -X POST http://localhost:8000/api/sync/ecommerce \
         -H "Content-Type: application/json" \
         -d '{"sync_type": "full", "batch_size": 1000}'
    
    # 启动增量同步
    curl -X POST http://localhost:8000/api/sync/ecommerce \
         -H "Content-Type: application/json" \
         -d '{"sync_type": "incremental", "hours_back": 24}'
    
    # 查询同步状态
    curl http://localhost:8000/api/sync/ecommerce/status
    """