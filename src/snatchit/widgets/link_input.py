"""链接输入组件"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QProgressBar,
)
from PyQt6.QtCore import pyqtSignal

from snatchit.config import AppConfig, PLATFORM_CONFIG


class LinkInputWidget(QWidget):
    """平台选择 + 链接输入 + 路径选择组件"""

    platform_changed = pyqtSignal(str)  # 平台切换信号

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 平台选择
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("平台:"))
        self.platform_combo = QComboBox()
        for key, info in PLATFORM_CONFIG.items():
            self.platform_combo.addItem(info["label"], key)
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        platform_layout.addWidget(self.platform_combo, 1)
        layout.addLayout(platform_layout)

        # 视频链接
        link_layout = QHBoxLayout()
        link_layout.addWidget(QLabel("链接:"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("请输入视频链接")
        link_layout.addWidget(self.url_edit, 1)
        layout.addLayout(link_layout)

        # 保存路径
        self.path_label = QLabel("下载目录:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择保存路径")
        self.path_btn = QPushButton("浏览...")
        self.path_btn.setMaximumWidth(80)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # 状态标签
        self.status_label = QLabel("就绪")

        # 下载/取消按钮（由父窗口添加到布局中）
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setObjectName("primary")
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)

    def get_platform(self) -> str:
        """获取当前选择的平台 key"""
        idx = self.platform_combo.currentIndex()
        return list(PLATFORM_CONFIG.keys())[idx]

    def set_platform(self, platform: str):
        """设置当前平台"""
        platforms = list(PLATFORM_CONFIG.keys())
        if platform in platforms:
            self.platform_combo.setCurrentIndex(platforms.index(platform))

    def _on_platform_changed(self):
        platform = self.get_platform()
        info = PLATFORM_CONFIG[platform]
        self.url_edit.setPlaceholderText(info["url_placeholder"])
        self.platform_changed.emit(platform)
