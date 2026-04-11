---
name: f2-video-downloader
description: This skill should be used when the user asks to "download douyin video", "download twitter video", "download tiktok video", "download X video", "download weibo video", mentions "f2" library, or needs to download videos from social media platforms using the f2 Python library. Covers both CLI and API usage patterns.
version: 1.1.0
---

# F2 视频下载库使用指南

## 概述

F2 是一个异步多平台视频下载 Python 库，支持 CLI 命令调用与 API 接口调用。

**安装位置**：虚拟环境 `D:\workspace\projects\f2_env`
**Python 路径**：`D:\workspace\projects\f2_env\Scripts\python.exe`
**源码位置**：`D:\workspace\projects\f2-repo`
**包安装位置**：`D:\workspace\projects\f2_env\Lib\site-packages\f2`

**支持平台**：
- 抖音 (dy/douyin)
- TikTok (tk/tiktok)
- Twitter/X (x/twitter)
- 微博 (wb/weibo)

---

## 一、CLI 命令用法

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-c, --config` | 配置文件路径 | `f2/conf/app.yaml` |
| `-u, --url` | 视频/主页链接 | - |
| `-M, --mode` | 下载模式 | - |
| `-p, --path` | 保存路径 | `./Download` |
| `-k, --cookie` | 登录 Cookie | - |
| `-n, --naming` | 文件命名模板 | `{create}_{desc}` |
| `-o, --max-counts` | 最大下载数 | `0`（无限制） |
| `-e, --timeout` | 超时时间(秒) | `10` |
| `-r, --max_retries` | 重试次数 | `5` |
| `-P, --proxies` | 代理服务器 | - |

### 抖音 (dy)

```bash
# 下载单个视频
f2 dy -M one -u "https://v.douyin.com/iRNBho6u/"

# 下载用户主页作品
f2 dy -M post -u "https://www.douyin.com/user/MS4wLjABAAAA..."

# 下载用户喜欢作品
f2 dy -M like -u "https://www.douyin.com/user/MS4wLjABAAAA..."

# 下载合集作品
f2 dy -M mix -u "https://www.douyin.com/collection/..."

# 下载直播流
f2 dy -M live -u "https://live.douyin.com/775841227732"
```

**抖音模式枚举**：`one` | `post` | `like` | `collection` | `collects` | `music` | `mix` | `live`

### Twitter/X (x)

```bash
# 下载单条推文视频
f2 x -M one -u "https://x.com/user/status/1234567890"

# 下载用户主页推文
f2 x -M post -u "https://x.com/user"

# 下载用户喜欢推文
f2 x -M like -u "https://x.com/user"

# 下载书签推文
f2 x -M bookmark -u "https://x.com/i/bookmarks"
```

**Twitter 模式枚举**：`one` | `post` | `like` | `bookmark`

> **注意**：Twitter 还需要 `X-Csrf-Token`，需在配置文件中设置。

### TikTok (tk)

```bash
# 下载单个视频
f2 tk -M one -u "https://www.tiktok.com/@user/video/1234567890"

# 下载用户主页作品
f2 tk -M post -u "https://www.tiktok.com/@user"

# 下载用户收藏作品
f2 tk -M collect -u "https://www.tiktok.com/@user"
```

### 通用 CLI 操作

```bash
# 初始化配置文件
f2 dy --init-config dy.yaml
f2 x --init-config x.yaml

# 更新 Cookie 到配置文件
f2 dy -k "your_cookie_string" -c app.yaml --update-config

# 自动从浏览器获取 Cookie
f2 dy -c app.yaml --auto-cookie edge

# 查看帮助
f2 dy -h
f2 x -h
```

---

## 二、API 接口调用（开发者模式）

### 核心异步模板

所有 API 调用都是异步的，需要使用 `asyncio`：

```python
import asyncio
from f2.apps.douyin.handler import DouyinHandler
from f2.apps.twitter.handler import TwitterHandler
from f2.apps.tiktok.handler import TiktokHandler

async def main():
    handler = DouyinHandler(kwargs={"path": "./Download"})
    # 调用各种方法
    await handler.handle_one_video()

asyncio.run(main())
```

### 抖音 API

#### 1. 提取作品 ID

```python
from f2.apps.douyin.utils import AwemeIdFetcher

# 从单个链接提取
aweme_id = AwemeIdFetcher.get_aweme_id("https://v.douyin.com/iRNBho6u/")

# 从多个链接批量提取
aweme_ids = AwemeIdFetcher.get_all_aweme_id(["url1", "url2"])
```

#### 2. 提取用户 SecUID

```python
from f2.apps.douyin.utils import SecUserIdFetcher

sec_user_id = SecUserIdFetcher.get_sec_user_id("https://www.douyin.com/user/...")
sec_user_ids = SecUserIdFetcher.get_all_sec_user_id(["url1", "url2"])
```

#### 3. 获取用户信息

```python
from f2.apps.douyin.handler import DouyinHandler

handler = DouyinHandler(kwargs={"path": "./Download"})
user_info = await handler.fetch_user_profile(sec_user_id)
```

#### 4. 获取单个作品数据

```python
from f2.apps.douyin.handler import DouyinHandler

handler = DouyinHandler(kwargs={"path": "./Download"})
video_data = await handler.fetch_one_video(aweme_id)
```

#### 5. 获取用户发布作品

```python
async for video_data in handler.fetch_user_post_videos(
    sec_user_id,
    max_cursor=0,
    page_counts=20,
    max_counts=None  # None 表示获取全部
):
    print(video_data)
```

#### 6. 下载单个视频（完整流程）

```python
from f2.apps.douyin.handler import DouyinHandler

async def download_douyin_video(url: str, save_path: str = "./Download"):
    handler = DouyinHandler(kwargs={"path": save_path})
    # 使用 handle_one_video 会自动从 URL 提取 ID 并下载
    # 需要先设置 URL 到 kwargs 中
    handler.kwargs["url"] = url
    handler.kwargs["mode"] = "one"
    await handler.handle_one_video()
```

### Twitter API

#### 1. 提取推文 ID

```python
from f2.apps.twitter.utils import TweetIdFetcher

tweet_id = TweetIdFetcher.get_tweet_id("https://x.com/user/status/1234567890")
tweet_ids = TweetIdFetcher.get_all_tweet_ids(["url1", "url2"])
```

#### 2. 提取用户唯一 ID

```python
from f2.apps.twitter.utils import UniqueIdFetcher

unique_id = UniqueIdFetcher.get_unique_id("https://x.com/user")
```

#### 3. 获取单个推文

```python
from f2.apps.twitter.handler import TwitterHandler

handler = TwitterHandler(kwargs={"path": "./Download"})
tweet_data = await handler.fetch_one_tweet(tweet_id)
```

#### 4. 获取用户推文

```python
async for tweet_data in handler.fetch_post_tweet(
    userId,
    page_counts=20,
    max_cursor="",
    max_counts=None
):
    print(tweet_data)
```

#### 5. 下载单条推文视频

```python
from f2.apps.twitter.handler import TwitterHandler

async def download_twitter_tweet(url: str, save_path: str = "./Download"):
    handler = TwitterHandler(kwargs={"path": save_path})
    handler.kwargs["url"] = url
    handler.kwargs["mode"] = "one"
    await handler.handle_one_tweet()
```

### TikTok API

```python
from f2.apps.tiktok.utils import AwemeIdFetcher, SecUserIdFetcher
from f2.apps.tiktok.handler import TiktokHandler

# 提取作品 ID
aweme_id = AwemeIdFetcher.get_aweme_id("https://www.tiktok.com/@user/video/...")

# 下载
handler = TiktokHandler(kwargs={"path": "./Download"})
handler.kwargs["url"] = url
handler.kwargs["mode"] = "one"
await handler.handle_one_video()
```

---

## 三、配置文件

### 配置文件优先级

```
CLI 参数 > 自定义配置文件 > 应用低频配置文件(app.yaml)
```

### 配置文件位置

- **主配置文件 (app.yaml)**: `D:\workspace\projects\f2_env\Lib\site-packages\f2\conf\app.yaml`
- **F2 配置文件 (conf.yaml)**: `D:\workspace\projects\f2_env\Lib\site-packages\f2\conf\conf.yaml`
- **默认配置文件 (defaults.yaml)**: `D:\workspace\projects\f2_env\Lib\site-packages\f2\conf\defaults.yaml`（勿修改）

### app.yaml 核心配置项

```yaml
douyin:
  cookie: "从浏览器复制的完整 Cookie"
  url: "https://www.douyin.com/user/xxx"
  mode: "post"
  path: "./Download"
  naming: "{create}_{desc}"

twitter:
  cookie: "从浏览器复制的完整 Cookie"
  x-csrf-token: "从浏览器 Network 中获取"
  url: "https://x.com/user"
  mode: "post"
  path: "./Download"
  naming: "{create}_{desc}"
```

### 自定义配置文件示例

```yaml
# dy-single.yaml - 下载单个抖音视频
douyin:
  url: "https://v.douyin.com/iRNBho6u/"
  mode: one

# x-single.yaml - 下载单条推文
twitter:
  url: "https://x.com/user/status/1234567890"
  mode: one
```

调用方式：
```bash
f2 dy -c dy-single.yaml
f2 x -c x-single.yaml
```

### 通过代码指定配置文件

```python
from f2.utils.utils import create_and_merge_config

conf_file = "D:/workspace/projects/f2_env/Lib/site-packages/f2/conf/app.yaml"
conf = create_and_merge_config(conf_file)
```

---

## 四、下载目录结构

```
Download/
├── douyin/
│   └── post/
│       └── user_nickname/
│           ├── 2024-01-01_12-00-00_desc/
│           │   ├── 2024-01-01_12-00-00_desc-video.mp4
│           │   ├── 2024-01-01_12-00-00_desc-desc.txt
│           │   └── 2024-01-01_12-00-00_desc-cover.jpg
│           └── ...
├── twitter/
│   └── post/
│       └── user_nickname/
│           ├── 2024-01-01_12-00-00_desc/
│           │   ├── 2024-01-01_12-00-00_desc-video.mp4
│           │   └── 2024-01-01_12-00-00_desc-desc.txt
│           └── ...
└── tiktok/
    └── post/
        └── user_nickname/
            └── ...
```

---

## 五、关键工具类速查

### 抖音
| 功能 | 类 | 方法 |
|------|-----|------|
| 提取作品 ID | `AwemeIdFetcher` | `get_aweme_id(url)` |
| 批量提取作品 ID | `AwemeIdFetcher` | `get_all_aweme_id(urls)` |
| 提取用户 SecUID | `SecUserIdFetcher` | `get_sec_user_id(url)` |
| 提取合集 ID | `MixIdFetcher` | `get_mix_id(url)` |
| 提取直播间 ID | `WebCastIdFetcher` | `get_webcast_id(url)` |
| Handler（完整流程） | `DouyinHandler` | `handle_one_video()`, `handle_user_post()` 等 |
| 爬虫 | `DouyinCrawler` | `fetch_user_profile()`, `fetch_user_post()` 等 |
| 下载器 | `DouyinDownloader` | `create_download_task()`, `download_video()` 等 |

### Twitter
| 功能 | 类 | 方法 |
|------|-----|------|
| 提取推文 ID | `TweetIdFetcher` | `get_tweet_id(url)` |
| 批量提取推文 ID | `TweetIdFetcher` | `get_all_tweet_ids(urls)` |
| 提取用户唯一 ID | `UniqueIdFetcher` | `get_unique_id(url)` |
| Handler（完整流程） | `TwitterHandler` | `handle_one_tweet()`, `handle_post_tweet()` 等 |
| 爬虫 | `TwitterCrawler` | `fetch_user_profile()`, `fetch_post_tweet()` 等 |
| 下载器 | `TwitterDownloader` | `create_download_task()`, `download_video()` 等 |

### TikTok
| 功能 | 类 | 方法 |
|------|-----|------|
| 提取作品 ID | `AwemeIdFetcher` | `get_aweme_id(url)` |
| 提取用户 SecUID | `SecUserIdFetcher` | `get_sec_user_id(url)` |
| Handler（完整流程） | `TiktokHandler` | `handle_one_video()`, `handle_user_post()` 等 |

---

## 六、注意事项

1. **Cookie 管理**：
   - Cookie 有过期时间，失效后需重新提取
   - Cookie 只能包含 ASCII 字符
   - Twitter 额外需要 `X-Csrf-Token`

2. **代理设置**：
   - 下载 Twitter/X 通常需要代理
   - 格式：`--proxies http://x.x.x.x https://x.x.x.x`
   - 如果代理不支持 HTTPS 出口：`--proxies http://x.x.x.x http://x.x.x.x`

3. **异步特性**：
   - F2 是异步库，API 调用必须在 async 函数中进行
   - 所有爬虫接口使用 `async for` 迭代

4. **模式说明**：
   - `collection` 模式（收藏作品）需要登录
   - `mix` 模式的 URL 可以是合集链接或合集中的作品链接
   - `live` 模式暂不支持 360° 等特殊直播间

5. **F2 自动识别**：F2 能智能识别混乱文本中的链接，支持长短链输入

---

## 七、已知 Bug 及修复

### 1. Twitter API 响应结构变化 (instructions[0] → instructions[1])

**现象**：`Pydantic ValidationError`，`screen_name` 为 None
**原因**：Twitter API 返回的 `instructions` 数组第一个元素变为 `TimelineClearCache`，实际数据在 `instructions[1]`
**修复**：将 `filter.py` 中所有 jsonpath 的 `instructions[0]` 改为 `instructions[1]`（约 35 处）
**影响文件**：`f2/apps/twitter/filter.py`

### 2. extract_desc 处理 None 值崩溃

**现象**：`AttributeError: 'NoneType' object has no attribute 'strip'`
**原因**：推文 `full_text` 字段可能为 None，`extract_desc` 未做空值检查
**修复**：在 `extract_desc` 函数开头添加 `if text is None: return ""`
**影响文件**：`f2/apps/twitter/utils.py`

### 3. Twitter 视频下载为 M3U8 文本而非 MP4

**现象**：下载的 .mp4 文件仅 1-2KB，实际为 M3U8 HLS 播放列表文本，无法播放
**原因**：`TweetDetailFilter.tweet_video_url` 的 jsonpath `variants[*].url` 返回所有变体 URL，第一个是 `application/x-mpegURL` (M3U8)，而非 `video/mp4`
**修复**：改为提取完整 `variants` 对象，过滤 `content_type == "video/mp4"` 的项，按 `bitrate` 降序取最高码率的 URL
**影响文件**：`f2/apps/twitter/filter.py` — `TweetDetailFilter.tweet_video_url` 属性
**修复代码**：
```python
@property
def tweet_video_url(self):
    variants = self._get_attr_value(
        "$.data.threaded_conversation_with_injections_v2.instructions[1].entries[0].content.itemContent.tweet_results.result.legacy.extended_entities.media[*].video_info.variants[*]"
    )
    if not variants:
        return None
    if isinstance(variants, list):
        flat = []
        for v in variants:
            if isinstance(v, list):
                flat.extend(v)
            else:
                flat.append(v)
        mp4_variants = [v for v in flat if isinstance(v, dict) and v.get("content_type") == "video/mp4"]
        if not mp4_variants:
            return None
        mp4_variants.sort(key=lambda x: x.get("bitrate", 0), reverse=True)
        return mp4_variants[0].get("url")
    return None
```

> **注意**：以上修复均直接修改了 f2 库源码。如果重新安装/更新 f2，需要重新应用这些修复。建议在项目中保存补丁或使用本地修改版本。
