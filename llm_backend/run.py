import uvicorn
from app.core.logger import get_logger
import os
from pathlib import Path

logger = get_logger(service="server")

def start_server():
    # 确保工作目录正确
    os.chdir(Path(__file__).parent)
    
    logger.info("Starting server...")
    logger.info(f"Working directory: {os.getcwd()}")
    
    uvicorn.run(
        "main:app",        # 使用模块路径
        host="0.0.0.0",
        port=8000,
        access_log=True,   # 启用访问日志以便调试
        log_level="info",  # 更详细的日志级别
        reload=True,       # 开发模式下启用热重载
        reload_dirs=["./"] # 监控整个目录的更改
    )

if __name__ == "__main__":
    start_server()