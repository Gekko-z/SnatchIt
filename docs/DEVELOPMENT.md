# SnatchIt 开发文档

## 项目背景

SnatchIt 源于用户需求：需要一个可视化的跨平台视频下载工具，让非技术用户也能方便地下载抖音和 Twitter/X 平台的视频。

项目基于 [f2](https://github.com/Johnserf-Seed/f2) 库构建，f2 是一个异步多平台视频下载 CLI 工具。SnatchIt 为其提供 GUI 封装，使其对普通用户更加友好。

## 架构设计

### 组件关系

```
┌─────────────────────────────────────────────────┐
│                   MainWindow                     │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐          │
│  │LinkInput│ │CookiePanel│ │LogPanel │          │
│  └────┬────┘ └─────┬────┘ └────┬────┘          │
│       │            │           │                │
│  ┌────┴────────────┴───────────┴────┐           │
│  │         DownloadWorker            │           │
│  │   (QThread + asyncio 事件循环)     │           │
│  └────────────────┬─────────────────┘           │
│                   │                             │
│  ┌────────────────┴─────────────────┐           │
│  │          f2 Library              │           │
│  │  ┌────────────┐ ┌─────────────┐  │           │
│  │  │DouyinHandler│ │TwitterHandler│  │           │
│  │  └────────────┘ └─────────────┘  │           │
│  │  ┌────────────┐ ┌─────────────┐  │           │
│  │  │DouyinCrawler│ │TwitterCrawler│  │           │
│  │  └────────────┘ └─────────────┘  │           │
│  │  ┌────────────┐ ┌─────────────┐  │           │
│  │  │DouyinDownloader│ │TwitterDownloader│       │
│  │  └────────────┘ └─────────────┘  │           │
│  └──────────────────────────────────┘           │
│                                                  │
│  ┌─────────────────────────────────┐             │
│  │       CookieFetcher             │             │
│  │  (WebSocket → DevTools Protocol)│             │
│  └─────────────────────────────────┘             │
└─────────────────────────────────────────────────┘
```

### 数据流

1. 用户输入 URL → LinkInput 组件
2. 用户获取/输入 Cookie → CookiePanel
3. 用户点击"开始下载" → 创建 DownloadWorker
4. DownloadWorker 在新线程中：
   - 创建 asyncio 事件循环
   - 根据平台调用对应的 f2 Handler
   - Handler 通过 Crawler 获取元数据
   - Downloader 下载视频文件
5. 下载过程中通过 Qt 信号更新进度条和日志

## f2 集成细节

### kwargs 参数说明

传递给 f2 Handler 的 kwargs 字典：

```python
kwargs = {
    "url": "https://x.com/user/status/1234567890",  # 视频链接
    "mode": "one",        # one | post | like | bookmark (twitter)
                          # one | post | like | mix | live (douyin)
    "path": "./Download", # 保存路径
    "cookie": "...",      # 登录 Cookie
    "folderize": True,    # 是否创建子文件夹
    "naming": "{create}_{desc}",  # 文件命名模板
    "timeout": 10,        # 请求超时时间(秒)
    "max_retries": 5,     # 重试次数
}

# Twitter 还需要 headers
kwargs["headers"] = {
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://twitter.com/",
    "Authorization": "Bearer AAAAAAAAAAAA...",
    "X-Csrf-Token": "...",  # 等于 cookie 中的 ct0 值
}
```

### 抖音下载流程

```python
from f2.apps.douyin.utils import AwemeIdFetcher
from f2.apps.douyin.handler import DouyinHandler

# 从 URL 提取视频 ID
aweme_id = await AwemeIdFetcher.get_aweme_id(url)

# 创建 Handler 并下载
handler = DouyinHandler(kwargs=kwargs)
handler.kwargs["url"] = url
handler.kwargs["mode"] = "one"
await handler.handle_one_video()
```

### Twitter 下载流程

```python
from f2.apps.twitter.utils import TweetIdFetcher
from f2.apps.twitter.handler import TwitterHandler

# 从 URL 提取推文 ID
tweet_id = await TweetIdFetcher.get_tweet_id(url)

# 创建 Handler 并下载
handler = TwitterHandler(kwargs=kwargs)
handler.kwargs["url"] = url
handler.kwargs["mode"] = "one"
await handler.handle_one_tweet()
```

## Cookie 获取机制

### 原理

利用 Chrome DevTools Protocol (CDP) 的远程调试功能：
1. 启动浏览器时添加 `--remote-debugging-port=PORT` 参数
2. 浏览器会暴露 HTTP 接口 (`http://localhost:PORT/json`)
3. 通过该接口获取页面的 WebSocket 调试 URL
4. 连接 WebSocket 并执行 `document.cookie` JavaScript
5. 返回完整的 Cookie 字符串

### 支持的平台

- **抖音**: Edge/Chrome → `https://www.douyin.com` → `document.cookie`
- **Twitter**: Edge/Chrome → `https://x.com` → `document.cookie`

### 注意事项

- 提取前浏览器必须完全关闭
- 浏览器中必须已登录对应平台
- Cookie 有过期时间，失效后需重新获取
- `--remote-allow-origins=*` 参数必须添加

详细说明见 `.claude/skills/douyin-cookie.md`。

## Claude Code 开发环境部署

### 1. 安装 Skills

```bash
# Windows (PowerShell)
Copy-Item .claude\skills\*.md "$env:USERPROFILE\.claude\skills\"

# macOS / Linux
cp .claude/skills/*.md ~/.claude/skills/
```

### 2. 安装 Python 依赖

```bash
cd D:\workspace\projects\SnatchIt  # 替换为你的路径
pip install -e .
```

### 3. 运行应用

```bash
python -m snatchit.main
```

### 4. 开发工作流

- 修改代码后直接测试：`python -m snatchit.main`
- 使用 Claude Code 时，skills 会自动加载提供 f2 相关指导
- 提交前确保代码符合现有规范

## 已知问题

1. **Twitter Cookie 依赖**: Twitter 下载需要有效的登录 Cookie，且需要 `X-Csrf-Token`（从浏览器开发者工具获取 ct0 值）
2. **代理问题**: 部分地区下载 Twitter 视频需要代理
3. **Cookie 过期**: 自动获取的 Cookie 会过期，需定期重新获取
4. **Bark 通知**: Bark 通知 URL 未配置时会返回 405，但不影响下载功能

## TODO

- [ ] 支持批量下载（链接列表）
- [ ] 下载历史记录
- [ ] 代理设置 UI
- [ ] macOS `.app` bundle 打包（当前为非 `.app` 可执行文件 + `_internal/`）
- [ ] Windows 平台打包和运行验证
- [ ] Linux 平台打包和运行验证
- [ ] 自动更新检测
- [ ] 更多平台支持（Bilibili、Instagram 等）

## 开发进度

- [x] 项目骨架和仓库创建
- [x] Claude Code 配置和 Skills
- [x] 基础文档（README、CLAUDE.md、DEVELOPMENT.md）
- [x] 核心 UI 组件
- [x] f2 封装层
- [x] Cookie 获取模块
- [x] 日志面板和配置持久化
- [x] Cookie 获取异步化（后台线程）
- [x] 抖音链接自动标准化
- [x] PyInstaller 全量打包方案（替代 Nuitka）
- [x] 打包后数据库和配置文件写入权限修复
- [x] X-Csrf-Token 通过 kwargs 传递（无需写 f2 conf.yaml）
- [ ] 测试和验证（抖音已验证，Twitter 待验证）

## 开发日志

### 2026-04-13

- **PyInstaller 打包方案**：从 Nuitka 切换到 PyInstaller，解决 websockets 12.x lazy import 导致子包遗漏的问题
- **f2 版本号修复**：`__version__` 改为 `0.0.1.7+gekko.1`（PEP 440 格式），推送到 fork 远程分支
- **抖音 caption 字段**：`f2/apps/douyin/db.py` 添加 `caption` 和 `caption_raw` 字段
- **打包后路径适配**：
  - 新增 `get_data_dir()` 返回可写路径（exe 同级目录）
  - `CONFIGS_DIR` 改用 `get_data_dir()`
  - `os.chdir` 确保 f2 创建的 `.db` 文件在可写目录
- **X-Csrf-Token 修复**：通过 `kwargs["X-Csrf-Token"]` 传递，利用 `TwitterCrawler.__init__` 已有的 kwargs 优先读取逻辑，不再需要写 f2 的 `conf.yaml`（打包后该文件位于 `_internal/` 只读目录）
- **清理无用代码**：移除 `save_csrf_to_f2_conf()` 和 `_find_f2_conf_yaml()` 函数
- **文档更新**：创建 `docs/BUILD.md`，更新 `docs/DEVELOPMENT.md`、`docs/PACKING_STATUS.md`、`docs/F2_LOCAL_FIXES.md`
