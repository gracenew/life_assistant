import './style.css'

const app = document.getElementById('app')

const VIEWS = ['overview', 'tasks', 'events', 'finance', 'notes', 'habits']

function parseHash() {
  const h = (window.location.hash.slice(1) || '/overview').replace(/^\//, '')
  const v = h.split('/')[0] || 'overview'
  return VIEWS.includes(v) ? v : 'overview'
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

async function api(path, options = {}) {
  const url = path.startsWith('/') ? path : `/${path}`
  const headers = { ...options.headers }
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(options.body)
  }
  const res = await fetch(`/api${url}`, { ...options, headers })
  const text = await res.text()
  if (!res.ok) throw new Error(text || res.statusText)
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function fmtLocal(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
  } catch {
    return iso
  }
}

function layout(content, title = 'AI 生活助理') {
  const nav = VIEWS.map((v) => {
    const label = {
      overview: '概览',
      tasks: '任务',
      events: '日程',
      finance: '财务',
      notes: '笔记',
      habits: '习惯',
    }[v]
    const active = parseHash() === v ? 'nav-link active' : 'nav-link'
    return `<a class="${active}" href="#/${v}">${label}</a>`
  }).join('')

  return `
    <div class="shell">
      <header class="top">
        <div class="brand">
          <h1 class="brand-title">${escapeHtml(title)}</h1>
          <p class="brand-sub">本地数据 · 多模型对话</p>
        </div>
        <nav class="nav">${nav}</nav>
      </header>
      <main class="main">${content}</main>
    </div>
  `
}

let chatLoading = false
let agentLoading = false

async function renderOverview() {
  let cfg = {
    ai_provider: 'openrouter',
    ai_model: '',
    ollama_base_url: '',
    ollama_model: '',
    openrouter_base_url: '',
  }
  try {
    cfg = await api('/config')
  } catch {
    cfg = {
      ai_provider: 'openrouter',
      ai_model: '—',
      ollama_base_url: '（后端未连接）',
      ollama_model: '—',
      openrouter_base_url: '—',
    }
  }

  let tasks = []
  let events = []
  try {
    tasks = await api('/tasks?status=pending')
  } catch {
    tasks = []
  }
  try {
    events = await api('/events')
  } catch {
    events = []
  }

  const evSoon = (events || [])
    .filter((e) => new Date(e.start_at) >= new Date(new Date().setHours(0, 0, 0, 0)))
    .sort((a, b) => new Date(a.start_at) - new Date(b.start_at))
    .slice(0, 8)

  const taskLines = (tasks || []).slice(0, 8).map((t) => `<li>${escapeHtml(t.title)} · ${fmtLocal(t.due_at)}</li>`).join('')

  const eventLines = evSoon.map((e) => `<li>${escapeHtml(e.title)} · ${fmtLocal(e.start_at)}</li>`).join('')

  const inner = `
    <div class="grid-2">
      <section class="card">
        <h2 class="card-title">连接状态</h2>
        <p class="muted">默认 Provider：<code>${escapeHtml(cfg.ai_provider || 'ollama')}</code></p>
        <p class="muted">默认模型：<code>${escapeHtml(cfg.ai_model || '—')}</code></p>
        <p class="muted">Ollama 地址：<code>${escapeHtml(cfg.ollama_base_url || '—')}</code></p>
        <p class="muted">OpenRouter 地址：<code>${escapeHtml(cfg.openrouter_base_url || '—')}</code></p>
        <p class="hint">若使用 Ollama，请先执行 <code>ollama list</code> 确认模型名称。若使用 OpenRouter，可优先试免费模型，如 <code>z-ai/glm-4.5-air:free</code>，也可使用 <code>openrouter/free</code> 自动选择免费模型。</p>
      </section>
      <section class="card">
        <h2 class="card-title">与助理对话</h2>
        <div class="form-grid compact">
          <label>Provider
            <select id="chat-provider" class="input">
              <option value="ollama"${(cfg.ai_provider || 'openrouter') === 'ollama' ? ' selected' : ''}>Ollama</option>
              <option value="openrouter"${cfg.ai_provider === 'openrouter' ? ' selected' : ''}>OpenRouter</option>
            </select>
          </label>
          <label>模型
            <input id="chat-model" list="chat-model-options" class="input" value="${escapeHtml(cfg.ai_model || '')}" placeholder="例如 z-ai/glm-4.5-air:free 或 openrouter/free" />
          </label>
        </div>
        <datalist id="chat-model-options">
          <option value="z-ai/glm-4.5-air:free"></option>
          <option value="openrouter/free"></option>
          <option value="minimax/minimax-m2.5"></option>
          <option value="z-ai/glm-4.5-air"></option>
          <option value="${escapeHtml(cfg.ollama_model || 'qwen2.5:latest')}"></option>
        </datalist>
        <textarea id="chat-input" class="input-area" rows="4" placeholder="例如：根据我的待办和日程，帮我安排今天下午的优先级…"></textarea>
        <div class="row">
          <button type="button" class="btn primary" id="chat-send">发送</button>
          <span class="muted small" id="chat-status"></span>
        </div>
        <div id="chat-out" class="chat-out prose"></div>

        <div class="section-divider"></div>

        <h2 class="card-title">Agent 模式</h2>
        <p class="hint">适合需要调用工具的任务，例如查天气、搜网页、结合待办给建议，或先生成任务创建预览再确认执行。</p>
        <textarea id="agent-input" class="input-area" rows="4" placeholder="例如：帮我查一下明天上海天气，如果下雨就给我生成一个带伞任务预览。"></textarea>
        <div class="row">
          <button type="button" class="btn primary" id="agent-run">运行 Agent</button>
          <span class="muted small" id="agent-status"></span>
        </div>
        <div id="agent-out" class="chat-out prose"></div>
      </section>
    </div>
    <div class="grid-2">
      <section class="card">
        <h2 class="card-title">待办（前8条）</h2>
        <ul class="list-plain">${taskLines || '<li class="muted">暂无</li>'}</ul>
        <p><a href="#/tasks">管理任务 →</a></p>
      </section>
      <section class="card">
        <h2 class="card-title">临近日程</h2>
        <ul class="list-plain">${eventLines || '<li class="muted">暂无</li>'}</ul>
        <p><a href="#/events">管理日程 →</a></p>
      </section>
    </div>
  `

  app.innerHTML = layout(inner)

  const input = document.getElementById('chat-input')
  const out = document.getElementById('chat-out')
  const status = document.getElementById('chat-status')
  const providerInput = document.getElementById('chat-provider')
  const modelInput = document.getElementById('chat-model')
  const agentInput = document.getElementById('agent-input')
  const agentOut = document.getElementById('agent-out')
  const agentStatus = document.getElementById('agent-status')
  let pendingActions = []

  async function sendChat() {
    const message = (input.value || '').trim()
    const provider = providerInput.value
    const model = (modelInput.value || '').trim()
    if (!message || chatLoading) return
    chatLoading = true
    status.textContent = '请求中…'
    out.innerHTML = ''
    try {
      const data = await api('/chat', { method: 'POST', body: { message, provider, model: model || null } })
      if (data.error) {
        out.innerHTML = `<p class="err">${escapeHtml(data.error)}</p>`
      } else {
        out.innerHTML = `<p>${escapeHtml(data.reply).replace(/\n/g, '<br/>')}</p>`
      }
    } catch (e) {
      out.innerHTML = `<p class="err">${escapeHtml(e.message)}</p>`
    }
    chatLoading = false
    status.textContent = ''
  }

  function renderAgentResponse(data, notice = '') {
    pendingActions = data.pending_actions || []

    const toolCalls = (data.tool_calls || []).map((call) => {
      const summary = escapeHtml(call.summary || '')
      const error = call.error ? `<p class="err small">${escapeHtml(call.error)}</p>` : ''
      return `
        <li>
          <strong>${escapeHtml(call.tool)}</strong> · ${call.ok ? '成功' : '失败'}
          <div class="muted small">${summary}</div>
          ${error}
        </li>
      `
    }).join('')

    const actions = pendingActions.map((action, index) => `
      <div class="agent-action">
        <div>
          <strong>${escapeHtml(action.type)}</strong>
          <div class="muted small">${escapeHtml(JSON.stringify(action.payload))}</div>
        </div>
        <button type="button" class="btn sm" data-confirm-action="${index}">确认执行</button>
      </div>
    `).join('')

    agentOut.innerHTML = `
      ${notice ? `<p class="ok small">${escapeHtml(notice)}</p>` : ''}
      <p>${escapeHtml(data.answer || '').replace(/\n/g, '<br/>') || '<span class="muted">暂无结果</span>'}</p>
      ${data.reasoning ? `<p class="muted small">Agent 思路：${escapeHtml(data.reasoning)}</p>` : ''}
      <div class="agent-block">
        <h3 class="agent-title">工具调用</h3>
        <ul class="list-plain">${toolCalls || '<li class="muted">本次未调用工具</li>'}</ul>
      </div>
      <div class="agent-block">
        <h3 class="agent-title">待确认动作</h3>
        ${actions || '<p class="muted small">本次没有待确认动作</p>'}
      </div>
    `

    agentOut.querySelectorAll('[data-confirm-action]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const index = Number(btn.getAttribute('data-confirm-action'))
        const action = pendingActions[index]
        if (!action) return
        btn.disabled = true
        agentStatus.textContent = '执行中…'
        try {
          const result = await api('/agent/confirm', {
            method: 'POST',
            body: { action_type: action.type, payload: action.payload },
          })
          pendingActions = pendingActions.filter((_, i) => i !== index)
          renderAgentResponse(
            {
              ...data,
              pending_actions: pendingActions,
            },
            `已执行 ${result.action_type}：${result.record.title || result.record.id}`
          )
        } catch (e) {
          agentStatus.textContent = ''
          btn.disabled = false
          agentOut.insertAdjacentHTML('afterbegin', `<p class="err small">${escapeHtml(e.message)}</p>`)
          return
        }
        agentStatus.textContent = ''
      })
    })
  }

  async function runAgent() {
    const message = (agentInput.value || '').trim()
    const provider = providerInput.value
    const model = (modelInput.value || '').trim()
    if (!message || agentLoading) return
    agentLoading = true
    agentStatus.textContent = 'Agent 运行中…'
    agentOut.innerHTML = ''
    try {
      const data = await api('/agent/run', {
        method: 'POST',
        body: { message, provider, model: model || null, max_steps: 4 },
      })
      if (data.error) {
        agentOut.innerHTML = `<p class="err">${escapeHtml(data.error)}</p>`
      } else {
        renderAgentResponse(data)
      }
    } catch (e) {
      agentOut.innerHTML = `<p class="err">${escapeHtml(e.message)}</p>`
    }
    agentLoading = false
    agentStatus.textContent = ''
  }

  providerInput.addEventListener('change', () => {
    if (providerInput.value === 'openrouter' && !(modelInput.value || '').trim()) {
      modelInput.value = cfg.ai_model || 'z-ai/glm-4.5-air:free'
    }
    if (providerInput.value === 'ollama' && !(modelInput.value || '').trim()) {
      modelInput.value = cfg.ollama_model || 'qwen2.5:latest'
    }
  })

  document.getElementById('chat-send').addEventListener('click', sendChat)
  document.getElementById('agent-run').addEventListener('click', runAgent)
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) sendChat()
  })
  agentInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) runAgent()
  })
}

async function renderTasks() {
  const tasks = await api('/tasks')
  const rows = (tasks || [])
    .map(
      (t) => `
    <tr>
      <td>${escapeHtml(t.title)}</td>
      <td>${escapeHtml(t.status)}</td>
      <td>${fmtLocal(t.due_at)}</td>
      <td>
        <button type="button" class="btn sm" data-done="${t.id}">完成</button>
        <button type="button" class="btn sm danger" data-del="${t.id}">删</button>
      </td>
    </tr>`
    )
    .join('')

  const inner = `
    <section class="card">
      <h2 class="card-title">新建任务</h2>
      <form id="task-form" class="form-grid">
        <label>标题 <input name="title" required class="input" /></label>
        <label>截止 <input name="due_at" type="datetime-local" class="input" /></label>
        <label>优先级
          <select name="priority" class="input"><option value="low">低</option><option value="medium" selected>中</option><option value="high">高</option></select>
        </label>
        <label class="full">备注 <textarea name="description" class="input" rows="2"></textarea></label>
        <div class="full"><button type="submit" class="btn primary">添加</button></div>
      </form>
    </section>
    <section class="card">
      <h2 class="card-title">任务列表</h2>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>标题</th><th>状态</th><th>截止</th><th></th></tr></thead>
          <tbody>${rows || '<tr><td colspan="4" class="muted">暂无</td></tr>'}</tbody>
        </table>
      </div>
    </section>
  `
  app.innerHTML = layout(inner, '任务')

  document.getElementById('task-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const fd = new FormData(e.target)
    const title = fd.get('title')
    const due = fd.get('due_at')
    const body = {
      title,
      description: fd.get('description') || null,
      priority: fd.get('priority'),
      status: 'pending',
      due_at: due ? new Date(due).toISOString() : null,
    }
    await api('/tasks', { method: 'POST', body })
    await renderTasks()
  })

  app.querySelectorAll('[data-done]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-done')
      await api(`/tasks/${id}`, { method: 'PATCH', body: { status: 'done' } })
      await renderTasks()
    })
  })
  app.querySelectorAll('[data-del]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-del')
      await api(`/tasks/${id}`, { method: 'DELETE' })
      await renderTasks()
    })
  })
}

async function renderEvents() {
  const events = await api('/events')
  const rows = (events || [])
    .sort((a, b) => new Date(b.start_at) - new Date(a.start_at))
    .map(
      (ev) => `
    <tr>
      <td>${escapeHtml(ev.title)}</td>
      <td>${fmtLocal(ev.start_at)}</td>
      <td>${ev.end_at ? fmtLocal(ev.end_at) : '—'}</td>
      <td><button type="button" class="btn sm danger" data-del-ev="${ev.id}">删</button></td>
    </tr>`
    )
    .join('')

  const inner = `
    <section class="card">
      <h2 class="card-title">新建日程</h2>
      <form id="ev-form" class="form-grid">
        <label>标题 <input name="title" required class="input" /></label>
        <label>开始 <input name="start_at" type="datetime-local" required class="input" /></label>
        <label>结束 <input name="end_at" type="datetime-local" class="input" /></label>
        <label class="full">备注 <textarea name="description" class="input" rows="2"></textarea></label>
        <div class="full"><button type="submit" class="btn primary">添加</button></div>
      </form>
    </section>
    <section class="card">
      <h2 class="card-title">日程列表</h2>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>标题</th><th>开始</th><th>结束</th><th></th></tr></thead>
          <tbody>${rows || '<tr><td colspan="4" class="muted">暂无</td></tr>'}</tbody>
        </table>
      </div>
    </section>
  `
  app.innerHTML = layout(inner, '日程')

  document.getElementById('ev-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const fd = new FormData(e.target)
    const start = fd.get('start_at')
    const end = fd.get('end_at')
    const body = {
      title: fd.get('title'),
      description: fd.get('description') || null,
      start_at: new Date(start).toISOString(),
      end_at: end ? new Date(end).toISOString() : null,
      all_day: false,
    }
    await api('/events', { method: 'POST', body })
    await renderEvents()
  })

  app.querySelectorAll('[data-del-ev]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-del-ev')
      await api(`/events/${id}`, { method: 'DELETE' })
      await renderEvents()
    })
  })
}

async function renderFinance() {
  const txs = await api('/transactions')
  const rows = (txs || []).map(
    (tx) => `
    <tr>
      <td>${escapeHtml(String(tx.amount))}</td>
      <td>${escapeHtml(tx.category)}</td>
      <td>${fmtLocal(tx.occurred_at)}</td>
      <td>${escapeHtml(tx.note || '')}</td>
      <td><button type="button" class="btn sm danger" data-del-tx="${tx.id}">删</button></td>
    </tr>`
  ).join('')

  const inner = `
    <section class="card">
      <h2 class="card-title">记一笔</h2>
      <form id="tx-form" class="form-grid">
        <label>金额（支出为负，收入为正） <input name="amount" type="number" step="0.01" required class="input" /></label>
        <label>分类 <input name="category" class="input" value="餐饮" /></label>
        <label>时间 <input name="occurred_at" type="datetime-local" required class="input" /></label>
        <label class="full">备注 <input name="note" class="input" /></label>
        <div class="full"><button type="submit" class="btn primary">保存</button></div>
      </form>
    </section>
    <section class="card">
      <h2 class="card-title">流水</h2>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>金额</th><th>分类</th><th>时间</th><th>备注</th><th></th></tr></thead>
          <tbody>${rows || '<tr><td colspan="5" class="muted">暂无</td></tr>'}</tbody>
        </table>
      </div>
    </section>
  `
  app.innerHTML = layout(inner, '财务')

  const occurred = document.querySelector('input[name="occurred_at"]')
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  occurred.value = now.toISOString().slice(0, 16)

  document.getElementById('tx-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const fd = new FormData(e.target)
    const body = {
      amount: parseFloat(String(fd.get('amount')), 10),
      category: fd.get('category'),
      note: fd.get('note') || null,
      occurred_at: new Date(fd.get('occurred_at')).toISOString(),
      currency: 'CNY',
    }
    await api('/transactions', { method: 'POST', body })
    await renderFinance()
  })

  app.querySelectorAll('[data-del-tx]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-del-tx')
      await api(`/transactions/${id}`, { method: 'DELETE' })
      await renderFinance()
    })
  })
}

async function renderNotes() {
  const notes = await api('/notes')
  const rows = (notes || []).map(
    (n) => `
    <tr>
      <td>${escapeHtml(n.title)}</td>
      <td class="muted">${escapeHtml((n.tags || '').slice(0, 40))}</td>
      <td>${fmtLocal(n.updated_at)}</td>
      <td><button type="button" class="btn sm" data-edit-note="${n.id}">编辑</button>
      <button type="button" class="btn sm danger" data-del-note="${n.id}">删</button></td>
    </tr>`
  ).join('')

  const inner = `
    <section class="card">
      <h2 class="card-title">新建笔记</h2>
      <form id="note-form" class="form-grid">
        <label>标题 <input name="title" required class="input" /></label>
        <label>标签（逗号分隔） <input name="tags" class="input" placeholder="工作, 灵感" /></label>
        <label class="full">正文 <textarea name="body" class="input" rows="5"></textarea></label>
        <div class="full"><button type="submit" class="btn primary">保存</button></div>
      </form>
    </section>
    <section class="card">
      <h2 class="card-title">笔记列表</h2>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>标题</th><th>标签</th><th>更新</th><th></th></tr></thead>
          <tbody>${rows || '<tr><td colspan="4" class="muted">暂无</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    <section class="card hidden" id="note-editor-wrap">
      <h2 class="card-title">编辑笔记 <span id="note-editor-id" class="muted"></span></h2>
      <form id="note-edit-form" class="form-grid">
        <input type="hidden" name="id" />
        <label>标题 <input name="title" required class="input" /></label>
        <label>标签 <input name="tags" class="input" /></label>
        <label class="full">正文 <textarea name="body" class="input" rows="8"></textarea></label>
        <div class="full"><button type="submit" class="btn primary">更新</button></div>
      </form>
    </section>
  `
  app.innerHTML = layout(inner, '笔记')

  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const fd = new FormData(e.target)
    await api('/notes', {
      method: 'POST',
      body: { title: fd.get('title'), body: fd.get('body') || '', tags: fd.get('tags') || '' },
    })
    await renderNotes()
  })

  app.querySelectorAll('[data-del-note]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-del-note')
      await api(`/notes/${id}`, { method: 'DELETE' })
      await renderNotes()
    })
  })

  app.querySelectorAll('[data-edit-note]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-edit-note')
      const n = await api(`/notes/${id}`)
      const wrap = document.getElementById('note-editor-wrap')
      wrap.classList.remove('hidden')
      document.getElementById('note-editor-id').textContent = `#${id}`
      const f = document.getElementById('note-edit-form')
      f.querySelector('input[name="id"]').value = id
      f.querySelector('input[name="title"]').value = n.title
      f.querySelector('input[name="tags"]').value = n.tags || ''
      f.querySelector('textarea[name="body"]').value = n.body || ''
      wrap.scrollIntoView({ behavior: 'smooth' })
    })
  })

  document.getElementById('note-edit-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const fd = new FormData(e.target)
    const id = fd.get('id')
    await api(`/notes/${id}`, {
      method: 'PATCH',
      body: { title: fd.get('title'), body: fd.get('body') || '', tags: fd.get('tags') || '' },
    })
    await renderNotes()
  })
}

async function renderHabits() {
  const habits = await api('/habits')
  const rows = await Promise.all(
    (habits || []).map(async (h) => {
      let logs = []
      try {
        logs = await api(`/habits/${h.id}/logs?limit=7`)
      } catch {
        logs = []
      }
      const streak = (logs || []).filter((l) => l.completed).length
      return `
      <tr>
        <td>${escapeHtml(h.name)}</td>
        <td>${escapeHtml(h.frequency)}</td>
        <td>${streak} / 最近7条记录</td>
        <td><button type="button" class="btn sm" data-log="${h.id}">今日打卡</button>
        <button type="button" class="btn sm danger" data-del-h="${h.id}">删</button></td>
      </tr>`
    })
  )

  const inner = `
    <section class="card">
      <h2 class="card-title">新建习惯</h2>
      <form id="habit-form" class="form-grid">
        <label>名称 <input name="name" required class="input" /></label>
        <label>频率
          <select name="frequency" class="input"><option value="daily">每日</option><option value="weekly">每周</option></select>
        </label>
        <label class="full">说明 <textarea name="description" class="input" rows="2"></textarea></label>
        <div class="full"><button type="submit" class="btn primary">添加</button></div>
      </form>
    </section>
    <section class="card">
      <h2 class="card-title">习惯列表</h2>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>名称</th><th>频率</th><th>记录</th><th></th></tr></thead>
          <tbody>${rows.join('') || '<tr><td colspan="4" class="muted">暂无</td></tr>'}</tbody>
        </table>
      </div>
    </section>
  `
  app.innerHTML = layout(inner, '习惯')

  document.getElementById('habit-form').addEventListener('submit', async (e) => {
    e.preventDefault()
    const fd = new FormData(e.target)
    await api('/habits', {
      method: 'POST',
      body: {
        name: fd.get('name'),
        description: fd.get('description') || null,
        frequency: fd.get('frequency'),
      },
    })
    await renderHabits()
  })

  app.querySelectorAll('[data-log]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-log')
      await api(`/habits/${id}/log`, { method: 'POST', body: { completed: true } })
      await renderHabits()
    })
  })
  app.querySelectorAll('[data-del-h]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-del-h')
      await api(`/habits/${id}`, { method: 'DELETE' })
      await renderHabits()
    })
  })
}

async function route() {
  const view = parseHash()
  try {
    if (view === 'overview') await renderOverview()
    else if (view === 'tasks') await renderTasks()
    else if (view === 'events') await renderEvents()
    else if (view === 'finance') await renderFinance()
    else if (view === 'notes') await renderNotes()
    else if (view === 'habits') await renderHabits()
  } catch (e) {
    app.innerHTML = layout(`<p class="err">${escapeHtml(e.message)}</p><p class="muted">请先启动后端：<code>cd backend && .venv/bin/uvicorn app.main:app --reload --port 8008</code></p>`)
  }
}

window.addEventListener('hashchange', route)
if (!window.location.hash) window.location.hash = '#/overview'
route()
