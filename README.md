# AI 生活助理

一个本地优先的个人管理工具，提供任务、日程、财务、笔记、习惯管理，以及基于 Ollama 的中文对话能力。

## 功能概览

- 任务管理：新增、查看、完成、删除任务
- 日程管理：维护未来安排与时间节点
- 财务记录：记录收入支出流水
- 笔记管理：保存和编辑日常笔记
- 习惯打卡：维护习惯并记录完成情况
- AI 对话：基于本地数据摘要生成建议
- Agent 模式：按需调用工具完成网页搜索、天气查询、任务读取与任务创建预览

## 技术栈

- 前端：Vite + 原生 JavaScript
- 后端：FastAPI + SQLAlchemy
- 数据存储：SQLite
- 模型接入：Ollama、OpenRouter

## 目录结构

- `src/`：前端页面逻辑与样式
- `public/`：前端静态资源
- `backend/`：后端 API、数据库和模型集成

## 环境要求

- Node.js 18 及以上
- Python 3.10 及以上
- 已安装并可运行的 Ollama
- 若使用 OpenRouter，还需准备可用的 API Key

## 前端启动

```bash
npm install
npm run dev
```

默认访问地址通常为 `http://localhost:5173`。

## 后端启动

先准备 Python 虚拟环境和依赖，然后启动服务：

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8008
```

也可以在项目根目录直接运行：

```bash
npm run dev:api
```

## 环境变量

可参考 [backend/.env.example](/Users/gw/Desktop/code/test/backend/.env.example) 创建 `backend/.env`：

```env
AI_PROVIDER=ollama
AI_MODEL=
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:latest
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=
OPENROUTER_SITE_URL=http://127.0.0.1:5173
OPENROUTER_APP_NAME=ai-life-assistant
DATABASE_URL=sqlite:///./data/life_assistant.db
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

## 构建与预览

```bash
npm run build
npm run preview
```

## 开发说明

- 前端开发服务器会将 `/api` 代理到 `http://127.0.0.1:8008`
- 本地数据库默认保存在 `backend/data/life_assistant.db`
- 若使用 Ollama，请确认本地服务已启动，且 `OLLAMA_MODEL` 与本地已安装模型名称一致
- 若使用 OpenRouter，请确认 `OPENROUTER_API_KEY` 已配置且模型名称使用完整 provider/model 形式

## Agent 与工具

当前第一版 Agent 能力包含：

- `web_search`：搜索公开网页结果
- `weather`：查询天气
- `list_tasks`：读取任务列表
- `create_task_preview`：生成待确认的任务创建预览

后端接口：

- `POST /api/agent/run`：运行 Agent
- `GET /api/agent/tools`：查看可用工具
- `POST /api/agent/confirm`：确认执行待办动作
