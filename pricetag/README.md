# pricetag

把 Claude 用量渲染成 1-bit 图，推到一块刷了开源固件的汉朔 Nebular 价签上。

## 当前状态

- 渲染：能跑。`python3 main.py --mock` 出图，布局对照示例。
- 数据：`ccusage statusline --json` 接好了，schema 不稳定时回落到 mock。
- BLE 推送：**还没接**。等价签刷完 [atc1441](https://github.com/atc1441/ATC_TLSR_Paper) 固件、能跟 WebFlasher 通上之后再补——`ble.py` 里有占位说明。

## 跑一下

```bash
pip install -r requirements.txt          # pillow, bleak
python3 main.py --mock                    # 渲染 mock 数据到 out/tag.png
python3 main.py                           # 走真实 ccusage
python3 main.py --save my.png             # 自定义输出路径
```

复制 `config.example.toml` -> `config.toml` 改尺寸/字体/标题。

## 字体

默认走 macOS：

- CJK：`/System/Library/Fonts/PingFang.ttc`
- 等宽：`/System/Library/Fonts/Menlo.ttc`

其他系统改 `[fonts]`。脚本里有 Linux fallback。

## 文件

```
main.py             # CLI 入口
usage.py            # 取 ccusage 数据 + mock 兜底
render.py           # PIL 画图
ble.py              # 推送骨架（TODO）
config.example.toml # 默认配置
```

## 还要做的事

1. **刷固件**（你已下单工具，等货）
2. **拿到 BLE MAC** —— 刷完之后 WebFlasher 会显示
3. **填 `config.toml` 的 `[ble].mac`**
4. **照 atc1441 的 `Image_Uploader.html` 把 BLE 协议补到 `ble.py`**：service/characteristic UUID、分块大小、握手序列
5. **可选**：起个 launchd / cron 每 N 分钟跑一次，让价签自动刷新

## 显示尺寸

默认 400×300，按 Nebular 4.2" 假设。等你拆开看到实际屏幕信息再 `[display]` 里调。
