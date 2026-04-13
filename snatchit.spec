# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for SnatchIt

跨平台配置文件，Windows/macOS/Linux 共用。
平台差异在 build.py 中通过 extra_args 处理。
"""

import sys
from pathlib import Path

# --- 动态定位 f2 安装路径 ---
import importlib.util

f2_spec = importlib.util.find_spec("f2")
if f2_spec and f2_spec.origin:
    f2_dir = Path(f2_spec.origin).parent
else:
    print("[错误] 未找到 f2 安装路径，请先执行: pip install -e .")
    sys.exit(1)

# --- Hidden Imports ---
# f2 使用 importlib.import_module 动态加载这些模块，PyInstaller 静态分析无法追踪
hiddenimports = [
    # f2 core
    "f2",
    "f2.__main__",
    "f2.apps",
    "f2.apps.__apps__",
    # f2.apps.douyin
    "f2.apps.douyin",
    "f2.apps.douyin.api",
    "f2.apps.douyin.cli",
    "f2.apps.douyin.crawler",
    "f2.apps.douyin.db",
    "f2.apps.douyin.dl",
    "f2.apps.douyin.filter",
    "f2.apps.douyin.handler",
    "f2.apps.douyin.help",
    "f2.apps.douyin.model",
    "f2.apps.douyin.utils",
    "f2.apps.douyin.algorithm.webcast_signature",
    "f2.apps.douyin.proto.douyin_webcast_pb2",
    # f2.apps.twitter
    "f2.apps.twitter",
    "f2.apps.twitter.api",
    "f2.apps.twitter.cli",
    "f2.apps.twitter.crawler",
    "f2.apps.twitter.db",
    "f2.apps.twitter.dl",
    "f2.apps.twitter.filter",
    "f2.apps.twitter.handler",
    "f2.apps.twitter.help",
    "f2.apps.twitter.model",
    "f2.apps.twitter.utils",
    # f2 core modules
    "f2.cli",
    "f2.cli.cli_commands",
    "f2.cli.cli_console",
    "f2.crawlers",
    "f2.crawlers.base_crawler",
    "f2.db",
    "f2.db.base_db",
    "f2.dl",
    "f2.dl.base_downloader",
    "f2.exceptions",
    "f2.exceptions.api_exceptions",
    "f2.exceptions.conf_exceptions",
    "f2.exceptions.db_exceptions",
    "f2.exceptions.file_exceptions",
    "f2.helps",
    "f2.i18n",
    "f2.i18n.translator",
    "f2.log",
    "f2.log.logger",
    "f2.utils",
    "f2.utils.utils",
    "f2.utils.conf_manager",
    "f2.utils.xbogus",
    "f2.utils.abogus",
    "f2.utils._dl",
    "f2.utils._signal",
    "f2.utils._singleton",
    "f2.utils.json_filter",
    "f2.utils.decorators",
    "f2.utils.conf_manager",
    # websockets (12.x lazy imports)
    "websockets",
    "websockets.legacy",
    "websockets.legacy.client",
    "websockets.legacy.server",
    "websockets.legacy.handshake",
    "websockets.legacy.http",
    "websockets.legacy.protocol",
    "websockets.frames",
    "websockets.connection",
    "websockets.uri",
    "websockets.headers",
    "websockets.auth",
    "websockets_proxy",
    # f2 其他依赖中的动态导入
    "browser_cookie3",
    "execjs",
    "gmssl",
    "gmssl.sm2",
    "gmssl.sm3",
    "gmssl.sm4",
    "aiosqlite",
    "aiofiles",
    "jsonpath_ng",
    "importlib_resources",
    "m3u8",
    "google.protobuf",
    "google.protobuf",
    "cryptography",
    "cryptography.fernet",
    # SnatchIt widgets
    "snatchit",
    "snatchit.config",
    "snatchit.config_manager",
    "snatchit.downloader",
    "snatchit.cookie_fetcher",
    "snatchit.utils",
    "snatchit.widgets",
    "snatchit.widgets.main_window",
    "snatchit.widgets.cookie_panel",
    "snatchit.widgets.link_input",
    "snatchit.widgets.log_panel",
]

# --- Data Files ---
datas = []

# f2 conf/
f2_conf = f2_dir / "conf"
if f2_conf.exists():
    datas.append((str(f2_conf), "f2/conf"))

# f2 languages/
f2_lang = f2_dir / "languages"
if f2_lang.exists():
    datas.append((str(f2_lang), "f2/languages"))

# f2 douyin proto
douyin_proto = f2_dir / "apps" / "douyin" / "proto"
if douyin_proto.exists():
    datas.append((str(douyin_proto), "f2/apps/douyin/proto"))

# f2 douyin algorithm (webcast_signature.js)
douyin_algo = f2_dir / "apps" / "douyin" / "algorithm"
if douyin_algo.exists():
    datas.append((str(douyin_algo), "f2/apps/douyin/algorithm"))

# SnatchIt resources
style_qss = Path("src/snatchit/resources/style.qss")
if style_qss.exists():
    datas.append((str(style_qss), "snatchit/resources"))

# SnatchIt configs（如果存在则包含）
configs_dir = Path("configs")
if configs_dir.exists():
    datas.append((str(configs_dir), "configs"))

# SnatchIt icon
icon_path = Path("src/snatchit/resources/snatchit.ico")
if icon_path.exists():
    datas.append((str(icon_path), "snatchit/resources"))


# --- 平台判断 ---
block_cipher = None

a = Analysis(
    ["src/snatchit/main.py"],
    pathex=[str(Path("src"))],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "pytest_asyncio",
        "black",
        "babel",
        "nuitka",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# --- 平台自适应 ---
if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="SnatchIt",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,  # macOS 先使用 console 模式方便调试
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_entitlements=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="SnatchIt",
    )
elif sys.platform == "win32":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="SnatchIt",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,  # Windows 保留控制台用于调试输出
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon=str(icon_path) if icon_path.exists() else None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="SnatchIt",
    )
else:
    # Linux
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="SnatchIt",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        disable_windowed_traceback=False,
        target_arch=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="SnatchIt",
    )
