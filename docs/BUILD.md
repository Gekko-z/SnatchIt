# SnatchIt 打包说明

## 概述

SnatchIt 采用 **PyInstaller** 进行全量打包，将 Python 运行时、PyQt6、f2 及其所有依赖打包为独立可执行文件，用户无需安装 Python 即可运行。

## 打包产物

```
dist/SnatchIt/
├── SnatchIt          # 可执行文件（macOS/Linux）或 SnatchIt.exe（Windows）
└── _internal/        # 所有依赖（Python、PyQt6、f2、websockets 等）
```

## 环境要求

| 平台 | Python 版本 | 备注 |
|------|------------|------|
| Windows | 3.10+ | 推荐 3.11 |
| macOS (Apple Silicon) | 3.10+ | 推荐 3.11，arm64 |
| macOS (Intel) | 3.10+ | 需 Intel 版 Python |
| Linux (x86_64) | 3.10+ | 需安装系统依赖见下文 |

## 打包步骤

### 1. 安装依赖

```bash
# 安装 SnatchIt 及其所有依赖（含 f2 fork）
pip install -e .

# 安装 PyInstaller
pip install pyinstaller
```

### 2. 执行打包

```bash
python build.py
```

脚本会自动：
1. 检查 Python 版本（>= 3.10）
2. 检查 PyInstaller 和 f2 是否已安装
3. 验证 f2 版本号（必须为 `0.0.1.7.gekko*` 自定义版本）
4. 生成默认 configs（douyin.yaml、twitter.yaml）
5. 调用 PyInstaller 打包
6. 输出到 `dist/SnatchIt/`

### 3. 验证产物

```bash
# macOS
open dist/SnatchIt/SnatchIt

# Windows
dist\SnatchIt\SnatchIt.exe

# Linux
dist/SnatchIt/SnatchIt
```

## 平台差异

### macOS

- 当前使用 `console=True`（保留终端输出，方便调试）
- 发布时可改为 `console=False`（隐藏终端，仅显示 GUI）
- 输出为 `dist/SnatchIt/SnatchIt` 可执行文件
- 如需 `.app` bundle，需修改 spec 使用 `BUNDLE` 模式

### Windows

- `console=True` 保留控制台输出
- 输出为 `dist\SnatchIt\SnatchIt.exe`
- 如需无控制台窗口，改为 `console=False`

### Linux

- 需要系统安装 PyQt6 依赖：`sudo apt install libxcb-xinerama0 libxcb-cursor0`（Debian/Ubuntu）
- 输出为 `dist/SnatchIt/SnatchIt`
- 可能需要 `chmod +x dist/SnatchIt/SnatchIt`

## f2 版本验证

打包时会验证 f2 版本号，确保使用的是自定义修复版本（`0.0.1.7.gekko.*`）。如果版本不匹配会打印警告但不会阻止打包。

f2 fork 地址：https://github.com/Gekko-z/f2@fix/twitter-api-adaptation

修复内容：
- Twitter API `instructions[0] → instructions[1]` 适配
- 抖音 `caption` / `caption_raw` 数据库字段
- 其他自定义修复

## 分发方式

### 方式一：全量打包（推荐，面向普通用户）

用户下载 `dist/SnatchIt/` 整个目录，直接运行可执行文件。无需安装 Python 或任何依赖。

### 方式二：pip install（面向开发者/高级用户）

```bash
pip install git+https://github.com/Gekko-z/SnatchIt@master
```

会自动安装 f2 fork 修复版本。启动时会自动检查 Python 版本和 f2 版本，如不匹配会尝试自动修复。

## 已知问题

1. **pyopenssl 依赖冲突**：f2 的 `cryptography==44.0.1` 与某些环境的 `pyopenssl` 不兼容，但不影响 SnatchIt 运行
2. **PyExecJS**：抖音签名计算需要 Node.js，如未安装可能导致部分功能异常
3. **Linux 系统依赖**：PyQt6 需要 `libxcb` 等系统库

## 文件说明

| 文件 | 说明 |
|------|------|
| `build.py` | PyInstaller 打包脚本，跨平台通用 |
| `snatchit.spec` | PyInstaller 配置文件，定义 hiddenimports、datas、excludes |
| `configs/` | 运行时生成的平台配置文件（douyin.yaml、twitter.yaml） |
