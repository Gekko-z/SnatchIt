"""运行时工具函数"""

import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    """获取运行时目录。

    - 打包后：返回 exe 所在目录（onedir 模式下为 .dist 目录）
    - 开发模式：返回项目根目录
    """
    if getattr(sys, "frozen", False):
        # Nuitka 打包模式：sys.executable 是解释器路径，在 exe 同级目录
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent
