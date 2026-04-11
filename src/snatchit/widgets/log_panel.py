"""日志面板"""

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout


class LogPanel(QGroupBox):
    """日志显示面板"""

    def __init__(self, parent=None):
        super().__init__("下载日志", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # 清空按钮
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.clear_log)
        clear_btn.setMaximumWidth(100)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

    def append_log(self, text: str):
        """追加日志"""
        self.log_text.append(text)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
