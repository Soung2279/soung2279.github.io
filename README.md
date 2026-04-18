# Sprite Sheet Maker · 序列帧合并器

将一组按序排列的帧图片合并为一张精灵表（Sprite Sheet），特效动画制作用。

> **Merge sequential frame images into a single sprite sheet for effects animation.**

---

## 功能 Features

| 功能 | 说明 |
|------|------|
| 自动排列 | 按文件名自然排序（`frame2` 排在 `frame10` 前）|
| 自由配置列数 | 指定列数，或留 `0` 自动计算（`ceil(√n)`）|
| 帧间距 | 支持设置帧与帧之间的像素间距 |
| 背景色 | 透明 / 任意 RGBA 颜色 |
| 统一缩放 | 合并前将所有帧缩放到同一尺寸 |
| 图形界面 | 内置 tkinter GUI，无需记命令 |
| 命令行 | 完整 CLI，方便批处理/脚本集成 |
| 格式支持 | PNG · JPEG · BMP · GIF · WebP |

---

## 安装 Installation

```bash
pip install -r requirements.txt
```

> 如果需要使用 GUI，还需要安装 tkinter（通常随 Python 一起提供）：
> ```bash
> # Debian/Ubuntu
> sudo apt install python3-tk
> ```

---

## 使用方法 Usage

### 图形界面 GUI

直接运行脚本（无参数）即可打开 GUI：

```bash
python sprite_sheet_maker.py
```

操作步骤：
1. 点击 **浏览** 选择帧图片文件夹
2. 根据需要调整列数、间距、背景色、缩放选项
3. 指定输出文件路径
4. 点击 **▶ 合成 Generate**

---

### 命令行 CLI

```
python sprite_sheet_maker.py <folder> [options]
```

| 参数 | 说明 | 默认 |
|------|------|------|
| `folder` | 包含帧图片的文件夹 | 必填 |
| `-o`, `--output` | 输出文件路径 | `sprite_sheet.png` |
| `-c`, `--columns` | 列数（0 = 自动） | `0` |
| `-p`, `--padding` | 帧间距（像素） | `0` |
| `--bg` | 背景色（`transparent` / `#RRGGBB` / `#RRGGBBAA`） | `transparent` |
| `--resize` | 统一缩放尺寸，例如 `64x64` | 不缩放 |
| `--gui` | 启动图形界面 | — |

#### 示例 Examples

```bash
# 基本用法：自动列数，透明背景
python sprite_sheet_maker.py frames/ -o sheet.png

# 指定 8 列，2px 间距
python sprite_sheet_maker.py frames/ -c 8 -p 2 -o sheet.png

# 统一缩放到 64×64，白色背景
python sprite_sheet_maker.py frames/ --resize 64x64 --bg "#ffffff" -o sheet.png

# 统一缩放到 64×64，透明背景，6 列
python sprite_sheet_maker.py frames/ --resize 64x64 -c 6 -o sheet.png
```

---

## 运行测试 Running Tests

```bash
pip install pytest
python -m pytest test_sprite_sheet_maker.py -v
```

---

## 支持格式 Supported Formats

`.png` · `.jpg` / `.jpeg` · `.bmp` · `.gif` · `.webp`

所有帧在合成前会统一转换为 RGBA 模式。若各帧尺寸不一致，请使用 `--resize` 参数进行统一缩放。

---

## 许可 License

MIT
