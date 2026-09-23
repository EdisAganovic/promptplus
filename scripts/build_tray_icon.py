"""Rasterize the lightning artwork into matching app and tray icons."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (ROOT / "electron" / "tray.ico", ROOT / "icon.ico")
SIZES = (16, 20, 24, 32, 48, 64, 128, 256)
SCALE = 4


def render(size):
    canvas_size = size * SCALE
    factor = canvas_size / 512
    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (0, 0, canvas_size - 1, canvas_size - 1),
        radius=round(100 * factor),
        fill="#1a1b27",
    )
    bolt = ((284, 58), (123, 282), (234, 282), (214, 454), (389, 208), (276, 208))
    draw.polygon([(round(x * factor), round(y * factor)) for x, y in bolt], fill="#34d399")
    return image.resize((size, size), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    images = [render(size) for size in SIZES]
    for output in OUTPUTS:
        images[-1].save(output, format="ICO", append_images=images[:-1], sizes=[(size, size) for size in SIZES])
        print(output)
