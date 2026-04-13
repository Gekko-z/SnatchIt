# f2 本地修改记录

> 本文件记录对 f2 仓库的本地修改，以便日后重新安装后恢复。

## 仓库信息

- **远程仓库**: `https://github.com/Gekko-z/f2`
- **分支**: `fix/twitter-api-adaptation`
- **版本号**: `0.0.1.7+gekko.1`（PEP 440 合规）

## 修改内容

### 1. `f2/__init__.py`
- **修改**: `__version__` 改为 `"0.0.1.7+gekko.1"`（PEP 440 本地版本标识符格式）
- **原因**: SnatchIt 打包时需要验证是否为修复后的 fork 版本

### 2. `f2/apps/twitter/filter.py`
- **问题**: Twitter API 响应结构变化，`instructions[0]` 不再是目标数据
- **修复**: 将所有 jsonpath 中的 `instructions[0]` 替换为 `instructions[1]`
- **原因**: Twitter API 现在在索引 0 位置返回 `TimelineClearCache`

### 3. `f2/apps/twitter/utils.py`
- **修复 1**: `extract_desc()` 添加 `full_text` 为 None 时的保护，避免崩溃
- **修复 2**: `tweet_video_url` 按 `content_type` 过滤 MP4 变体，不再返回 M3U8 HLS 播放列表 URL，并选择最高码率的 MP4 文件

### 4. `f2/apps/douyin/db.py`
- **问题**: `video_info` 表缺少 `caption` 和 `caption_raw` 字段
- **修复**: 在 CREATE TABLE 中添加 `"caption TEXT"` 和 `"caption_raw TEXT"` 字段
- **注意**: 旧数据库文件不含这些字段，需要删除旧 `.db` 文件后重新创建

## 如何恢复

```bash
# 克隆 fork 仓库
git clone https://github.com/Gekko-z/f2.git
cd f2
git checkout fix/twitter-api-adaptation

# 安装
pip install .
```

## SnatchIt 集成

SnatchIt 通过 `pyproject.toml` 依赖 f2 fork：
```toml
"f2 @ git+https://github.com/Gekko-z/f2@fix/twitter-api-adaptation"
```

打包时 PyInstaller 自动从 site-packages 中收集 f2 及其依赖，打包为独立产物。
