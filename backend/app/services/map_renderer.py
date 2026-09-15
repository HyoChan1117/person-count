"""교실 배치도 + 좌석 점유 오버레이를 Pillow로 렌더링."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _hex(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def render_occupancy_map(
    map_data: dict,
    occupied: set[str],
    empty: set[str],
) -> bytes:
    """배치도 PNG bytes 반환. occupied/empty 는 좌석 라벨 집합."""
    objects = map_data.get("objects", [])
    mapW = int(map_data.get("mapW", 900))
    mapH = int(map_data.get("mapH", 600))

    img = Image.new("RGB", (mapW, mapH), _hex("#f8fafc"))
    draw = ImageDraw.Draw(img)

    for obj in objects:
        x, y, w, h = int(obj["x"]), int(obj["y"]), int(obj["w"]), int(obj["h"])
        t = obj.get("type")

        if t == "chair":
            draw.rounded_rectangle([x, y, x+w, y+h], radius=3, fill=_hex("#e2e8f0"))

        elif t == "cctv":
            draw.rounded_rectangle([x, y, x+w, y+h], radius=4,
                                    fill=_hex("#e2e8f0"), outline=_hex("#94a3b8"), width=1)
            label = obj.get("label") or "CAM"
            fsize = max(9, min(int(h * 0.28), 13))
            draw.text((x + w / 2, y + h / 2), label, fill=_hex("#334155"),
                      anchor="mm", font=_font(fsize))

        elif t == "desk":
            label = (obj.get("label") or "").strip()
            is_occ   = bool(label and label in occupied)
            is_empty = bool(label and not is_occ and label in empty)
            fill    = "#fee2e2" if is_occ else "#f1f5f9" if is_empty else "#f8fafc"
            outline = "#ef4444" if is_occ else "#94a3b8" if is_empty else "#cbd5e1"
            draw.rectangle([x, y, x+w, y+h], fill=_hex(fill), outline=_hex(outline), width=2)
            if label:
                text_color = "#dc2626" if is_occ else "#64748b" if is_empty else "#1e293b"
                fsize = max(9, min(int(h * 0.38), 16))
                draw.text((x + w / 2, y + h / 2), label,
                          fill=_hex(text_color), anchor="mm", font=_font(fsize))

    # 범례 (하단 중앙)
    legend_items = [
        ("#fee2e2", "#ef4444", "점유"),
        ("#f1f5f9", "#94a3b8", "미점유"),
    ]
    item_w = 90  # 아이템 하나당 폭
    total_w = item_w * len(legend_items)
    lx = (mapW - total_w) // 2
    legend_y = mapH - 28
    for fill, outline, text in legend_items:
        draw.rounded_rectangle([lx, legend_y, lx+16, legend_y+16],
                               radius=3, fill=_hex(fill), outline=_hex(outline), width=1)
        draw.text((lx + 20, legend_y + 8), text, fill=_hex("#475569"),
                  anchor="lm", font=_font(12))
        lx += item_w

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


