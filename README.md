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

## 使用示例

### 普通 AI 对话

适合总结、整理和给建议：

- `根据我的待办和日程，帮我安排今天下午的优先级`
- `总结一下我最近的任务和日程风险`
- `帮我把今天的重点事项整理成 3 条`

### Agent 模式

适合需要调用工具的任务，例如天气、搜索、待办读取，以及生成待确认动作。

#### 1. 简单天气查询

这类问题会优先直达天气工具，不依赖大模型先做决策：

- `帮我查一下明天上海天气`
- `北京今天的天气怎么样`

返回结果通常会包含：

- 天气概况
- 温度区间
- 是否建议带伞

#### 2. 简单待办查询

这类问题会优先直达待办工具：

- `看看我当前待办里最靠前的几项是什么`
- `我现在有哪些待办任务`

返回结果通常会列出当前靠前的未完成任务。

#### 3. 复杂 Agent 编排

如果问题同时包含“查询 + 判断 + 动作建议”，系统会进入完整 Agent 编排：

- `帮我查一下明天上海天气，如果下雨就给我一个带伞任务预览`
- `搜索一下 OpenRouter 免费模型，再推荐一个适合这个项目测试的`

这类请求的处理流程通常是：

1. Agent 判断需要调用哪些工具
2. 执行天气 / 搜索 / 本地数据工具
3. 汇总结果
4. 如有写入动作，先给出预览，再由用户确认

#### 4. 确认执行动作

当前第一版已支持任务创建预览与确认执行：

- Agent 先生成 `create_task_preview`
- 前端展示待确认动作
- 用户点击确认后，后端才真正写入任务

这样可以避免 AI 直接误改用户数据。

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

当前已实现的路由策略：

- 简单天气问题：优先直达 `weather`
- 简单待办问题：优先直达 `list_tasks`
- 复杂复合问题：进入完整 Agent + Tools 编排
