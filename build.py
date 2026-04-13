"""PyInstaller 打包脚本 — 跨平台支持 Windows/macOS/Linux

使用方法:
    python build.py

前置依赖:
    pip install pyinstaller
    pip install -e .  (或确保 f2 已安装)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR


F2_REQUIRED_VERSION_PREFIX = "0.0.1.7+gekko"  # 自定义版本号前缀


def check_python_version():
    """检查 Python 版本 >= 3.10"""
    if sys.version_info < (3, 10):
        print(f"[错误] Python >= 3.10 是必需的，当前版本: {sys.version}")
        sys.exit(1)
    print(f"[信息] Python {sys.version} ({sys.executable})")


def check_dependency(name: str, module_name: str = None):
    """检查依赖是否已安装"""
    mod = module_name or name
    try:
        __import__(mod)
        print(f"[信息] {name} 已安装")
    except ImportError:
        print(f"[错误] 未找到 {name}，请先执行: pip install {name}")
        sys.exit(1)


def generate_default_configs():
    """生成默认 configs 目录和 yaml 文件（如果不存在）"""
    configs_dir = PROJECT_ROOT / "configs"
    configs_dir.mkdir(exist_ok=True)

    import yaml

    douyin_config = {
        "douyin": {
            "cookie": "",
            "mode": "one",
            "naming": "{create}_{desc}",
            "path": "./Download",
            "timeout": 10,
            "max_retries": 5,
            "folderize": True,
            "interval": "all",
            "languages": "zh_CN",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
            },
            "bark": {"url": "", "key": ""},
        }
    }

    twitter_config = {
        "twitter": {
            "cookie": "",
            "mode": "one",
            "naming": "{create}_{desc}",
            "path": "./Download",
            "timeout": 10,
            "max_retries": 5,
            "folderize": True,
            "interval": "all",
            "bark": {"url": "", "key": ""},
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://twitter.com/",
                "X-Csrf-Token": "",
            },
        }
    }

    douyin_path = configs_dir / "douyin.yaml"
    if not douyin_path.exists():
        with open(douyin_path, "w", encoding="utf-8") as f:
            yaml.dump(douyin_config, f, default_flow_style=False, allow_unicode=True)
        print(f"[信息] 已生成 {douyin_path}")
    else:
        print(f"[信息] {douyin_path} 已存在")

    twitter_path = configs_dir / "twitter.yaml"
    if not twitter_path.exists():
        with open(twitter_path, "w", encoding="utf-8") as f:
            yaml.dump(twitter_config, f, default_flow_style=False, allow_unicode=True)
        print(f"[信息] 已生成 {twitter_path}")
    else:
        print(f"[信息] {twitter_path} 已存在")


def verify_f2_version():
    """验证 f2 版本号是否为自定义修复版本"""
    import importlib.util

    f2_spec = importlib.util.find_spec("f2")
    if not f2_spec or not f2_spec.origin:
        print("[错误] 未找到 f2 安装路径")
        sys.exit(1)

    f2_dir = Path(f2_spec.origin).parent
    f2_mod = importlib.import_module("f2")
    f2_version = getattr(f2_mod, "__version__", "unknown")

    if f2_version.startswith(F2_REQUIRED_VERSION_PREFIX):
        print(f"[信息] f2 版本验证通过 ({f2_version})")
        print(f"[信息] f2 路径: {f2_dir}")
    else:
        print(f"[警告] f2 版本不匹配 (当前: {f2_version}, 需要: {F2_REQUIRED_VERSION_PREFIX}*)")
        print(f"[信息] f2 路径: {f2_dir}")
        print(f"[警告] 继续使用当前 f2 版本，如遇问题请安装正确的 f2 fork")


def main():
    print("=" * 60)
    print("SnatchIt 打包工具 (PyInstaller)")
    print("=" * 60)

    # Step 1: 检查
    check_python_version()
    check_dependency("PyInstaller", "PyInstaller")
    check_dependency("f2")
    print()

    # Step 2: 验证 f2 版本
    verify_f2_version()
    print()

    # Step 3: 生成 configs
    generate_default_configs()
    print()

    # Step 4: 清理旧的构建产物
    dist_dir = PROJECT_ROOT / "dist"
    build_dir = PROJECT_ROOT / "build"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"[信息] 已清理 {dist_dir}")
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"[信息] 已清理 {build_dir}")

    # Step 5: 运行 PyInstaller
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        str(PROJECT_ROOT / "snatchit.spec"),
    ]

    print(f"执行命令: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"\n打包失败，退出码: {result.returncode}")
        sys.exit(result.returncode)

    # Step 6: 输出结果
    if sys.platform == "darwin":
        output = dist_dir / "SnatchIt"
    elif sys.platform == "win32":
        output = dist_dir / "SnatchIt"
    else:
        output = dist_dir / "SnatchIt"

    if output.exists():
        print("\n" + "=" * 60)
        print(f"打包成功！输出目录: {output}/")
        if sys.platform == "darwin":
            print(f"运行: open {output}/SnatchIt.app/Contents/MacOS/SnatchIt")
        elif sys.platform == "win32":
            print(f"运行: {output}\\SnatchIt.exe")
        else:
            print(f"运行: {output}/SnatchIt")
        print("=" * 60)
    else:
        print(f"\n打包成功但未找到输出目录: {output}")
        sys.exit(1)


if __name__ == "__main__":
    main()
