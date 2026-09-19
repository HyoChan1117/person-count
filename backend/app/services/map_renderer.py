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

    img = Image.new("RGB", (mapW, mapH), _hex("#ffffff"))
    draw = ImageDraw.Draw(img)

    border = _hex("#a9b3c2")
    chair_fill = _hex("#e2e8f1")
    text = _hex("#061735")
    muted_text = _hex("#53647f")

    for obj in objects:
        x, y, w, h = int(obj["x"]), int(obj["y"]), int(obj["w"]), int(obj["h"])
        t = obj.get("type")

        if t == "chair":
            draw.rounded_rectangle([x, y, x+w, y+h], radius=8, fill=chair_fill)

        elif t == "cctv":
            draw.rounded_rectangle([x, y, x+w, y+h], radius=12,
                                    fill=_hex("#ffffff"), outline=border, width=3)
            label = obj.get("label") or "CCTV"
            fsize = max(10, min(int(h * 0.24), 22, int((w * 0.78) / (max(1, len(label)) * 0.7))))
            draw.text((x + w / 2, y + h / 2), label, fill=muted_text,
                      anchor="mm", font=_font(fsize))

        elif t == "desk":
            label = (obj.get("label") or "").strip()
            is_occ = bool(label and label in occupied)
            fill = _hex("#d9efea") if is_occ else _hex("#ffffff")
            outline = _hex("#147b70") if is_occ else border
            draw.rounded_rectangle([x, y, x+w, y+h], radius=10,
                                   fill=fill, outline=outline, width=3)
            if label:
                fsize = max(11, min(int(h * 0.42), 30))
                draw.text((x + w / 2, y + h / 2), label,
                          fill=text, anchor="mm", font=_font(fsize))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


