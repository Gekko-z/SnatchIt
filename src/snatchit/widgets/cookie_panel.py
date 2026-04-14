"""Cookie 管理面板 - 基于 yaml 配置文件"""

from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from snatchit.config import PLATFORM_CONFIG
from snatchit.config_manager import read_cookie, ensure_config_exists, save_cookie_to_yaml


class CookiePanel(QGroupBox):
    """Cookie 管理面板"""

    def __init__(self, config, parent=None):
        super().__init__("Cookie 管理", parent)
        self.config = config
        self.current_platform = config.get("platform")
        self.cookie_edits = {}       # {platform: QLineEdit}
        self.path_labels = {}        # {platform: QLabel} 显示 yaml 路径
        self.row_widgets = {}        # {platform: QVBoxLayout} 每行的容器
        self._setup_ui()
        self._load_cookies_from_yaml()
        # 初始化时只显示当前平台
        self._update_visibility()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 为每个平台创建 Cookie 输入行
        for key, info in PLATFORM_CONFIG.items():
            # 使用 QWidget 容器以便控制 setVisible
            row_widget = QWidget()
            row = QVBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            self.row_widgets[key] = row_widget

            # 第一行：平台标签 + yaml 路径
            info_layout = QHBoxLayout()
            label = QLabel(f"{info['label']}:")
            path_label = QLabel("")
            path_label.setStyleSheet("color: gray; font-size: 11px;")
            path_label.setTextInteractionFlags(
                path_label.textInteractionFlags() |
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self.path_labels[key] = path_label
            info_layout.addWidget(label)
            info_layout.addStretch()
            info_layout.addWidget(path_label, 1)
            row.addLayout(info_layout)

            # 第二行：Cookie 输入 + 按钮
            input_layout = QHBoxLayout()
            edit = QLineEdit()
            edit.setPlaceholderText(f"粘贴 {info['label']} Cookie")
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.cookie_edits[key] = edit

            # 显示/隐藏按钮
            toggle_btn = QPushButton("显示")
            toggle_btn.setMaximumWidth(60)
            toggle_btn.clicked.connect(
                lambda checked, e=edit, b=toggle_btn: self._toggle_visibility(e, b)
            )

            # 保存到 yaml 按钮
            save_btn = QPushButton("保存")
            save_btn.setObjectName("primary")
            save_btn.setMaximumWidth(60)
            save_btn.clicked.connect(lambda checked, k=key: self._save_cookie(k))

            input_layout.addWidget(edit, 1)
            input_layout.addWidget(toggle_btn)
            input_layout.addWidget(save_btn)
            row.addLayout(input_layout)

            layout.addWidget(row_widget)

    def _load_cookies_from_yaml(self):
        """应用启动时从 yaml 配置文件加载 Cookie"""
        for key in PLATFORM_CONFIG:
            yaml_path = ensure_config_exists(key)
            path_label = self.path_labels.get(key)
            if path_label:
                path_label.setText(yaml_path)
            cookie = read_cookie(key)
            edit = self.cookie_edits.get(key)
            if edit and cookie:
                edit.setText(cookie)
                # Twitter 自动从 Cookie 提取 ct0 并保存到 yaml headers
                if key == "twitter":
                    token = self._extract_csrf_from_cookie(cookie)
                    if token:
                        self._save_csrf_token(yaml_path, token)

    def _save_csrf_token(self, yaml_path: str, token: str):
        """保存 X-Csrf-Token 到 yaml 配置的 headers 中"""
        import yaml
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            if "twitter" not in config:
                config["twitter"] = {}
            if "headers" not in config["twitter"]:
                config["twitter"]["headers"] = {}
            config["twitter"]["headers"]["X-Csrf-Token"] = token
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            return False

    def _extract_csrf_from_cookie(self, cookie: str) -> str:
        """从 Cookie 字符串中提取 ct0 值（即 X-Csrf-Token）"""
        for part in cookie.split(";"):
            part = part.strip()
            if part.lower().startswith("ct0="):
                return part.split("=", 1)[1].strip()
        return ""

    def _toggle_visibility(self, edit: QLineEdit, btn: QPushButton):
        """切换 Cookie 显示/隐藏"""
        if edit.echoMode() == QLineEdit.EchoMode.Password:
            edit.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.setText("隐藏")
        else:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            btn.setText("显示")

    def _save_cookie(self, platform: str):
        """手动将输入框的 Cookie 保存到 yaml"""
        edit = self.cookie_edits.get(platform)
        if not edit:
            return
        cookie = edit.text().strip()
        if not cookie:
            QMessageBox.warning(self, "提示", "请先粘贴 Cookie")
            return

        success, msg = save_cookie_to_yaml(platform, cookie)
        if success:
            # Twitter 自动从 Cookie 提取 ct0，同时保存到 yaml headers
            if platform == "twitter":
                token = self._extract_csrf_from_cookie(cookie)
                if token:
                    yaml_path = ensure_config_exists(platform)
                    self._save_csrf_token(yaml_path, token)
            QMessageBox.information(self, "成功", "Cookie 已保存到配置文件!")
        else:
            QMessageBox.warning(self, "失败", msg)

    def get_cookie(self, platform: str) -> str:
        """获取指定平台的 Cookie（直接从 yaml 文件读取）"""
        return read_cookie(platform).strip()

    def set_cookie(self, platform: str, cookie: str):
        """设置指定平台的 Cookie（显示用）"""
        edit = self.cookie_edits.get(platform)
        if edit and cookie:
            edit.setText(cookie)

    def _update_visibility(self):
        """只显示当前平台的行"""
        for key, widget in self.row_widgets.items():
            widget.setVisible(key == self.current_platform)

    def set_current_platform(self, platform: str):
        """设置当前显示的平台"""
        self.current_platform = platform
        self._update_visibility()
