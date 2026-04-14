"""SnatchIt - 跨平台视频下载客户端"""

import sys
import logging
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import QIcon

from snatchit.widgets.main_window import MainWindow


# 环境检查常量
REQUIRED_PYTHON_VERSION = (3, 11)
F2_REPO_URL = "git+https://github.com/Gekko-z/f2@main"
F2_REQUIRED_VERSION_PREFIX = "0.0.1.7+gekko"  # 自定义版本号前缀，用于验证是否为修复版


def check_environment():
    """检查 Python 版本和 f2 依赖，必要时自动安装 f2"""
    # 1. 检查 Python 版本
    if sys.version_info[:2] != REQUIRED_PYTHON_VERSION:
        current = f"{sys.version_info.major}.{sys.version_info.minor}"
        required = f"{REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}"
        print(f"[环境检查] 警告: 当前 Python {current}，推荐 {required}")
        print(f"[环境检查] 请使用 Python {required} 运行此应用")
        print(f"[环境检查] 下载地址: https://www.python.org/downloads/")
        # 不阻止运行，仅警告

    # 2. 检查 f2 是否已安装且版本正确
    try:
        import f2
        f2_version = getattr(f2, "__version__", "")
        if f2_version.startswith(F2_REQUIRED_VERSION_PREFIX):
            print(f"[环境检查] f2 版本验证通过 ({f2_version})")
        else:
            print(f"[环境检查] 警告: f2 版本不匹配 (当前: {f2_version}, 需要: {F2_REQUIRED_VERSION_PREFIX}*)，正在自动更新...")
            _install_f2()
    except ImportError:
        print(f"[环境检查] f2 未安装，正在自动安装...")
        _install_f2()


def _install_f2():
    """自动安装/更新 f2 fork"""
    try:
        print(f"[环境检查] 正在安装 f2 从 {F2_REPO_URL} ...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", F2_REPO_URL, "-q"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print(f"[环境检查] f2 安装成功")
        else:
            print(f"[环境检查] 错误: f2 安装失败")
            print(f"[环境检查] stdout: {result.stdout}")
            print(f"[环境检查] stderr: {result.stderr}")
            print(f"[环境检查] 请手动执行: pip install {F2_REPO_URL}")
    except subprocess.TimeoutExpired:
        print(f"[环境检查] 错误: f2 安装超时")
    except Exception as e:
        print(f"[环境检查] 错误: f2 安装失败: {e}")


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def load_stylesheet(app: QApplication):
    """加载 QSS 样式表"""
    from snatchit.utils import get_bundle_dir
    bundle_dir = get_bundle_dir()
    # 尝试打包后路径（PyInstaller/Nuitka）
    style_path = bundle_dir / "snatchit" / "resources" / "style.qss"
    if not style_path.exists():
        # 开发模式
        style_path = bundle_dir / "src" / "snatchit" / "resources" / "style.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


APP_NAME = "SnatchIt"
LOCAL_SOCKET_NAME = "snatchit-single-instance-lock"


def send_activate_message():
    """通知已有实例激活窗口"""
    socket = QLocalSocket()
    socket.connectToServer(LOCAL_SOCKET_NAME)
    if socket.waitForConnected(500):
        socket.write(b"activate")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        # 等待断开后再退出，避免消息未发送完
        import time
        time.sleep(0.1)
        return True
    return False


def main():
    """应用入口"""
    # 单实例检查：已有实例则发送激活消息后退出
    if send_activate_message():
        print("[单实例] 已有实例运行中，已发送激活信号")
        sys.exit(0)

    # 仅在非打包模式下进行环境检查（打包后 f2 已内置）
    if not getattr(sys, "frozen", False) and not getattr(sys, "_MEIPASS", None):
        check_environment()

    setup_logging()

    app = QApplication(sys.argv)

    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")  # 使用 Fusion 风格，跨平台一致

    # 加载样式表
    load_stylesheet(app)

    # 设置应用图标
    from snatchit.utils import get_bundle_dir
    bundle_dir = get_bundle_dir()
    icon_path = bundle_dir / "snatchit" / "resources" / "snatchit.ico"
    if not icon_path.exists():
        icon_path = bundle_dir / "src" / "snatchit" / "resources" / "snatchit.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 创建单实例锁服务器，接收新实例的激活信号
    app._instance_lock = QLocalServer()
    app._instance_lock.removeServer(LOCAL_SOCKET_NAME)  # 清理可能的残留锁文件
    if app._instance_lock.listen(LOCAL_SOCKET_NAME):
        def _on_new_connection():
            """新实例连接时激活当前窗口"""
            server_socket = app._instance_lock.nextPendingConnection()
            if server_socket:
                def _on_ready_read():
                    data = server_socket.readAll()
                    if b"activate" in bytes(data):
                        print("[单实例] 收到激活信号，激活窗口")
                        window.raise_()
                        window.activateWindow()
                        window.show()
                        # macOS 特殊处理：确保窗口提到前台
                        import sys as _sys
                        if _sys.platform == "darwin":
                            from PyQt6.QtWidgets import QApplication
                            QApplication.alert(window, 0)
                    server_socket.deleteLater()
                server_socket.readyRead.connect(_on_ready_read)

        app._instance_lock.newConnection.connect(_on_new_connection)
    else:
        print(f"[单实例] 警告: 无法创建本地锁 {LOCAL_SOCKET_NAME}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
