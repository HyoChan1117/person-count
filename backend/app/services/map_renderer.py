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
    near: set[str] | None = None,
) -> bytes:
    """배치도 PNG bytes 반환. occupied/near/empty 는 좌석 라벨 집합."""
    near = (near or set()) - occupied  # 빨강 우선
    objects = map_data.get("objects", [])
    mapW = int(map_data.get("mapW", 900))
    mapH = int(map_data.get("mapH", 600))

    img = Image.new("RGB", (mapW, mapH), _hex("#f8fafc"))
    draw = ImageDraw.Draw(img)

    # 그리드
    grid_color = _hex("#e2e8f0")
    for x in range(0, mapW + 1, 40):
        draw.line([(x, 0), (x, mapH)], fill=grid_color, width=1)
    for y in range(0, mapH + 1, 40):
        draw.line([(0, y), (mapW, y)], fill=grid_color, width=1)

    for obj in objects:
        x, y, w, h = int(obj["x"]), int(obj["y"]), int(obj["w"]), int(obj["h"])
        t = obj.get("type")

        if t == "chair":
            draw.rounded_rectangle([x, y, x+w, y+h], radius=3, fill=_hex("#e2e8f0"))

        elif t == "cctv":
            draw.rounded_rectangle([x, y, x+w, y+h], radius=4, fill=_hex("#475569"))
            label = obj.get("label") or "CAM"
            fsize = max(9, min(int(h * 0.28), 13))
            draw.text((x + w / 2, y + h / 2), label, fill="white",
                      anchor="mm", font=_font(fsize))

        elif t == "desk":
            label = (obj.get("label") or "").strip()
            is_occ   = bool(label and label in occupied)
            is_near  = bool(label and not is_occ and label in near)
            is_empty = bool(label and not is_occ and not is_near and label in empty)
            fill    = "#fee2e2" if is_occ else "#ffedd5" if is_near else "#dcfce7" if is_empty else "#f5e9cc"
            outline = "#ef4444" if is_occ else "#f97316" if is_near else "#22c55e" if is_empty else "#c9a55a"
            draw.rounded_rectangle(
                [x, y, x+w, y+h], radius=5,
                fill=_hex(fill), outline=_hex(outline), width=2,
            )
            if label:
                text_color = "#dc2626" if is_occ else "#ea580c" if is_near else "#16a34a" if is_empty else "#5a3e1b"
                fsize = max(9, min(int(h * 0.38), 16))
                draw.text((x + w / 2, y + h / 2), label,
                          fill=_hex(text_color), anchor="mm", font=_font(fsize))

    # 범례 (하단 중앙)
    legend_items = [
        ("#fee2e2", "#ef4444", "점유"),
        ("#ffedd5", "#f97316", "근접(미착석)"),
        ("#dcfce7", "#22c55e", "미점유"),
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
