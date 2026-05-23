# pricetag

把 Claude 用量渲染成黑/白/红三色图，推到一块刷了 OpenEPaperLink 固件的汉朔 Nebular 420R-N 价签上。

预览：`examples/preview.png`

## 架构

```
[你 PC]
   │  HTTP POST /imgupload
   ▼
[ESP32-S3 AP]   ← OpenEPaperLink 固件
   │  BLE
   ▼
[价签]          ← OEPL TLSR 固件（不是 atc1441 ATC_Paper.bin）
```

理由：atc1441 的 BLE 固件没有 Nebular 4.2" BWR 的屏驱，OEPL 才支持。OEPL 用 ESP32 当
AP，PC 走 HTTP 推图。

## 当前状态

- **渲染**：三色 (黑/白/红)，`python3 main.py --mock` 出图。
- **数据**：`ccusage statusline --json` 或 `--mock`。
- **吉祥物**：8 角 Anthropic sparkle 占位，自带 `assets/mascot.png` 槽位。
- **推送**：HTTP POST 到 OEPL AP 的 `/imgupload` 接口。
- **硬件**：见 `HARDWARE.md`（接线 + 刷机步骤）。

## 跑一下

```bash
pip install -r requirements.txt          # 只需 pillow（push 走 stdlib urllib）
python3 main.py --mock                    # 渲染 mock 数据
python3 main.py                           # 真实 ccusage
python3 main.py --push                    # 推到价签（需配好 config.toml）
python3 main.py --push --dither           # 启用 AP 抖动（拍照风格用）
```

输出三个文件：

- `tag.png` — RGB 预览
- `tag_bw.png` — 黑通道（参考用，OEPL AP 自己会再次处理）
- `tag_red.png` — 红通道

## 配置

复制 `config.example.toml` → `config.toml`：

```toml
[oepl]
ap_url  = "http://192.168.1.42"  # ESP32-S3 AP 的 IP
tag_mac = "00000197E5CB3B38"     # 价签 MAC（在 AP web UI 里看）

[fonts]
cjk  = "/System/Library/Fonts/PingFang.ttc"   # 或 C:/Windows/Fonts/msyh.ttc
mono = "/System/Library/Fonts/Menlo.ttc"      # 或 C:/Windows/Fonts/consola.ttf
```

## 文件

```
main.py                # CLI 入口
usage.py               # ccusage + mock 兜底
render.py              # 三色 PIL 画图 + BW/Red 通道拆分
oepl.py                # HTTP POST 到 OEPL AP
config.example.toml    # 默认配置
HARDWARE.md            # 接线、刷机步骤
docs/wiring_official.jpg  # atc1441 官方接线图
assets/mascot.png      # 可选吉祥物（用户提供）
examples/preview.png   # 渲染预览
```

## 还要做的事

1. **采购**：USB-TTL ✅、烙铁 ✅、ESP32-S3-N16R8 ⏳
2. **刷价签**：UART Flasher + OEPL TLSR 固件（不是 atc1441 那个 .bin）
3. **刷 ESP32**：[install.openepaperlink.de](https://install.openepaperlink.de/) → 选 BLE-only S3 build
4. **配 WiFi**：ESP32 起 AP 网络 `OpenEPaperLink`，连上去配你家 WiFi
5. **配对**：价签自动被 AP 发现，记下 AP 的 IP 和 价签的 MAC
6. **填 `config.toml`**，跑 `python3 main.py --push`

## Nebular-420R-N 假设

- 4.2" e-paper, 400×300, BWR
- TLSR8258（已通过 PCB 印字确认）
- 装回去后能闲鱼买的硬件配置

实际拆开发现不对劲再调 `[display]` 尺寸。
