import './style.css'
import { marked } from 'marked'

const app = document.getElementById('app')

marked.setOptions({
  gfm: true,
  breaks: true,
})

function parseHash() {
  const h = window.location.hash.slice(1) || '/'
  const match = h.match(/^\/post\/([^/]+)\/?$/)
  if (match) return { view: 'post', slug: decodeURIComponent(match[1]) }
  return { view: 'home' }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function layout(inner) {
  return `
    <div class="layout">
      <header class="site-header">
        <a href="#/" style="color:inherit;text-decoration:none">
          <h1 class="site-title">我的博客</h1>
        </a>
        <p class="site-desc">记录想法、读书与技术笔记</p>
      </header>
      ${inner}
      <footer class="site-footer">本地个人博客 · 编辑 <code style="font-size:0.9em">public/posts.json</code> 更新文章</footer>
    </div>
  `
}

function renderHome(posts) {
  const items = posts
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .map(
      (p) => `
      <li class="post-card">
        <a class="post-card-link" href="#/post/${encodeURIComponent(p.slug)}">
          <h2 class="post-card-title">${escapeHtml(p.title)}</h2>
          <div class="post-meta">${escapeHtml(p.date)}${p.tags?.length ? ' · ' + p.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join(' ') : ''}</div>
          <p class="post-excerpt">${escapeHtml(p.excerpt)}</p>
        </a>
      </li>
    `
    )
    .join('')

  app.innerHTML = layout(`
    <ul class="post-list">${items}</ul>
  `)
}

function renderPost(post) {
  if (!post) {
    app.innerHTML = layout(`<p class="empty">找不到这篇文章。</p><p><a href="#/">返回首页</a></p>`)
    return
  }
  const tags =
    post.tags?.length > 0
      ? post.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join(' ')
      : ''
  const html = marked.parse(post.body)
  app.innerHTML = layout(`
    <article>
      <a class="back-link" href="#/">← 返回列表</a>
      <header class="article-header">
        <h1 class="article-title">${escapeHtml(post.title)}</h1>
        <div class="post-meta">${escapeHtml(post.date)}${tags ? ' · ' + tags : ''}</div>
      </header>
      <div class="prose">${html}</div>
    </article>
  `)
}

let cachedPosts = null

async function loadPosts() {
  if (cachedPosts) return cachedPosts
  const res = await fetch('/posts.json')
  if (!res.ok) throw new Error('无法加载 posts.json')
  cachedPosts = await res.json()
  return cachedPosts
}

async function route() {
  const { view, slug } = parseHash()
  try {
    const posts = await loadPosts()
    if (view === 'home') {
      renderHome(posts)
    } else {
      const post = posts.find((p) => p.slug === slug)
      renderPost(post)
    }
  } catch (e) {
    app.innerHTML = layout(`<p class="empty">加载失败：${escapeHtml(e.message)}</p>`)
  }
}

window.addEventListener('hashchange', route)
route()
