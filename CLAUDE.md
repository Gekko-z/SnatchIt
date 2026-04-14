# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**SnatchIt** 是一个跨平台视频下载 GUI 客户端，支持抖音和 Twitter/X 平台的视频下载。基于 PyQt6 构建，底层使用 f2 库进行实际的视频抓取和下载。

## 技术栈

- **GUI 框架**: PyQt6
- **异步支持**: asyncio + QThread
- **视频下载**: f2 (fork 版本: https://github.com/Gekko-z/f2, 分支: main)
- **Cookie 获取**: 浏览器远程调试 (WebSocket, Chrome DevTools Protocol)
- **打包工具**: Nuitka (后续)
- **Python**: >= 3.10

## 目录结构

```
├── .claude/                    # Claude Code 配置和 skills
│   ├── settings.json
│   └── skills/
│       ├── f2-video-downloader.md  # f2 库使用指南
│       ├── douyin-cookie.md        # 抖音 Cookie 获取
│       └── DEPLOY.md               # Skills 部署说明
├── CLAUDE.md                   # 本文件
├── src/
│   └── snatchit/
│       ├── __init__.py
│       ├── main.py             # PyQt6 应用入口
│       ├── config.py           # 配置管理 (QSettings)
│       ├── downloader.py       # f2 封装层 (QThread + asyncio)
│       ├── cookie_fetcher.py   # Cookie 获取 (WebSocket)
│       ├── widgets/            # UI 组件
│       └── resources/          # 样式表等资源
├── docs/
│   └── DEVELOPMENT.md          # 开发者文档
├── pyproject.toml
├── requirements.txt
├── build.py                    # Nuitka 打包脚本
└── README.md
```

## 开发命令

```bash
# 安装依赖
cd D:\workspace\projects\SnatchIt
pip install -e .

# 运行应用
python -m snatchit.main
# 或
snatchit

# 打包为 exe (后续)
python build.py
```

## f2 库集成

f2 是本项目的核心下载引擎。使用 fork 版本（含 Twitter API 修复）：
- **仓库**: https://github.com/Gekko-z/f2
- **分支**: main

### 已知 f2 修复

1. **instructions[0] → instructions[1]**: Twitter API 响应结构变化
2. **extract_desc None 检查**: 防止 full_text 为 None 时崩溃
3. **tweet_video_url MP4 过滤**: 过滤 M3U8，选择最高码率 MP4

详细 f2 用法请参阅 `.claude/skills/f2-video-downloader.md`。

## Cookie 获取机制

通过浏览器远程调试端口 (Chrome DevTools Protocol) 获取 Cookie：
1. 启动 Edge/Chrome 并开启 `--remote-debugging-port`
2. 通过 WebSocket 连接
3. 执行 `document.cookie` JavaScript 表达式
4. 返回完整 Cookie 字符串

支持抖音 (douyin.com) 和 Twitter (x.com)。详细说明见 `.claude/skills/douyin-cookie.md`。

## 开发规范

- 代码注释使用中文
- 组件命名使用 PascalCase (QWidget 子类)
- 函数/变量命名使用 snake_case
- 所有异步下载操作在 QThread 中运行，避免阻塞 UI
- 日志通过自定义 logging.Handler 转发到 PyQt 信号

## 下载流程

### 抖音
```
URL → AwemeIdFetcher.get_aweme_id(url) → aweme_id
→ DouyinHandler(kwargs).handle_one_video() → 下载
```

### Twitter
```
URL → TweetIdFetcher.get_tweet_id(url) → tweet_id
→ TwitterHandler(kwargs).handle_one_tweet() → 下载
```

kwargs 必须包含: `url`, `mode`, `path`, `cookie`, 可选: `folderize`, `naming`, `headers`
