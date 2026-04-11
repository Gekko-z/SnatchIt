# Skills 部署说明

## 概述

本项目在 `.claude/skills/` 目录下包含了 Claude Code 开发本项目所需的技能文档。当你在其他电脑上使用 Claude Code 开发时，需要将这些 skills 安装到目标机器的 Claude Code 中。

## 包含的 Skills

| 文件 | 说明 |
|------|------|
| `f2-video-downloader.md` | f2 视频下载库使用指南，包含 CLI 命令、API 调用、配置文件、工具类速查表等 |
| `douyin-cookie.md` | 抖音 Cookie 自动获取指南，通过浏览器远程调试 (WebSocket) 提取已登录 Cookie |

## 安装方法

### Windows

将 `.claude/skills/` 下的所有 `.md` 文件复制到：

```
%USERPROFILE%\.claude\skills\
```

例如：
```powershell
Copy-Item .claude\skills\*.md "$env:USERPROFILE\.claude\skills\"
```

### macOS / Linux

将 `.claude/skills/` 下的所有 `.md` 文件复制到：

```
~/.claude/skills/
```

例如：
```bash
cp .claude/skills/*.md ~/.claude/skills/
```

## 验证

安装完成后，在 Claude Code 对话中提到以下关键词，对应的 skill 应自动加载：

- "f2"
- "download douyin video"
- "download twitter video"
- "download tiktok video"
