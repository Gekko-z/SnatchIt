# f2 本地修改记录

> 本文件记录对 f2 仓库的本地修改，以便日后重新安装后恢复。

## 仓库信息

- **本地路径**: `D:\workspace\projects\f2-repo`
- **远程仓库**: `https://github.com/Gekko-z/f2`
- **分支**: `fix/twitter-api-adaptation`
- **最新 commit**: `7404138 fix(twitter): 适配 Twitter API 响应结构变化，修复视频下载问题`

## 修改内容

修改涉及 2 个文件：

### 1. `f2/apps/twitter/filter.py`

- **问题**: Twitter API 响应结构变化，`instructions[0]` 不再是目标数据
- **修复**: 将所有 jsonpath 中的 `instructions[0]` 替换为 `instructions[1]`
- **原因**: Twitter API 现在在索引 0 位置返回 `TimelineClearCache`

### 2. `f2/apps/twitter/utils.py`

- **修复 1**: `extract_desc()` 添加 `full_text` 为 None 时的保护，避免崩溃
- **修复 2**: `tweet_video_url` 按 `content_type` 过滤 MP4 变体，不再返回 M3U8 HLS 播放列表 URL，并选择最高码率的 MP4 文件

## 如何恢复

如果需要在其他机器或重新安装后恢复这些修改：

```bash
# 克隆 fork 仓库
git clone https://github.com/Gekko-z/f2.git
cd f2
git checkout fix/twitter-api-adaptation

# 或者直接从本地复制
cp -r D:\workspace\projects\f2-repo\f2 <目标路径>/f2
```

## SnatchIt 打包

SnatchIt 打包时会自动将 f2 从 `D:\workspace\projects\f2-repo\f2` 复制到 `lib/f2`，然后使用本地副本进行 Nuitka 编译，避免命名空间冲突。
