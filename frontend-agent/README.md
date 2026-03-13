# 智能客服助手前端

这是一个基于Vue3构建的智能客服助手前端应用，用于与后端的LangGraph API进行交互。

## 功能特性

- 实时聊天界面
- 流式消息显示
- 智能客服对话
- 会话管理
- 响应式设计

## 技术栈

- Vue 3
- Pinia (状态管理)
- Vite (构建工具)
- JavaScript (ES6+)

## 安装和运行

1. 安装依赖:
```bash
npm install
```

2. 启动开发服务器:
```bash
npm run dev
```

3. 构建生产版本:
```bash
npm run build
```

## 环境配置

如果需要配置API服务器地址，可以在项目根目录创建`.env`文件:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 项目结构

```
src/
├── api/              # API接口定义
│   └── chatApi.js
├── stores/           # Pinia状态管理
│   └── chatStore.js
├── components/       # 组件
│   └── ChatInterface.vue
├── App.vue           # 主应用组件
└── main.js          # 应用入口
```

## API代理

开发服务器配置了API代理，将`/api`路径的请求转发到后端服务器（默认为`http://localhost:8000`）。