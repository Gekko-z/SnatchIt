"""Cookie 获取器 - 通过浏览器远程调试端口获取 Cookie"""

import json
import time
import subprocess
import urllib.request
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# 浏览器安装路径
BROWSER_PATHS = {
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
}


@dataclass
class CookieResult:
    """Cookie 获取结果"""
    success: bool
    cookie: str = ""
    error: str = ""


class CookieFetcher:
    """通过 Chrome DevTools Protocol 获取浏览器 Cookie"""

    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self._process = None

    def _check_browser_running(self, browser: str) -> bool:
        """检查浏览器是否已在运行"""
        import subprocess
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {browser}.exe"],
                capture_output=True, text=True, encoding="gbk"
            )
            return browser.lower() + ".exe" in result.stdout.lower()
        except Exception:
            return False

    def _find_browser(self, browser: str) -> Optional[str]:
        """查找浏览器可执行文件路径"""
        for path in BROWSER_PATHS.get(browser, []):
            import os
            if os.path.exists(path):
                return path
        return None

    def _start_browser(self, browser_exe: str, url: str):
        """启动浏览器并开启远程调试"""
        import os
        env = os.environ.copy()
        self._process = subprocess.Popen(
            [
                browser_exe,
                f"--remote-debugging-port={self.debug_port}",
                "--remote-allow-origins=*",
                "--no-first-run",
                "--no-default-browser-check",
                url,
            ],
            env=env,
        )
        logger.info(f"已启动浏览器: {browser_exe}")

    def _wait_for_debug_port(self, max_wait: int = 15) -> bool:
        """等待调试端口就绪"""
        for i in range(max_wait):
            try:
                req = urllib.request.Request(
                    f"http://localhost:{self.debug_port}/json/version"
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    return True
            except Exception:
                time.sleep(1)
        return False

    def _get_websocket_url(self, domain: str) -> Optional[str]:
        """获取指定页面的 WebSocket 调试 URL"""
        try:
            req = urllib.request.Request(f"http://localhost:{self.debug_port}/json")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pages = json.loads(resp.read())

            for page in pages:
                if domain in page.get("url", ""):
                    ws_url = page.get("webSocketDebuggerUrl", "")
                    if ws_url:
                        logger.info(f"找到目标页面: {page.get('title', 'unknown')}")
                        return ws_url

            logger.warning(f"未找到包含 {domain} 的页面")
            for p in pages:
                logger.info(f"  可用页面: {p.get('title', '?')}: {p.get('url', 'blank')[:80]}")
            return None
        except Exception as e:
            logger.error(f"获取页面列表失败: {e}")
            return None

    def _get_all_cookies(self, ws_url: str, domain_filter: str = "") -> Optional[str]:
        """通过 CDP Network.getAllCookies 获取所有 Cookie（包括 HttpOnly）

        Args:
            ws_url: WebSocket 调试 URL
            domain_filter: 域名过滤，只保留包含该域名的 Cookie
        """
        try:
            import websocket
            ws = websocket.create_connection(ws_url, timeout=10)
            cmd = {
                "id": 1,
                "method": "Network.getAllCookies",
            }
            ws.send(json.dumps(cmd))
            ws.settimeout(10)
            result = ws.recv()
            ws.close()

            response = json.loads(result)
            if "result" in response and "cookies" in response["result"]:
                cookies = response["result"]["cookies"]
                # 将 cookie 对象转换为 cookie 字符串，按域名过滤
                parts = []
                for c in cookies:
                    cookie_domain = c.get("domain", "")
                    if domain_filter and domain_filter not in cookie_domain:
                        continue
                    part = f"{c['name']}={c['value']}"
                    parts.append(part)
                return "; ".join(parts)
            logger.error(f"意外的响应: {response}")
            return None
        except ImportError:
            logger.error("websocket-client 库未安装，请运行: pip install websocket-client")
            return None
        except Exception as e:
            logger.error(f"CDP Network.getAllCookies 失败: {e}")
            return None

    def _execute_js(self, ws_url: str, expression: str) -> Optional[str]:
        """通过 WebSocket 执行 JavaScript"""
        try:
            import websocket
            ws = websocket.create_connection(ws_url, timeout=10)
            cmd = {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expression,
                    "returnByValue": True,
                },
            }
            ws.send(json.dumps(cmd))
            ws.settimeout(10)
            result = ws.recv()
            ws.close()

            response = json.loads(result)
            if "result" in response and "result" in response["result"]:
                return response["result"]["result"].get("value", "")
            logger.error(f"意外的响应: {response}")
            return None
        except ImportError:
            logger.error("websocket-client 库未安装，请运行: pip install websocket-client")
            return None
        except Exception as e:
            logger.error(f"WebSocket 执行失败: {e}")
            return None

    def fetch(self, platform: str, browser: str = "edge") -> CookieResult:
        """
        获取指定平台的 Cookie

        Args:
            platform: 平台名称 (douyin | twitter)
            browser: 浏览器类型 (edge | chrome)

        Returns:
            CookieResult: 包含成功状态、Cookie 字符串或错误信息
        """
        # 确定目标域名和浏览器路径
        domains = {
            "douyin": "https://www.douyin.com",
            "twitter": "https://x.com",
        }
        domain = domains.get(platform)
        if not domain:
            return CookieResult(success=False, error=f"不支持的平台: {platform}")

        browser_exe = self._find_browser(browser)
        if not browser_exe:
            return CookieResult(
                success=False,
                error=f"未找到 {browser} 浏览器，请确认安装路径",
            )

        # 检查浏览器是否已在运行
        browser_name = "msedge" if browser == "edge" else "chrome"
        if self._check_browser_running(browser_name):
            return CookieResult(
                success=False,
                error=f"检测到 {browser} 浏览器正在运行，请先关闭所有浏览器窗口后重试",
            )

        try:
            # 启动浏览器
            logger.info(f"正在启动 {browser} 浏览器...")
            self._start_browser(browser_exe, domain)

            # 等待调试端口
            logger.info("等待浏览器启动...")
            if not self._wait_for_debug_port():
                return CookieResult(success=False, error="浏览器启动超时，请重试")

            time.sleep(3)  # 等待页面加载

            # 获取 WebSocket URL
            ws_url = self._get_websocket_url(domain)
            if not ws_url:
                return CookieResult(
                    success=False,
                    error="未找到目标页面，请确保浏览器已打开对应网站",
                )

            # 优先使用 Network.getAllCookies（可获取 HttpOnly Cookie）
            logger.info("正在获取 Cookie...")
            cookie = self._get_all_cookies(ws_url)
            # 如果 Network.getAllCookies 失败，回退到 document.cookie
            if not cookie:
                logger.warning("Network.getAllCookies 失败，回退到 document.cookie")
                cookie = self._execute_js(ws_url, "document.cookie")
            if cookie:
                logger.info(f"Cookie 获取成功，长度: {len(cookie)}")
                return CookieResult(success=True, cookie=cookie)
            else:
                return CookieResult(
                    success=False,
                    error="Cookie 获取失败，请确保浏览器中已登录该账号",
                )

        except Exception as e:
            logger.error(f"Cookie 获取过程出错: {e}")
            return CookieResult(success=False, error=str(e))
