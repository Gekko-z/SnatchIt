# 抖音 Cookie 提取工具

## 用途
从已登录的 Microsoft Edge 浏览器中提取抖音 (douyin.com) 的 Cookie，用于 TikTokDownload 等工具的认证配置。

## 前提条件
- Python 3.11+ 已安装（路径: `C:\Python\python.exe`）
- `websocket-client` 库已安装
- Microsoft Edge 已安装（路径: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`）
- Edge 中已登录抖音账号

## 使用步骤

### 1. 确保 Edge 完全关闭
让用户手动关闭所有 Edge 进程，然后验证：
```bash
cmd.exe /c "tasklist | findstr msedge"  # 应该无输出
```

### 2. 创建 WebSocket 提取脚本
写入 `get_cookies_ws.py`：

```python
import json
import time
import subprocess
import urllib.request
import websocket

EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DEBUG_PORT = 9222

def start_edge():
    subprocess.Popen([
        EDGE_EXE,
        f"--remote-debugging-port={DEBUG_PORT}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.douyin.com"
    ], shell=True)
    print("Starting Edge...")

def wait_for_debug(max_wait=15):
    for i in range(max_wait):
        try:
            req = urllib.request.Request(f"http://localhost:{DEBUG_PORT}/json/version")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return json.loads(resp.read())
        except Exception:
            time.sleep(1)
    return None

def get_cookies_via_ws():
    req = urllib.request.Request(f"http://localhost:{DEBUG_PORT}/json")
    with urllib.request.urlopen(req, timeout=5) as resp:
        pages = json.loads(resp.read())

    douyin_page = None
    for page in pages:
        if 'douyin.com' in page.get('url', ''):
            douyin_page = page
            break

    if not douyin_page:
        print("No douyin page found.")
        print("Pages available:")
        for p in pages:
            print(f"  {p.get('title', '?')}: {p.get('url', 'blank')[:80]}")
        return None

    ws_url = douyin_page.get('webSocketDebuggerUrl', '')
    if not ws_url:
        print("No WebSocket URL found for the douyin page")
        return None

    print(f"Connecting to: {douyin_page.get('title', 'unknown')}")

    ws = websocket.create_connection(ws_url, timeout=10)

    cmd = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "document.cookie",
            "returnByValue": True
        }
    }
    ws.send(json.dumps(cmd))
    ws.settimeout(10)
    result = ws.recv()
    ws.close()

    response = json.loads(result)
    if 'result' in response and 'result' in response['result']:
        return response['result']['result'].get('value', '')

    print(f"Unexpected response: {response}")
    return None

if __name__ == '__main__':
    start_edge()
    if wait_for_debug():
        print("Edge connected, waiting for page to load...")
        time.sleep(5)
        cookies = get_cookies_via_ws()
        if cookies:
            print(f"\nCookie length: {len(cookies)}")
            print(f"\n=== FULL COOKIE STRING ===\n{cookies}")
        else:
            print("Failed to get cookies")
    else:
        print("Failed to connect to Edge")
```

### 3. 运行脚本
```bash
C:/Python/python.exe get_cookies_ws.py
```

脚本会：
1. 自动启动 Edge 并打开抖音页面
2. 用户确保 Edge 中已登录抖音
3. 通过 WebSocket 连接到 Edge 的 DevTools Protocol
4. 执行 `document.cookie` JavaScript 获取完整 Cookie 字符串

### 4. 写入配置文件
获取到 Cookie 字符串后，更新 `conf.ini`：

```python
import os

config_path = "conf.ini"  # 目标配置文件路径
cookie_string = "..."  # 上面脚本输出的完整 Cookie 字符串

with open(config_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('cookie ='):
        new_lines.append(f'cookie = "{cookie_string}"\n')
    else:
        new_lines.append(line)

with open(config_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
```

## 注意事项
- Cookie 有过期时间，失效后需要重新提取
- 提取过程中 Edge 必须完全关闭后再启动（带 `--remote-debugging-port` 参数）
- `--remote-allow-origins=*` 参数必须添加，否则 WebSocket 连接会被拒绝 (403 Forbidden)
- 此方法仅适用于 Chromium 内核浏览器（Edge/Chrome）
- 提取完成后脚本会自动关闭 Edge，或用户可以手动关闭
