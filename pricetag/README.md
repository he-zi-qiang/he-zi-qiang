# pricetag

把 Claude 用量渲染成黑/白/红三色图，推到一块刷了开源固件的汉朔 Nebular 价签（420R-N，4.2" BWR）上。

预览：`examples/preview.png`

## 当前状态

- **渲染**：三色 (黑/白/红)，`python3 main.py --mock` 出图。Title 用红色，进度条 ≥ 80% 时填红示警。
- **数据**：`ccusage statusline --json` 取真实用量；不可用时用 `--mock`。
- **吉祥物**：右上角有 8 角 Anthropic-mark 占位 sparkle。**把任意 PNG 放到 `assets/mascot.png`，渲染会自动用你的**（带透明通道也行）。
- **BLE 推送**：还没接。等价签刷完 [atc1441 固件](https://github.com/atc1441/ATC_TLSR_Paper) 拿到 MAC 之后补——`ble.py` 里有说明。

## 跑一下

```bash
pip install -r requirements.txt          # pillow, bleak
python3 main.py --mock                    # mock 数据
python3 main.py                           # 真实 ccusage
python3 main.py --save my.png             # 改输出路径
```

输出三个文件：

- `tag.png` — RGB 预览（你看效果用）
- `tag_bw.png` — 1-bit 黑通道（给 BWR 固件用）
- `tag_red.png` — 1-bit 红通道（给 BWR 固件用）

复制 `config.example.toml` → `config.toml` 调标题、序列号、字体、mascot 路径。

## 字体

macOS 默认：

- CJK：`/System/Library/Fonts/PingFang.ttc`
- 等宽：`/System/Library/Fonts/Menlo.ttc`

其他系统改 `[fonts]`，Linux 自带 fallback。

## 换吉祥物

```bash
# 把任意 PNG 丢进去
cp ~/Downloads/my-mascot.png assets/mascot.png
python3 main.py --mock
```

会自动缩放到 48×48 贴左上角。透明背景效果最好。

## 文件

```
main.py                # CLI 入口
usage.py               # 取 ccusage 数据 + mock 兜底
render.py              # PIL 三色画图 + BW/Red 通道拆分
ble.py                 # 推送骨架（TODO）
config.example.toml    # 默认配置
assets/mascot.png      # 可选，你的吉祥物图
examples/preview.png   # 渲染预览
```

## 还要做的事

1. **刷固件**（你已下单工具，等货）
2. **拆机拍 PCB 照片** → 我帮你标 SWS / NRST / GND
3. **焊飞线 → Chrome 跑 [WebFlasher](https://atc1441.github.io/ATC_TLSR_Paper_Flasher.html) → 刷 OEPL/BWR 固件**
4. **拿到 BLE MAC**，填 `config.toml` 的 `[ble].mac`
5. **照 atc1441 的 `Image_Uploader.html` 把 BLE 协议补到 `ble.py`**
6. **可选**：起个 launchd 每 10 分钟跑一次

## Nebular-420R-N 默认假设

- 4.2" e-paper, 400×300
- BWR (黑/白/红)
- TLSR8359 主控
- NFC 是辅助通道（提供 BLE MAC 而已），数据走 BLE

实际拆开看到不对劲再调 `[display]`。
