"""日志面板"""

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QComboBox
from PyQt6.QtGui import QClipboard
from PyQt6.QtCore import QCoreApplication
import logging


class LogPanel(QGroupBox):
    """日志显示面板"""

    # 日志级别
    LEVEL_INFO = "INFO"
    LEVEL_DEBUG = "DEBUG"

    def __init__(self, parent=None):
        super().__init__("下载日志", parent)
        self.log_level = self.LEVEL_INFO
        self._all_logs = []  # 保存全部日志用于复制
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # 控制栏：日志级别 + 复制 + 清空
        btn_layout = QHBoxLayout()

        # 日志级别下拉框
        level_label = QPushButton("日志级别:")
        level_label.setStyleSheet("background: transparent; border: none; color: #e0e0e0; font-weight: normal;")
        level_label.setEnabled(False)
        self.level_combo = QComboBox()
        self.level_combo.addItem("INFO")
        self.level_combo.addItem("DEBUG")
        self.level_combo.setMaximumWidth(100)
        self.level_combo.currentTextChanged.connect(self._on_level_changed)

        # 复制按钮
        copy_btn = QPushButton("复制日志")
        copy_btn.setMaximumWidth(100)
        copy_btn.clicked.connect(self._copy_logs)

        # 清空按钮
        clear_btn = QPushButton("清空日志")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self.clear_log)

        btn_layout.addWidget(level_label)
        btn_layout.addWidget(self.level_combo)
        btn_layout.addStretch()
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

    def _on_level_changed(self, level: str):
        self.log_level = level
        # 同步修改底层 root logger 的级别
        root_logger = logging.getLogger()
        if level == self.LEVEL_DEBUG:
            root_logger.setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(logging.INFO)
        self._refresh_display()

    def _should_show(self, text: str) -> bool:
        """判断日志是否应该显示"""
        if self.log_level == self.LEVEL_DEBUG:
            return True
        # INFO 级别：不显示 DEBUG 行
        return not text.startswith("[DEBUG]")

    def _refresh_display(self):
        """刷新显示内容"""
        self.log_text.clear()
        for text in self._all_logs:
            if self._should_show(text):
                self.log_text.append(text)
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def append_log(self, text: str):
        """追加日志"""
        self._all_logs.append(text)
        if self._should_show(text):
            self.log_text.append(text)
            # 自动滚动到底部
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)

    def _copy_logs(self):
        """复制全部日志到剪贴板"""
        clipboard = QCoreApplication.instance().clipboard()
        clipboard.setText("\n".join(self._all_logs))

    def clear_log(self):
        """清空日志"""
        self._all_logs.clear()
        self.log_text.clear()
