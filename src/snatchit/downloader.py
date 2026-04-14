"""f2 下载器封装 - 通过 f2 Python API 调用"""

import asyncio
import importlib.util
import logging
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Nuitka 无法追踪 importlib.import_module 的动态导入
# 这些静态导入让 Nuitka 编译 f2 的核心子包及其依赖
import f2
import f2.apps.douyin
import f2.apps.twitter
import f2.crawlers
import rich
import rich.rule

import yaml
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


def _get_log_file() -> str:
    """获取日志文件路径：打包后为 exe 同级 logs/ 目录，开发时为项目根 logs/"""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent.parent.parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    return str(logs_dir / f"snatchit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")


# 初始化文件日志
_log_file = _get_log_file()
_file_handler = logging.FileHandler(_log_file, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
_file_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(_file_handler)
logging.getLogger().setLevel(logging.INFO)
logger.info(f"日志文件: {_log_file}")
logger.info(f"Python: {sys.executable}, frozen: {getattr(sys, 'frozen', False)}")


def normalize_douyin_url(url: str) -> str:
    """
    标准化抖音链接，将用户页+modal_id 格式转换为标准 video 格式。
    """
    if re.search(r"(video|note)/", url):
        return url
    if "v.douyin.com" in url:
        return url
    try:
        parsed = urlparse(url)
        if "douyin.com" in parsed.netloc:
            params = parse_qs(parsed.query)
            modal_id = params.get("modal_id", [None])[0]
            if modal_id:
                return f"https://www.douyin.com/video/{modal_id}"
    except Exception:
        pass
    return url


def _merge_f2_config(platform: str, url: str, save_path: str, config_path: str) -> dict:
    """构建 f2 所需的完整配置参数"""
    with open(config_path, "r", encoding="utf-8") as f:
        custom_conf = yaml.safe_load(f) or {}
    platform_conf = custom_conf.get(platform, {})

    f2_main_conf = {}
    try:
        spec = importlib.util.find_spec("f2")
        if spec and spec.origin:
            f2_dir = Path(spec.origin).parent
            conf_yaml = f2_dir / "conf" / "conf.yaml"
            if conf_yaml.exists():
                with open(conf_yaml, "r", encoding="utf-8") as f:
                    full_conf = yaml.safe_load(f) or {}
                f2_main_conf = full_conf.get("f2", {}).get(platform, {})
    except Exception:
        pass

    kwargs = {
        "url": url,
        "mode": platform_conf.get("mode", "one"),
        "path": save_path,
        "cookie": platform_conf.get("cookie", ""),
        "timeout": platform_conf.get("timeout", 10),
        "max_retries": platform_conf.get("max_retries", 5),
        "folderize": platform_conf.get("folderize", True),
        "naming": platform_conf.get("naming", "{create}_{desc}"),
        "interval": platform_conf.get("interval", "all"),
        "proxies": f2_main_conf.get("proxies", {"http://": None, "https://": None}),
    }

    main_headers = f2_main_conf.get("headers", {})
    custom_headers = platform_conf.get("headers", {})
    kwargs["headers"] = {**main_headers}
    for k, v in custom_headers.items():
        if v:
            kwargs["headers"][k] = v
    kwargs["headers"]["Cookie"] = kwargs["cookie"]

    # 将 X-Csrf-Token 传入 kwargs 顶层，TwitterCrawler 会优先读取
    # 这样无需读写 f2 的 conf.yaml（打包后该文件位于 _internal/ 只读目录）
    csrf_token = custom_headers.get("X-Csrf-Token", "")
    if csrf_token:
        kwargs["X-Csrf-Token"] = csrf_token

    return kwargs


class DownloadWorker(QThread):
    """下载工作线程 - 直接调用 f2 Python API"""

    log = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        platform: str,
        url: str,
        save_path: str,
        config_path: str,
        parent=None,
    ):
        super().__init__(parent)
        self.platform = platform
        self.url = url
        self.save_path = save_path
        self.config_path = config_path

    def run(self):
        """在线程中运行下载任务"""
        # 切换到数据目录（可写），避免 f2 创建 .db 文件时路径不可写而失败
        os.chdir(str(Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent.parent.parent))

        logger.info("=" * 60)
        logger.info("开始下载任务")
        logger.info(f"平台: {self.platform}")
        logger.info(f"URL: {self.url}")
        logger.info(f"保存路径: {self.save_path}")
        logger.info(f"配置路径: {self.config_path}")

        qt_handler = QtLogHandler(self.log)
        root_logger = logging.getLogger()
        root_logger.addHandler(qt_handler)

        try:
            self._run_f2_api()
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"下载异常: {e}\n{error_trace}")
            self.finished.emit(False, str(e))
        finally:
            root_logger.removeHandler(qt_handler)
            logger.info("下载任务结束")

    def _run_f2_api(self):
        """通过 f2 Python API 执行下载"""
        self.progress.emit(10, "正在初始化...")

        if not self.config_path or not Path(self.config_path).exists():
            msg = f"配置文件不存在: {self.config_path}"
            logger.error(msg)
            self.finished.emit(False, msg)
            return

        self.progress.emit(20, "正在解析链接...")
        self.progress.emit(40, "正在获取视频信息...")

        # 构建配置参数
        kwargs = _merge_f2_config(self.platform, self.url, self.save_path, self.config_path)
        kwargs["app_name"] = self.platform

        logger.info(f"f2 配置: mode={kwargs.get('mode')}, naming={kwargs.get('naming')}")
        logger.info(f"f2 headers: {kwargs.get('headers', {})}")

        try:
            asyncio.run(self._run_f2_handler(kwargs))
            self.progress.emit(100, "下载完成")
            self.finished.emit(True, "下载完成")
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"f2 handler 异常: {e}\n{error_trace}")
            error_msg = str(e)
            if "APIResponseError" in error_msg or "403" in error_msg:
                error_msg = f"API 请求失败，请检查 Cookie 是否有效: {e}"
            self.finished.emit(False, error_msg)

    async def _run_f2_handler(self, kwargs: dict):
        """调用 f2 的 handler"""
        app_name = kwargs["app_name"]
        logger.info(f"正在加载 f2.apps.{app_name}.handler ...")
        app_module = importlib.import_module(f"f2.apps.{app_name}.handler")
        logger.info(f"f2 handler 加载完成，开始执行下载...")
        await app_module.main(kwargs)
        logger.info("f2 handler 执行完毕")

    def cancel(self):
        """取消下载"""
        self.terminate()
        self.log.emit("[用户] 已取消下载")


class QtLogHandler(logging.Handler):
    """将 Python logging 输出转发到 Qt 信号"""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.signal.emit(msg)
        except Exception:
            self.handleError(record)
