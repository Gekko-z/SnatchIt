"""主窗口"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from snatchit.config import AppConfig
from snatchit.widgets.link_input import LinkInputWidget
from snatchit.widgets.cookie_panel import CookiePanel
from snatchit.widgets.log_panel import LogPanel


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        self.worker = None  # 当前下载工作线程
        self._setup_ui()
        self._load_config()
        self._connect_signals()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("SnatchIt - 跨平台视频下载")
        self.setMinimumSize(600, 550)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 顶部控制区
        top_layout = QVBoxLayout()
        top_layout.setSpacing(10)

        # 平台选择 + 链接输入
        self.link_input = LinkInputWidget(self.config)
        top_layout.addWidget(self.link_input)

        # 保存路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.link_input.path_label)
        path_layout.addWidget(self.link_input.path_edit, 1)
        path_layout.addWidget(self.link_input.path_btn)
        top_layout.addLayout(path_layout)

        layout.addLayout(top_layout)

        # Cookie 管理面板
        self.cookie_panel = CookiePanel(self.config)
        layout.addWidget(self.cookie_panel)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.download_btn = self.link_input.download_btn  # 复用 link_input 的按钮
        self.cancel_btn = self.link_input.cancel_btn
        btn_layout.addWidget(self.download_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # 进度条
        layout.addWidget(self.link_input.progress_bar)
        layout.addWidget(self.link_input.status_label)

        # 日志面板
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel, 1)  # 日志占据剩余空间

        # 设置按钮初始状态
        self._set_buttons_enabled(True)

    def _load_config(self):
        """加载保存的配置"""
        # 加载平台选择
        saved_platform = self.config.get("platform")
        self.link_input.set_platform(saved_platform)

        # 加载保存路径
        saved_path = self.config.get("save_path")
        self.link_input.path_edit.setText(saved_path)

        # 加载 Cookie
        for platform in self.config.get_platforms():
            cookie = self.config.get_cookie(platform)
            if cookie:
                self.cookie_panel.set_cookie(platform, cookie)

    def _connect_signals(self):
        """连接信号槽"""
        # 路径浏览按钮
        self.link_input.path_btn.clicked.connect(self._browse_path)

        # 下载按钮
        self.download_btn.clicked.connect(self._start_download)

        # 取消按钮
        self.cancel_btn.clicked.connect(self._cancel_download)

        # 平台切换时更新 Cookie
        self.link_input.platform_changed.connect(self._on_platform_changed)

    def _browse_path(self):
        """浏览选择保存路径"""
        current = self.link_input.path_edit.text()
        path = QFileDialog.getExistingDirectory(self, "选择保存路径", current)
        if path:
            self.link_input.path_edit.setText(path)
            self.config.set("save_path", path)

    def _start_download(self):
        """开始下载"""
        from snatchit.downloader import DownloadWorker

        # 验证输入
        url = self.link_input.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入视频链接")
            return

        platform = self.link_input.get_platform()
        cookie = self.cookie_panel.get_cookie(platform)
        if not cookie:
            QMessageBox.warning(self, "提示", "请先获取或输入 Cookie")
            return

        save_path = self.link_input.path_edit.text().strip()
        if not save_path:
            QMessageBox.warning(self, "提示", "请选择保存路径")
            return

        # 确保路径存在
        Path(save_path).mkdir(parents=True, exist_ok=True)

        # 保存配置
        self.config.set("platform", platform)
        self.config.set("save_path", save_path)
        self.config.set_cookie(platform, cookie)

        # 禁用按钮
        self._set_buttons_enabled(False)
        self.log_panel.clear_log()

        # 创建并启动下载线程
        self.worker = DownloadWorker(
            platform=platform,
            url=url,
            cookie=cookie,
            save_path=save_path,
        )
        self.worker.log.connect(self.log_panel.append_log)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._download_finished)
        self.worker.start()

    def _cancel_download(self):
        """取消下载"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.log_panel.append_log("[用户] 已取消下载")
            self._set_buttons_enabled(True)
            self.link_input.progress_bar.setValue(0)
            self.link_input.status_label.setText("已取消")

    def _update_progress(self, percent: int, text: str):
        """更新进度"""
        self.link_input.progress_bar.setValue(percent)
        self.link_input.status_label.setText(text)

    def _download_finished(self, success: bool, message: str):
        """下载完成回调"""
        self._set_buttons_enabled(True)
        if success:
            self.link_input.status_label.setText("下载完成")
            self.log_panel.append_log("[完成] 下载完成!")
        else:
            self.link_input.status_label.setText("下载失败")
            self.log_panel.append_log(f"[错误] {message}")
            QMessageBox.critical(self, "下载失败", message)

    def _set_buttons_enabled(self, enabled: bool):
        """设置按钮可用状态"""
        self.download_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(not enabled)
        self.link_input.url_edit.setEnabled(enabled)
        self.link_input.platform_combo.setEnabled(enabled)
        self.cookie_panel.setEnabled(enabled)

    def _on_platform_changed(self, platform: str):
        """平台切换时更新 Cookie 显示"""
        self.cookie_panel.set_current_platform(platform)
        self.config.set("platform", platform)

    def closeEvent(self, event):
        """关闭窗口时保存状态"""
        self.config.save_window_geometry(self.saveGeometry())
        self.config.set("platform", self.link_input.get_platform())
        self.config.set("save_path", self.link_input.path_edit.text())

        # 保存所有平台的 Cookie
        for platform in self.config.get_platforms():
            cookie = self.cookie_panel.cookie_edits.get(platform)
            if cookie:
                self.config.set_cookie(platform, cookie.text())

        # 终止正在进行的下载
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        event.accept()
