"""YAML 配置文件管理器"""

from pathlib import Path

import yaml

from snatchit.utils import get_data_dir

# 项目 configs 目录（可写路径：打包后为 exe 同级目录）
CONFIGS_DIR = get_data_dir() / "configs"


PLATFORM_CONFIG_FILES = {
    "douyin": CONFIGS_DIR / "douyin.yaml",
    "twitter": CONFIGS_DIR / "twitter.yaml",
}

DEFAULT_CONTENTS = {
    "douyin": {
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
            "bark": {
                "url": "",
                "key": "",
            },
        }
    },
    "twitter": {
        "twitter": {
            "cookie": "",
            "mode": "one",
            "naming": "{create}_{desc}",
            "path": "./Download",
            "timeout": 10,
            "max_retries": 5,
            "folderize": True,
            "interval": "all",
            "bark": {
                "url": "",
                "key": "",
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://twitter.com/",
                "X-Csrf-Token": "",
            },
        }
    },
}


def ensure_config_exists(platform: str) -> str:
    """
    确保指定平台的 yaml 配置文件存在，不存在则自动创建。

    Returns:
        配置文件的绝对路径
    """
    config_path = PLATFORM_CONFIG_FILES.get(platform)
    if not config_path:
        return ""

    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        content = DEFAULT_CONTENTS.get(platform, {})
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(content, f, default_flow_style=False, allow_unicode=True)

    return str(config_path.absolute())


def save_cookie_to_yaml(platform: str, cookie: str) -> tuple[bool, str]:
    """直接将 Cookie 写入 yaml 配置文件"""
    config_path = ensure_config_exists(platform)
    if not config_path:
        return False, "配置文件路径无效"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        if platform not in config:
            config[platform] = {}
        config[platform]["cookie"] = cookie
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True, "Cookie 已保存到配置文件"
    except Exception as e:
        return False, f"写入配置文件失败: {e}"


def read_cookie(platform: str) -> str:
    """从 yaml 配置文件中读取 cookie"""
    config_path = ensure_config_exists(platform)
    if not config_path:
        return ""

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return config.get(platform, {}).get("cookie", "")
    except Exception:
        return ""

