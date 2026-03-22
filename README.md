# 个人博客

基于 **Vite** 与 **Markdown** 的轻量静态博客：前端单页、文章数据在 JSON 中，本地即可预览与构建。

## 环境要求

- [Node.js](https://nodejs.org/) 18 及以上（推荐当前 LTS）

## 安装与运行

```bash
npm install
```

开发（热更新，默认打开浏览器）：

```bash
npm run dev
```

访问终端里提示的本地地址（一般为 `http://localhost:5173`）。

生产构建与预览：

```bash
npm run build
npm run preview
```

构建产物在 `dist/`，可部署到任意静态托管（GitHub Pages、Netlify、Vercel 等）。

## 写文章

编辑 `public/posts.json`：每条为 JSON 对象，字段含 `slug`、`title`、`date`、`tags`、`excerpt`，正文用 Markdown 写在 `body` 里。首页按 `date` 从新到旧排序。

路由：`/#/` 为列表，`/#/post/<slug>` 为单篇。

## 技术栈

- [Vite](https://vitejs.dev/)
- [marked](https://marked.js.org/)（Markdown 渲染）

## 许可证

私有项目，按需自行添加许可证。
