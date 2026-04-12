# 打包状态备忘 - 2026-04-12

## 当前进度

### 已完成
- `downloader.py` 已从 subprocess 方式改为 f2 Python API 直接调用（`asyncio.run` + `importlib`）
- `downloader.py` 中添加了静态 `import f2` / `import f2.apps.douyin` / `import f2.apps.twitter` 等
- `main_window.py` 已修正 `DownloadWorker` 参数（`platform, url, save_path, config_path`）
- `build.py` 已重构为从项目 `lib/f2` 取 f2（自动从 f2-repo 复制）
- `build.py` 使用 `.pth` 文件方式让 Nuitka 发现 f2 包
- websockets 和 f2 源码 .py 文件会在打包后手动复制到 dist
- f2 的 namespace 子包已创建 `__init__.py`（`lib/f2/apps/douyin/` 等）

### 待解决
**Nuitka 编译后 dist 中 f2.apps 不可用** — 即使 `--include-package=f2` 生效，Nuitka 也不会编译 namespace 包的子模块。目前的方案是打包后手动复制 .py 文件，但运行时这些 .py 文件无法找到 Nuitka 编译的 rich 等依赖。

**最后的构建命令**:
```
build.py 使用 .pth 文件 + --include-package=f2 --include-package=rich
```
编译成功但 `import f2.apps.douyin.handler` 在 dist 中报 `No module named 'rich'`。

### f2 的修改记录
- 本地 fork: `D:\workspace\projects\f2-repo`
- 分支: `fix/twitter-api-adaptation`
- 修改已记录在 `docs/F2_LOCAL_FIXES.md`
- 涉及 `instructions[0]→instructions[1]`、`extract_desc None 检查`、`tweet_video_url MP4 过滤`

### 下一个尝试方向
1. 确认 `.pth` 方式是否让 Nuitka 真正编译了 f2（检查 dist/f2 中是否有 .pyd 文件）
2. 如果 Nuitka 编译了 f2 但 .py 文件覆盖了 .pyd 导入，考虑只复制未被编译的子模块 .py 文件
3. 或者考虑用 `--onefile` 模式打包，避免模块路径问题
4. 或者考虑降低 websockets 版本到 13+（不使用 lazy imports）

### 文件变更列表
- `src/snatchit/downloader.py` — API 方式调用 f2 + 静态导入 f2 + 文件日志
- `src/snatchit/widgets/main_window.py` — 修正 DownloadWorker 参数
- `src/snatchit/utils.py` — `get_bundle_dir()` 工具函数
- `src/snatchit/config_manager.py` — 动态路径查找 + `save_csrf_to_f2_conf()`
- `src/snatchit/widgets/cookie_panel.py` — lambda 闭包修复 + csrf 自动提取
- `build.py` — 完整重写，.pth + 自动复制 f2 + websockets 源码
- `docs/F2_LOCAL_FIXES.md` — f2 本地修改记录
- `pyproject.toml` — f2 git 依赖

### 环境清理记录
- site-packages 中的 f2 已从 editable 改为正式安装（`pip install D:\workspace\projects\f2-repo`）
- 手动创建了 f2 子包的 `__init__.py`（apps/douyin, apps/twitter 等）
- site-packages/f2 中也有对应的 `__init__.py`
