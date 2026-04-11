# SnatchIt

跨平台视频下载客户端 - 支持抖音和 Twitter/X

## 功能

- 支持抖音 (Douyin) 视频下载
- 支持 Twitter/X 推文下载
- 自动从浏览器获取 Cookie（无需手动配置）
- 实时下载进度显示
- 下载日志查看

## 系统要求

- Windows 10/11 (macOS/Linux 支持后续添加)
- Python 3.10+

## 快速开始

### 源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/Gekko-z/SnatchIt.git
cd SnatchIt

# 2. 安装依赖
pip install -e .

# 3. 运行
python -m snatchit.main
```

### 下载独立版本

前往 [Releases](https://github.com/Gekko-z/SnatchIt/releases) 下载打包好的 exe 文件（后续提供）。

## 使用说明

1. 选择平台（抖音 或 Twitter）
2. 粘贴视频/推文链接
3. 选择保存路径
4. 点击"从浏览器获取"自动获取 Cookie（或手动粘贴）
5. 点击"开始下载"

## Cookie 获取

SnatchIt 支持通过浏览器远程调试自动获取 Cookie：
- 确保你的 Edge/Chrome 浏览器已登录对应平台账号
- 点击"从浏览器获取"按钮
- 自动启动浏览器并提取 Cookie

## 开发文档

详细的开发指南请参阅 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。

## 许可证

MIT
