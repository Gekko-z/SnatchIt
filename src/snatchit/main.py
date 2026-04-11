"""SnatchIt - 跨平台视频下载客户端"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from snatchit.widgets.main_window import MainWindow


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def load_stylesheet(app: QApplication):
    """加载 QSS 样式表"""
    style_path = Path(__file__).parent / "resources" / "style.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    """应用入口"""
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("SnatchIt")
    app.setStyle("Fusion")  # 使用 Fusion 风格，跨平台一致

    # 加载样式表
    load_stylesheet(app)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
