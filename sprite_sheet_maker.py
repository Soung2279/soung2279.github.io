"""
Sprite Sheet Maker
序列帧图片合并器 - 将一组按序排列的图片合并为一张精灵表（Sprite Sheet）
"""

import os
import re
import math
import argparse

from PIL import Image

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, colorchooser
    _HAS_TK = True
except ModuleNotFoundError:
    _HAS_TK = False


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def natural_sort_key(name: str):
    """Sort filenames naturally so that frame2 comes before frame10."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", name)]


def collect_images(folder: str) -> list:
    """Return sorted image file paths from *folder*."""
    entries = [
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
    ]
    entries.sort(key=natural_sort_key)
    return [os.path.join(folder, f) for f in entries]


def make_sprite_sheet(
    image_paths,
    columns=0,
    padding=0,
    bg_color=(0, 0, 0, 0),
    output_path="sprite_sheet.png",
    resize=None,
    progress_callback=None,
):
    """
    Merge *image_paths* into a sprite sheet.

    Parameters
    ----------
    image_paths:        Ordered list of image file paths.
    columns:            Number of columns.  0 = auto (ceil(sqrt(n))).
    padding:            Pixel gap between frames.
    bg_color:           Background RGBA tuple.
    output_path:        Where to write the result.
    resize:             (width, height) to force every frame to this size.
                        None = keep original size (all frames must be same size).
    progress_callback:  Optional callable(current, total).

    Returns
    -------
    Absolute path of the written sprite sheet.
    """
    if not image_paths:
        raise ValueError("No images provided.")

    total = len(image_paths)
    frames = []

    for i, path in enumerate(image_paths, 1):
        img = Image.open(path).convert("RGBA")
        if resize:
            img = img.resize(resize, Image.LANCZOS)
        frames.append(img)
        if progress_callback:
            progress_callback(i, total)

    # Determine frame size (all must be equal after optional resize)
    fw, fh = frames[0].size
    for f in frames[1:]:
        if f.size != (fw, fh):
            raise ValueError(
                f"Frame sizes differ ({fw}x{fh} vs {f.size[0]}x{f.size[1]}). "
                "Use --resize to normalise them."
            )

    cols = columns if columns > 0 else math.ceil(math.sqrt(total))
    rows = math.ceil(total / cols)

    sheet_w = cols * fw + (cols - 1) * padding
    sheet_h = rows * fh + (rows - 1) * padding

    sheet = Image.new("RGBA", (sheet_w, sheet_h), bg_color)

    for idx, frame in enumerate(frames):
        col = idx % cols
        row = idx // cols
        x = col * (fw + padding)
        y = row * (fh + padding)
        sheet.paste(frame, (x, y))

    sheet.save(output_path)
    return os.path.abspath(output_path)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def parse_color(value):
    """Parse a hex color (#RRGGBB or #RRGGBBAA) or 'transparent'."""
    value = value.strip()
    if value.lower() == "transparent":
        return (0, 0, 0, 0)
    if value.startswith("#"):
        value = value[1:]
    if len(value) == 6:
        r, g, b = int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
        return (r, g, b, 255)
    if len(value) == 8:
        r, g, b, a = (int(value[i:i+2], 16) for i in range(0, 8, 2))
        return (r, g, b, a)
    raise argparse.ArgumentTypeError(
        f"Invalid color '{value}'. Use #RRGGBB, #RRGGBBAA, or 'transparent'."
    )


def parse_size(value):
    """Parse WIDTHxHEIGHT string."""
    parts = value.lower().split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Size must be WIDTHxHEIGHT, e.g. 64x64")
    return (int(parts[0]), int(parts[1]))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cli_main():
    parser = argparse.ArgumentParser(
        description="序列帧图片合并器 — Sprite Sheet Maker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sprite_sheet_maker.py frames/ -o sheet.png
  python sprite_sheet_maker.py frames/ -c 8 -p 2 -o sheet.png
  python sprite_sheet_maker.py frames/ --resize 64x64 --bg transparent
        """,
    )
    parser.add_argument("folder", help="Folder containing the sequential frame images.")
    parser.add_argument("-o", "--output", default="sprite_sheet.png",
                        help="Output file path (default: sprite_sheet.png).")
    parser.add_argument("-c", "--columns", type=int, default=0,
                        help="Number of columns (default: auto).")
    parser.add_argument("-p", "--padding", type=int, default=0,
                        help="Pixel gap between frames (default: 0).")
    parser.add_argument("--bg", default="transparent", type=parse_color,
                        metavar="COLOR",
                        help="Background color: #RRGGBB, #RRGGBBAA, or 'transparent' (default).")
    parser.add_argument("--resize", type=parse_size, default=None,
                        metavar="WxH",
                        help="Resize every frame to this size before merging, e.g. 64x64.")
    parser.add_argument("--gui", action="store_true",
                        help="Launch the graphical interface instead.")

    args = parser.parse_args()

    if args.gui:
        gui_main()
        return

    paths = collect_images(args.folder)
    if not paths:
        parser.error(f"No supported images found in '{args.folder}'.")

    print(f"Found {len(paths)} frames.")

    def progress(current, total):
        bar_len = 40
        filled = int(bar_len * current / total)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"\r[{bar}] {current}/{total}", end="", flush=True)

    out = make_sprite_sheet(
        paths,
        columns=args.columns,
        padding=args.padding,
        bg_color=args.bg,
        output_path=args.output,
        resize=args.resize,
        progress_callback=progress,
    )
    print(f"\nSaved -> {out}")


# ---------------------------------------------------------------------------
# GUI (only defined when tkinter is available)
# ---------------------------------------------------------------------------

if _HAS_TK:
    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Sprite Sheet Maker  |  序列帧合并器")
            self.resizable(False, False)
            self._build_ui()

        def _build_ui(self):
            pad = {"padx": 8, "pady": 4}

            # Input folder
            frm_src = ttk.LabelFrame(self, text="输入文件夹  Input Folder")
            frm_src.grid(row=0, column=0, columnspan=3, sticky="ew", **pad)

            self.var_folder = tk.StringVar()
            ttk.Entry(frm_src, textvariable=self.var_folder, width=48).grid(
                row=0, column=0, padx=4, pady=4)
            ttk.Button(frm_src, text="浏览...", command=self._browse_folder).grid(
                row=0, column=1, padx=4, pady=4)

            self.lbl_count = ttk.Label(frm_src, text="未选择文件夹")
            self.lbl_count.grid(row=1, column=0, columnspan=2, padx=4, pady=(0, 4))

            # Options
            frm_opt = ttk.LabelFrame(self, text="选项  Options")
            frm_opt.grid(row=1, column=0, columnspan=3, sticky="ew", **pad)

            ttk.Label(frm_opt, text="列数 Columns (0=自动):").grid(
                row=0, column=0, sticky="w", padx=4, pady=2)
            self.var_cols = tk.IntVar(value=0)
            ttk.Spinbox(frm_opt, from_=0, to=999, textvariable=self.var_cols,
                        width=6).grid(row=0, column=1, sticky="w", padx=4, pady=2)

            ttk.Label(frm_opt, text="间距 Padding (px):").grid(
                row=1, column=0, sticky="w", padx=4, pady=2)
            self.var_padding = tk.IntVar(value=0)
            ttk.Spinbox(frm_opt, from_=0, to=999, textvariable=self.var_padding,
                        width=6).grid(row=1, column=1, sticky="w", padx=4, pady=2)

            ttk.Label(frm_opt, text="背景色 Background:").grid(
                row=2, column=0, sticky="w", padx=4, pady=2)
            self.var_transparent = tk.BooleanVar(value=True)
            ttk.Checkbutton(frm_opt, text="透明 Transparent",
                            variable=self.var_transparent,
                            command=self._toggle_bg).grid(
                row=2, column=1, sticky="w", padx=4, pady=2)
            self.btn_bg = ttk.Button(frm_opt, text="选色...", command=self._pick_color,
                                     state="disabled")
            self.btn_bg.grid(row=2, column=2, padx=4, pady=2)
            self._bg_color = (0, 0, 0, 0)
            self._bg_preview = tk.Label(frm_opt, width=3, relief="solid",
                                        bg="#000000")
            self._bg_preview.grid(row=2, column=3, padx=4, pady=2)

            ttk.Label(frm_opt, text="缩放 Resize (宽x高, 留空=不缩放):").grid(
                row=3, column=0, sticky="w", padx=4, pady=2)
            self.var_resize = tk.StringVar()
            ttk.Entry(frm_opt, textvariable=self.var_resize, width=12).grid(
                row=3, column=1, sticky="w", padx=4, pady=2)

            # Output file
            frm_out = ttk.LabelFrame(self, text="输出文件  Output File")
            frm_out.grid(row=2, column=0, columnspan=3, sticky="ew", **pad)

            self.var_output = tk.StringVar(value="sprite_sheet.png")
            ttk.Entry(frm_out, textvariable=self.var_output, width=48).grid(
                row=0, column=0, padx=4, pady=4)
            ttk.Button(frm_out, text="另存为...", command=self._browse_output).grid(
                row=0, column=1, padx=4, pady=4)

            # Progress bar
            self.progress_var = tk.DoubleVar(value=0)
            self.progress_bar = ttk.Progressbar(self, variable=self.progress_var,
                                                maximum=100, length=400)
            self.progress_bar.grid(row=3, column=0, columnspan=3, padx=8, pady=4,
                                   sticky="ew")
            self.lbl_status = ttk.Label(self, text="")
            self.lbl_status.grid(row=4, column=0, columnspan=3)

            # Run button
            ttk.Button(self, text="▶  合成  Generate", command=self._run).grid(
                row=5, column=0, columnspan=3, pady=8)

        def _browse_folder(self):
            folder = filedialog.askdirectory(title="选择帧图片文件夹")
            if not folder:
                return
            self.var_folder.set(folder)
            paths = collect_images(folder)
            count = len(paths)
            self.lbl_count.config(
                text=f"找到 {count} 张图片" if count else "该文件夹中没有支持的图片"
            )

        def _browse_output(self):
            path = filedialog.asksaveasfilename(
                title="保存精灵表",
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("All files", "*.*")],
            )
            if path:
                self.var_output.set(path)

        def _toggle_bg(self):
            if self.var_transparent.get():
                self._bg_color = (0, 0, 0, 0)
                self.btn_bg.config(state="disabled")
            else:
                self.btn_bg.config(state="normal")

        def _pick_color(self):
            color = colorchooser.askcolor(title="选择背景色")
            if color and color[0]:
                r, g, b = (int(v) for v in color[0])
                self._bg_color = (r, g, b, 255)
                hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                self._bg_preview.config(bg=hex_color)

        def _run(self):
            folder = self.var_folder.get().strip()
            if not folder or not os.path.isdir(folder):
                messagebox.showerror("错误", "请先选择有效的输入文件夹。")
                return

            paths = collect_images(folder)
            if not paths:
                messagebox.showerror("错误", "文件夹中没有支持的图片文件。")
                return

            output = self.var_output.get().strip()
            if not output:
                messagebox.showerror("错误", "请指定输出文件路径。")
                return

            resize = None
            resize_str = self.var_resize.get().strip()
            if resize_str:
                try:
                    resize = parse_size(resize_str)
                except (argparse.ArgumentTypeError, ValueError):
                    messagebox.showerror("错误", "缩放格式不正确，请使用 宽x高，例如 64x64。")
                    return

            bg_color = (0, 0, 0, 0) if self.var_transparent.get() else self._bg_color

            self.progress_var.set(0)
            self.lbl_status.config(text="处理中...")
            self.update_idletasks()

            def progress(current, t):
                self.progress_var.set(current / t * 100)
                self.lbl_status.config(text=f"正在处理第 {current}/{t} 帧...")
                self.update_idletasks()

            try:
                out = make_sprite_sheet(
                    paths,
                    columns=self.var_cols.get(),
                    padding=self.var_padding.get(),
                    bg_color=bg_color,
                    output_path=output,
                    resize=resize,
                    progress_callback=progress,
                )
                self.lbl_status.config(text=f"完成！已保存至 {out}")
                messagebox.showinfo("完成", f"精灵表已保存至：\n{out}")
            except Exception as exc:
                self.lbl_status.config(text="出错！")
                messagebox.showerror("错误", str(exc))


def gui_main():
    if not _HAS_TK:
        raise RuntimeError(
            "tkinter is not available. Install it (e.g. 'apt install python3-tk') "
            "to use the GUI."
        )
    app = App()
    app.mainloop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        # No arguments -> launch GUI
        gui_main()
    else:
        cli_main()
