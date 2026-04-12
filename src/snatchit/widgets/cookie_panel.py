"""Cookie 管理面板"""

from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal

from snatchit.config import PLATFORM_CONFIG


class CookieFetchWorker(QThread):
    """Cookie 获取工作线程"""

    finished = pyqtSignal(bool, str)  # success, cookie_or_error

    def __init__(self, platform: str, parent=None):
        super().__init__(parent)
        self.platform = platform

    def run(self):
        from snatchit.cookie_fetcher import CookieFetcher

        fetcher = CookieFetcher()
        result = fetcher.fetch(self.platform)
        if result.success:
            self.finished.emit(True, result.cookie)
        else:
            self.finished.emit(False, result.error)


class CookiePanel(QGroupBox):
    """Cookie 管理面板"""

    def __init__(self, config, parent=None):
        super().__init__("Cookie 管理", parent)
        self.config = config
        self.current_platform = config.get("platform")
        self.cookie_edits = {}  # {platform: QLineEdit}
        self.fetch_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 为每个平台创建 Cookie 输入行
        for key, info in PLATFORM_CONFIG.items():
            row = QHBoxLayout()
            label = QLabel(f"{info['label']}:")
            edit = QLineEdit()
            edit.setPlaceholderText(f"粘贴 {info['label']} Cookie 或点击自动获取")
            edit.setEchoMode(QLineEdit.EchoMode.Password)  # 隐藏 Cookie 内容
            self.cookie_edits[key] = edit

            # 显示/隐藏按钮
            toggle_btn = QPushButton("显示")
            toggle_btn.setMaximumWidth(60)
            toggle_btn.clicked.connect(lambda checked, e=edit: self._toggle_visibility(e, toggle_btn))

            # 自动获取按钮
            fetch_btn = QPushButton("从浏览器获取")
            fetch_btn.setObjectName("primary")
            fetch_btn.setMaximumWidth(120)
            fetch_btn.clicked.connect(lambda checked, k=key: self._fetch_cookie(k))

            row.addWidget(label)
            row.addWidget(edit, 1)
            row.addWidget(toggle_btn)
            row.addWidget(fetch_btn)
            layout.addLayout(row)

    def _toggle_visibility(self, edit: QLineEdit, btn: QPushButton):
        """切换 Cookie 显示/隐藏"""
        if edit.echoMode() == QLineEdit.EchoMode.Password:
            edit.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.setText("隐藏")
        else:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            btn.setText("显示")

    def _fetch_cookie(self, platform: str):
        """从浏览器自动获取 Cookie（后台线程）"""
        QMessageBox.information(
            self,
            "提示",
            f"即将启动浏览器获取 {PLATFORM_CONFIG[platform]['label']} 的 Cookie。\n\n"
            f"请确保：\n"
            f"1. 浏览器中已登录该账号\n"
            f"2. 所有 Edge/Chrome 浏览器窗口已关闭\n\n"
            f"点击确定后将自动启动浏览器。",
        )

        self.fetch_worker = CookieFetchWorker(platform)
        self.fetch_worker.finished.connect(self._on_cookie_fetched)
        self.fetch_worker.start()

    def _on_cookie_fetched(self, success: bool, message: str):
        """Cookie 获取完成回调"""
        if success:
            # message 是 cookie 字符串
            edit = self.cookie_edits.get(self.fetch_worker.platform)
            if edit:
                edit.setText(message)
                edit.setEchoMode(QLineEdit.EchoMode.Normal)
            QMessageBox.information(self, "成功", "Cookie 获取成功!")
        else:
            QMessageBox.warning(self, "失败", message)

    def get_cookie(self, platform: str) -> str:
        """获取指定平台的 Cookie"""
        edit = self.cookie_edits.get(platform)
        if edit:
            return edit.text().strip()
        return ""

    def set_cookie(self, platform: str, cookie: str):
        """设置指定平台的 Cookie"""
        edit = self.cookie_edits.get(platform)
        if edit and cookie:
            edit.setText(cookie)

    def set_current_platform(self, platform: str):
        """设置当前显示的平台（高亮对应行）"""
        self.current_platform = platform
