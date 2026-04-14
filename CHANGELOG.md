# Changelog

本项目的所有变更都将记录在此文件中。
格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)、
本项目遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [Unreleased]

### Changed

- 移除 Cookie 面板中的 X-Csrf-Token 输入框和保存按钮，改为从 Cookie 自动提取 ct0 并保存到 yaml headers。
- 默认日志级别改为 INFO，减少日常日志文件体积。
- 日志面板切换级别时同步修改底层 root logger，实现真正的动态级别切换。
- DEBUG 模式下完整打印 Twitter API 响应 JSON，移除字符截断限制（依赖 f2 fork）。

## [0.1.0] - 2026-04-14

### Added

- 初始版本，基于 PyQt6 的跨平台视频下载 GUI 客户端。
- 支持抖音和 Twitter/X 平台的视频下载。
- 基于 f2 库进行视频抓取和下载。
- 通过浏览器远程调试 (WebSocket, Chrome DevTools Protocol) 获取 Cookie。
- 自定义下载路径、命名模板、文件夹分类等配置。
- 日志面板支持 INFO/DEBUG 级别切换。
- Nuitka 打包支持。
