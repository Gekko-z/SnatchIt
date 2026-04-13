# 打包状态 - 开发日志

## 2026-04-13 最新状态

### 打包方案：PyInstaller 全量打包

- **打包工具**: PyInstaller 6.19.0
- **输出产物**: `dist/SnatchIt/`（包含可执行文件 + `_internal/` 依赖目录）
- **平台**: 当前为 macOS arm64，Windows/Linux 同理
- **f2 版本**: `0.0.1.7+gekko.1`（自定义版本，符合 PEP 440）

### 已完成
- [x] PyInstaller 打包脚本 `build.py`
- [x] PyInstaller 配置 `snatchit.spec`
- [x] `get_bundle_dir()` / `get_data_dir()` 运行时路径适配
- [x] 数据库文件（`.db`）创建在可写目录（exe 同级）
- [x] YAML 配置文件（`configs/`）创建在可写目录
- [x] X-Csrf-Token 通过 kwargs 传递，不再需要写 f2 的 conf.yaml
- [x] 抖音下载功能验证通过
- [x] f2 fork 版本号推送至远程分支
- [x] 打包文档 `docs/BUILD.md`
- [x] 打包后无需系统安装 Python 或 f2，产物完全独立

### 待验证
- [ ] Twitter 下载功能验证
- [ ] Windows 平台打包和运行验证
- [ ] Linux 平台打包和运行验证

## 历史备忘（已解决）

### Nuitka 方案（已废弃）

Nuitka 的静态分析无法追踪 `websockets` 12.x 的 lazy import，导致子包遗漏。且 namespace 包的子模块无法被 Nuitka 正确编译，最终选择 PyInstaller 方案。

### 打包后路径问题（已解决）

- **问题 1**: f2 创建的 `.db` 文件路径为相对路径，在 `.app` bundle 内部不可写
  - **解决**: `DownloadWorker.run()` 开头 `os.chdir` 到 exe 同级目录
- **问题 2**: `configs/` 在 `_internal/` 只读目录
  - **解决**: `CONFIGS_DIR` 使用 `get_data_dir()` 指向 exe 同级目录
- **问题 3**: f2 的 `conf.yaml` 在 `_internal/f2/conf/` 只读，X-Csrf-Token 无法写入
  - **解决**: `TwitterCrawler.__init__` 已支持从 kwargs 读取 `X-Csrf-Token`，通过 `downloader.py` 传递，不再需要写 conf.yaml
