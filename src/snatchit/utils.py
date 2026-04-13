"""运行时工具函数"""

import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    """获取运行时资源目录（只读，用于读取 assets、style.qss 等）。

    - PyInstaller 打包后：返回 _MEIPASS（临时解压目录）
    - Nuitka 打包后：返回 exe 所在目录
    - 开发模式：返回项目根目录
    """
    if getattr(sys, "_MEIPASS", None):
        # PyInstaller 模式
        return Path(sys._MEIPASS)
    if getattr(sys, "frozen", False):
        # Nuitka 打包模式
        return Path(sys.executable).parent
    # 开发模式
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """获取运行时数据目录（可写，用于 db、yaml 配置等持久化文件）。

    - 打包后（PyInstaller/Nuitka）：返回可执行文件同级目录
    - 开发模式：返回项目根目录
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent
