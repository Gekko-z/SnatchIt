"""SnatchIt 应用配置管理"""

from pathlib import Path
from PyQt6.QtCore import QSettings


# 应用信息
APP_NAME = "SnatchIt"
APP_VERSION = "0.1.0"
APP_ORG = "Gekko-z"

# 默认配置
DEFAULTS = {
    "platform": "twitter",       # 默认平台: douyin | twitter
    "save_path": str(Path.home() / "Downloads" / "SnatchIt"),
    "naming_template": "{create}_{desc}",
    "folderize": True,
    "timeout": 10,
    "max_retries": 5,
}

# 平台配置
PLATFORM_CONFIG = {
    "douyin": {
        "label": "抖音",
        "url_placeholder": "https://www.douyin.com/video/...",
        "modes": ["one", "post"],
        "default_mode": "one",
    },
    "twitter": {
        "label": "Twitter / X",
        "url_placeholder": "https://x.com/user/status/...",
        "modes": ["one", "post", "like", "bookmark"],
        "default_mode": "one",
    },
}


class AppConfig:
    """应用配置管理器"""

    def __init__(self):
        self.settings = QSettings(APP_ORG, APP_NAME)

    def get(self, key: str, default=None):
        """获取配置值"""
        if default is None:
            default = DEFAULTS.get(key)
        value = self.settings.value(key, default)
        # 类型转换
        if key in ("folderize",):
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if key in ("timeout", "max_retries"):
            return int(value)
        return value

    def set(self, key: str, value):
        """设置配置值"""
        self.settings.setValue(key, value)

    def get_platform_config(self, platform: str) -> dict:
        """获取指定平台的配置"""
        return PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG["twitter"])

    def get_platforms(self) -> list:
        """获取所有支持的平台列表"""
        return list(PLATFORM_CONFIG.keys())

    def get_cookie(self, platform: str) -> str:
        """获取指定平台的 Cookie"""
        return self.settings.value(f"cookies/{platform}", "")

    def set_cookie(self, platform: str, cookie: str):
        """设置指定平台的 Cookie"""
        self.settings.setValue(f"cookies/{platform}", cookie)

    def get_window_geometry(self) -> bytes:
        """获取窗口几何信息"""
        return self.settings.value("window/geometry", b"")

    def save_window_geometry(self, geometry: bytes):
        """保存窗口几何信息"""
        self.settings.setValue("window/geometry", geometry)
