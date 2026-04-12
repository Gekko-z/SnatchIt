"""f2 下载器封装 - 在 QThread 中运行异步任务"""

import asyncio
import logging
import re
from urllib.parse import parse_qs, urlparse

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


def normalize_douyin_url(url: str) -> str:
    """
    标准化抖音链接，将用户页+modal_id 格式转换为标准 video 格式。

    支持的输入格式:
    - https://www.douyin.com/user/xxx?modal_id=7627395225548499377
    - https://www.douyin.com/video/7627110051009898361
    - https://v.douyin.com/xxx/ (短链接)

    Returns:
        标准化后的 URL
    """
    # 已经是标准 video/note 链接，直接返回
    if re.search(r'(video|note)/', url):
        return url

    # 短链接，直接返回（f2 会通过重定向解析）
    if 'v.douyin.com' in url:
        return url

    # 尝试从 user 页链接中提取 modal_id
    try:
        parsed = urlparse(url)
        if 'douyin.com' in parsed.netloc:
            params = parse_qs(parsed.query)
            modal_id = params.get('modal_id', [None])[0]
            if modal_id:
                return f"https://www.douyin.com/video/{modal_id}"
    except Exception:
        pass

    return url


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


class DownloadWorker(QThread):
    """下载工作线程"""

    # 信号定义
    log = pyqtSignal(str)          # 日志消息
    progress = pyqtSignal(int, str)  # 进度百分比, 状态文本
    finished = pyqtSignal(bool, str)  # 成功/失败, 消息

    def __init__(
        self,
        platform: str,
        url: str,
        cookie: str,
        save_path: str,
        mode: str = "one",
        folderize: bool = True,
        naming: str = "{create}_{desc}",
        parent=None,
    ):
        super().__init__(parent)
        self.platform = platform
        self.url = url
        self.cookie = cookie
        self.save_path = save_path
        self.mode = mode
        self.folderize = folderize
        self.naming = naming

    def run(self):
        """在线程中运行下载任务"""
        # 安装日志转发 handler
        qt_handler = QtLogHandler(self.log)
        root_logger = logging.getLogger()
        root_logger.addHandler(qt_handler)
        root_logger.setLevel(logging.DEBUG)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._do_download())
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            loop.close()
            root_logger.removeHandler(qt_handler)

    async def _do_download(self):
        """执行下载逻辑"""
        self.progress.emit(10, "正在初始化...")
        self.log.emit(f"平台: {self.platform}")
        self.log.emit(f"链接: {self.url}")

        # 抖音链接标准化（user页+modal_id -> video/xxx）
        if self.platform == "douyin":
            original_url = self.url
            self.url = normalize_douyin_url(self.url)
            if self.url != original_url:
                self.log.emit(f"链接已转换: {self.url}")

        # 构建 kwargs
        kwargs = self._build_kwargs()

        self.progress.emit(20, "正在解析链接...")

        if self.platform == "douyin":
            await self._download_douyin(kwargs)
        elif self.platform == "twitter":
            await self._download_twitter(kwargs)
        else:
            self.finished.emit(False, f"不支持的平台: {self.platform}")
            return

        self.progress.emit(100, "下载完成")
        self.finished.emit(True, "下载完成")

    def _build_kwargs(self) -> dict:
        """构建 f2 所需的参数"""
        kwargs = {
            "url": self.url,
            "mode": self.mode,
            "path": self.save_path,
            "cookie": self.cookie,
            "folderize": self.folderize,
            "naming": self.naming,
            "timeout": 10,
            "max_retries": 5,
        }

        # Twitter 需要额外的 headers
        if self.platform == "twitter":
            # 从 cookie 中提取 ct0 作为 X-Csrf-Token
            ct0 = self._extract_ct0(self.cookie)
            kwargs["headers"] = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
                ),
                "Referer": "https://twitter.com/",
                "Authorization": (
                    "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%"
                    "3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
                ),
                "X-Csrf-Token": ct0,
            }

        return kwargs

    def _extract_ct0(self, cookie: str) -> str:
        """从 Cookie 字符串中提取 ct0 值"""
        for item in cookie.split(";"):
            item = item.strip()
            if item.startswith("ct0="):
                return item.split("=", 1)[1]
        return ""

    async def _download_douyin(self, kwargs: dict):
        """下载抖音视频"""
        from f2.apps.douyin.utils import AwemeIdFetcher
        from f2.apps.douyin.handler import DouyinHandler

        self.log.emit("正在解析抖音链接...")
        aweme_id = await AwemeIdFetcher.get_aweme_id(self.url)
        self.log.emit(f"视频 ID: {aweme_id}")

        self.progress.emit(40, "正在获取视频信息...")
        handler = DouyinHandler(kwargs=kwargs)
        await handler.handle_one_video()

        self.progress.emit(90, "正在下载视频...")

    async def _download_twitter(self, kwargs: dict):
        """下载 Twitter 视频"""
        from f2.apps.twitter.utils import TweetIdFetcher
        from f2.apps.twitter.handler import TwitterHandler

        self.log.emit("正在解析推文链接...")
        tweet_id = await TweetIdFetcher.get_tweet_id(self.url)
        self.log.emit(f"推文 ID: {tweet_id}")

        self.progress.emit(40, "正在获取推文信息...")
        handler = TwitterHandler(kwargs=kwargs)
        await handler.handle_one_tweet()

        self.progress.emit(90, "正在下载视频...")
