from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
from datetime import datetime
from app.services.ecommerce_sync_service import EcommerceDataSyncService

router = APIRouter(prefix="/api/sync", tags=["数据同步"])

class SyncRequest(BaseModel):
    sync_type: str = "incremental"  # full 或 incremental
    hours_back: Optional[int] = 24
    batch_size: Optional[int] = 1000

@router.post("/ecommerce")
async def trigger_ecommerce_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """触发电商数据同步"""
    try:
        sync_service = EcommerceDataSyncService()
        
        if request.sync_type == "full":
            # 全量同步作为后台任务
            background_tasks.add_task(sync_service.sync_all_data, request.batch_size)
            return {
                "message": "全量数据同步已启动",
                "status": "started",
                "sync_type": "full"
            }
        else:
            # 增量同步作为后台任务
            background_tasks.add_task(
                sync_service.sync_incremental_data, 
                request.hours_back
            )
            return {
                "message": f"增量数据同步已启动（最近{request.hours_back}小时）",
                "status": "started",
                "sync_type": "incremental",
                "hours_back": request.hours_back
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步启动失败: {str(e)}")

@router.get("/ecommerce/status")
async def get_sync_status():
    """获取数据同步状态"""
    # 这里可以实现状态查询逻辑
    return {
        "status": "running",
        "last_sync": datetime.now().isoformat(),
        "message": "数据同步服务正常运行"
    }

@router.post("/ecommerce/schedule")
async def schedule_sync_task():
    """设置定时同步任务"""
    # 这里可以实现定时任务调度逻辑
    return {
        "message": "定时同步任务已设置",
        "schedule": "每小时执行增量同步"
    }