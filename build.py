"""Nuitka 打包脚本 — 将 SnatchIt + f2 打包为独立可执行文件

使用方法:
    python build.py

依赖:
    pip install nuitka
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent  # 项目根目录


def ensure_local_f2() -> Path:
    """确保项目内有 lib/f2 副本"""
    local_f2 = SCRIPT_DIR / "lib" / "f2"
    if local_f2.exists() and (local_f2 / "__init__.py").exists():
        return local_f2
    f2_repo = SCRIPT_DIR.parent / "f2-repo" / "f2"
    if not f2_repo.exists():
        print(f"[错误] 未找到 f2-repo: {f2_repo}")
        sys.exit(1)
    print(f"[信息] 从 {f2_repo} 复制 f2 到 {local_f2} ...")
    if local_f2.exists():
        shutil.rmtree(local_f2)
    shutil.copytree(f2_repo, local_f2)
    print(f"[信息] 已复制 f2 到 {local_f2}")
    return local_f2


def fix_f2_namespace_packages(f2_dir: Path):
    """为 f2 的 namespace 子包创建空的 __init__.py"""
    subdirs = ["apps", "apps/douyin", "apps/twitter", "apps/tiktok", "apps/bark",
               "apps/weibo", "crawlers", "db", "dl", "i18n", "log"]
    for sub in subdirs:
        init = f2_dir / sub / "__init__.py"
        if not init.exists():
            init.touch()


def install_f2_temporarily() -> str:
    """将 lib/f2 临时安装到 site-packages（非 editable），返回 .pth 文件路径"""
    import site
    site_pkgs = site.getsitepackages()[0]  # e.g. C:\Python\Lib\site-packages
    pth_path = Path(site_pkgs) / "_snatchit_f2_build.pth"
    lib_f2_parent = str(SCRIPT_DIR / "lib")
    pth_path.write_text(lib_f2_parent, encoding="utf-8")
    return str(pth_path)


def cleanup_f2_installation(pth_path: str):
    """删除临时 .pth 文件"""
    try:
        Path(pth_path).unlink()
    except Exception:
        pass


def _copy_py_files_only(src_dir: Path, dst_dir: Path):
    """递归复制 Python 包的 .py 文件"""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        if item.name == "__pycache__":
            continue
        if item.is_dir():
            _copy_py_files_only(item, dst_dir / item.name)
        elif item.suffix == ".py":
            shutil.copy2(item, dst_dir / item.name)


def _copy_f2_source(src_dir: Path, dst_dir: Path):
    """复制 f2 源码 .py 文件到 dist（跳过 conf）"""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        if item.name == "__pycache__":
            continue
        if item.name == "conf":
            continue
        if item.is_dir():
            _copy_py_files_only(item, dst_dir / item.name)
        elif item.suffix == ".py":
            shutil.copy2(item, dst_dir / item.name)


def main():
    project_root = SCRIPT_DIR
    configs_dir = project_root / "configs"
    local_f2 = ensure_local_f2()
    f2_conf_dir = local_f2 / "conf"

    if not (f2_conf_dir / "conf.yaml").exists():
        print("[错误] 未找到 f2/conf/conf.yaml")
        sys.exit(1)

    # 修复 namespace 包
    fix_f2_namespace_packages(local_f2)

    # 将 lib/f2 临时注册到 site-packages，让 Nuitka 能找到它
    pth_file = install_f2_temporarily()
    print(f"[信息] 已创建临时 .pth: {pth_file}")

    try:
        # websockets 源码路径（12.x 使用 lazy imports）
        import importlib.util
        ws_spec = importlib.util.find_spec("websockets")
        ws_dir = Path(ws_spec.origin).parent if ws_spec and ws_spec.origin else None

        # Nuitka 参数
        cmd = [
            sys.executable,
            "-m", "nuitka",
            "--assume-yes-for-downloads",
            "--standalone",
            "--output-dir=dist",
            "--output-filename=SnatchIt",
            f"--include-data-dir={configs_dir}=configs",
            f"--include-data-dir={f2_conf_dir}=f2/conf",
            # 现在 Nuitka 能找到 f2 了（通过 .pth 文件）
            "--include-package=f2",
            # 包含 f2 的依赖
            "--include-package=rich",
            "--include-package=jsonpath_ng",
            "--include-package=httpx",
            "--include-package=pydantic",
            "--enable-plugin=pyqt6",
            "--nofollow-import-to=pytest",
            "--windows-console-mode=attach",
            str(project_root / "src" / "snatchit" / "main.py"),
        ]

        print("=" * 60)
        print("SnatchIt 打包工具")
        print("=" * 60)
        print(f"项目目录: {project_root}")
        print(f"f2 目录:  {local_f2}")
        print(f"f2 conf:  {f2_conf_dir}")
        print(f"输出目录: {project_root / 'dist'}")
        print("-" * 60)
        print(f"执行命令: {' '.join(cmd)}")
        print("-" * 60)

        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode != 0:
            print(f"\n打包失败，退出码: {result.returncode}")
            sys.exit(result.returncode)

        dist_dir = project_root / "dist" / "main.dist"
        if not dist_dir.exists():
            print(f"\n打包成功但未找到输出目录: {dist_dir}")
            sys.exit(1)

        # 手动复制 f2 和 websockets 源码 .py 文件到 dist
        # （Nuitka 可能没有编译所有动态导入的子模块）
        dist_f2 = dist_dir / "f2"
        print(f"[信息] 复制 f2 源码到 {dist_f2} ...")
        _copy_f2_source(local_f2, dist_f2)
        print(f"[信息] f2 源码复制完成")

        if ws_dir:
            dist_ws = dist_dir / "websockets"
            print(f"[信息] 复制 websockets 源码到 {dist_ws} ...")
            _copy_py_files_only(ws_dir, dist_ws)
            print(f"[信息] websockets 源码复制完成")

        # 复制 python.exe
        python_exe = Path(sys.executable)
        target = dist_dir / "python.exe"
        if not target.exists():
            shutil.copy2(python_exe, target)
            print(f"[信息] 已复制 python.exe 到 {target}")

        print("\n打包成功！输出目录: dist/main.dist/")

    finally:
        cleanup_f2_installation(pth_file)
        print(f"[信息] 已清理临时 .pth 文件")


if __name__ == "__main__":
    main()
