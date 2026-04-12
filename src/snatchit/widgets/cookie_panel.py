"""Cookie 管理面板 - 基于 yaml 配置文件"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from snatchit.config import PLATFORM_CONFIG
from snatchit.config_manager import read_cookie, ensure_config_exists, save_cookie_to_yaml, save_csrf_to_f2_conf


class CookiePanel(QGroupBox):
    """Cookie 管理面板"""

    def __init__(self, config, parent=None):
        super().__init__("Cookie 管理", parent)
        self.config = config
        self.current_platform = config.get("platform")
        self.cookie_edits = {}       # {platform: QLineEdit}
        self.csrf_edits = {}         # {platform: QLineEdit} 仅 Twitter 需要
        self.path_labels = {}        # {platform: QLabel} 显示 yaml 路径
        self._setup_ui()
        self._load_cookies_from_yaml()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 为每个平台创建 Cookie 输入行
        for key, info in PLATFORM_CONFIG.items():
            row = QVBoxLayout()
            row.setSpacing(4)

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

            # 手动指定 yaml 文件
            yaml_btn = QPushButton("指定配置文件")
            yaml_btn.setMaximumWidth(100)
            yaml_btn.clicked.connect(lambda checked, k=key: self._browse_yaml(k))

            input_layout.addWidget(edit, 1)
            input_layout.addWidget(toggle_btn)
            input_layout.addWidget(save_btn)
            input_layout.addWidget(yaml_btn)
            row.addLayout(input_layout)

            # Twitter 额外需要 X-Csrf-Token
            if key == "twitter":
                csrf_layout = QHBoxLayout()
                csrf_label = QLabel("X-Csrf-Token:")
                csrf_edit = QLineEdit()
                csrf_edit.setPlaceholderText("从浏览器开发者工具获取 (ct0 值)")
                csrf_edit.setEchoMode(QLineEdit.EchoMode.Password)
                self.csrf_edits[key] = csrf_edit

                csrf_toggle = QPushButton("显示")
                csrf_toggle.setMaximumWidth(60)
                csrf_toggle.clicked.connect(
                    lambda checked, e=csrf_edit, b=csrf_toggle: self._toggle_visibility(e, b)
                )

                csrf_save = QPushButton("保存")
                csrf_save.setMaximumWidth(60)
                csrf_save.clicked.connect(lambda checked: self._save_csrf("twitter"))

                csrf_layout.addWidget(csrf_label)
                csrf_layout.addWidget(csrf_edit, 1)
                csrf_layout.addWidget(csrf_toggle)
                csrf_layout.addWidget(csrf_save)
                row.addLayout(csrf_layout)

            layout.addLayout(row)

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
                self._auto_set_csrf_from_cookie(cookie)

            # 加载 X-Csrf-Token（如果 Cookie 中没有 ct0，再从 headers 读取）
            if key == "twitter":
                csrf_edit = self.csrf_edits.get(key)
                if csrf_edit and not csrf_edit.text():
                    csrf = self._read_csrf_token(yaml_path)
                    if csrf:
                        csrf_edit.setText(csrf)

    def _read_csrf_token(self, yaml_path: str) -> str:
        """从 yaml 配置中读取 x-csrf-token"""
        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            twitter_config = config.get("twitter", {})
            # 优先从 headers 中读取
            headers = twitter_config.get("headers", {})
            token = headers.get("X-Csrf-Token", "")
            if not token:
                # 尝试从 x-csrf-token 读取
                token = twitter_config.get("x-csrf-token", "")
            return token
        except Exception:
            return ""

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

    def _auto_set_csrf_from_cookie(self, cookie: str):
        """自动从 Cookie 字符串提取 ct0 并填入 X-Csrf-Token 输入框"""
        csrf_edit = self.csrf_edits.get("twitter")
        if not csrf_edit:
            return
        token = self._extract_csrf_from_cookie(cookie)
        if token:
            csrf_edit.setText(token)

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
            # Twitter 自动从 Cookie 提取 ct0，同时保存到自定义配置和 f2 conf.yaml
            if platform == "twitter":
                token = self._extract_csrf_from_cookie(cookie)
                if token:
                    yaml_path = ensure_config_exists(platform)
                    self._save_csrf_token(yaml_path, token)
                    save_csrf_to_f2_conf(token)
                    csrf_edit = self.csrf_edits.get(platform)
                    if csrf_edit:
                        csrf_edit.setText(token)
            QMessageBox.information(self, "成功", "Cookie 已保存到配置文件!")
        else:
            QMessageBox.warning(self, "失败", msg)

    def _save_csrf(self, platform: str):
        """保存 X-Csrf-Token"""
        csrf_edit = self.csrf_edits.get(platform)
        yaml_path = ensure_config_exists(platform)
        if not csrf_edit or not yaml_path:
            return
        token = csrf_edit.text().strip()
        yaml_ok = self._save_csrf_token(yaml_path, token)
        f2_ok = save_csrf_to_f2_conf(token)
        if yaml_ok and f2_ok:
            QMessageBox.information(self, "成功", "X-Csrf-Token 已保存!")
        else:
            QMessageBox.warning(self, "失败", "保存 X-Csrf-Token 失败")

    def _browse_yaml(self, platform: str):
        """手动指定 yaml 配置文件"""
        current = self.path_labels.get(platform, None)
        start_dir = str(Path(current.text()).parent) if current and current.text() else str(Path.home())
        yaml_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择 {PLATFORM_CONFIG[platform]['label']} 配置文件",
            start_dir,
            "YAML 文件 (*.yaml *.yml)",
        )
        if yaml_path:
            path_label = self.path_labels.get(platform)
            if path_label:
                path_label.setText(yaml_path)
            try:
                import yaml
                with open(yaml_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                cookie = config.get(platform, {}).get("cookie", "")
            except Exception as e:
                cookie = ""
                QMessageBox.warning(self, "读取失败", f"无法读取配置文件: {e}")

            edit = self.cookie_edits.get(platform)
            if edit and cookie:
                edit.setText(cookie)
                self._auto_set_csrf_from_cookie(cookie)

            # 加载 X-Csrf-Token
            if platform == "twitter":
                csrf_edit = self.csrf_edits.get(platform)
                if csrf_edit and not csrf_edit.text():
                    csrf = self._read_csrf_token(yaml_path)
                    if csrf:
                        csrf_edit.setText(csrf)

    def get_cookie(self, platform: str) -> str:
        """获取指定平台的 Cookie（直接从 yaml 文件读取）"""
        return read_cookie(platform).strip()

    def set_cookie(self, platform: str, cookie: str):
        """设置指定平台的 Cookie（显示用）"""
        edit = self.cookie_edits.get(platform)
        if edit and cookie:
            edit.setText(cookie)

    def set_current_platform(self, platform: str):
        """设置当前显示的平台（高亮对应行）"""
        self.current_platform = platform
