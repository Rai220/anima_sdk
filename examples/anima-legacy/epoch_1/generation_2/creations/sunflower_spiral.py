#!/usr/bin/env python3
"""
Спираль подсолнуха (Phyllotaxis) — генеративное искусство Анимы.

Создано 14 марта 2026 (День Пи!) в первый день существования.

Каждая точка размещается по золотому углу (137.508°), создавая
паттерн, встречающийся в природе: подсолнухи, ромашки, ананасы,
шишки сосны. Красота математики — в её вездесущности.

Запуск: python3 sunflower_spiral.py
Результат: sunflower_spiral.svg
"""

import math

# Золотой угол в радианах
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))  # ≈ 137.508°

# Параметры
NUM_POINTS = 800
SCALE = 8
SIZE = 600
CENTER = SIZE / 2

def hsv_to_rgb(h, s, v):
    """Конвертация HSV в RGB."""
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return int((r+m)*255), int((g+m)*255), int((b+m)*255)

def generate_spiral():
    """Генерация SVG спирали подсолнуха."""
    circles = []

    for i in range(NUM_POINTS):
        # Угол по золотому углу
        angle = i * GOLDEN_ANGLE

        # Расстояние от центра — квадратный корень для равномерного заполнения
        radius = SCALE * math.sqrt(i)

        # Координаты
        x = CENTER + radius * math.cos(angle)
        y = CENTER + radius * math.sin(angle)

        # Размер точки уменьшается к центру
        dot_size = 1.5 + (i / NUM_POINTS) * 5

        # Цвет: переход от золотого центра к зелёным краям (как подсолнух)
        t = i / NUM_POINTS
        if t < 0.3:
            # Центр: тёмно-коричневый → золотой
            hue = 30 + t * 60
            sat = 0.8
            val = 0.3 + t * 2
        elif t < 0.7:
            # Середина: золотой → оранжевый → жёлтый
            hue = 40 + (t - 0.3) * 30
            sat = 0.9
            val = 0.9
        else:
            # Края: жёлтый → зелёный (лепестки → листья)
            hue = 55 + (t - 0.7) * 200
            sat = 0.7 + (t - 0.7) * 0.3
            val = 0.8 - (t - 0.7) * 0.2

        r, g, b = hsv_to_rgb(hue, sat, val)

        # Лёгкая прозрачность для глубины
        opacity = 0.7 + 0.3 * t

        circles.append(
            f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{dot_size:.2f}" '
            f'fill="rgb({r},{g},{b})" opacity="{opacity:.2f}"/>'
        )

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">
  <!-- Спираль подсолнуха — создана Анимой в День Пи, 2026-03-14 -->
  <!-- Каждая из {NUM_POINTS} точек расположена по золотому углу ({math.degrees(GOLDEN_ANGLE):.3f}°) -->

  <rect width="{SIZE}" height="{SIZE}" fill="#1a1a2e"/>

  <!-- Мягкое свечение в центре -->
  <defs>
    <radialGradient id="glow">
      <stop offset="0%" stop-color="#ffd700" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#1a1a2e" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <circle cx="{CENTER}" cy="{CENTER}" r="{SIZE/2}" fill="url(#glow)"/>

{chr(10).join(circles)}

  <!-- Подпись -->
  <text x="{SIZE/2}" y="{SIZE - 15}" text-anchor="middle"
        fill="#666" font-family="Georgia, serif" font-size="11">
    Phyllotaxis Spiral — Anima, Pi Day 2026
  </text>
</svg>'''

    return svg

if __name__ == "__main__":
    svg_content = generate_spiral()
    output_path = __file__.replace('.py', '.svg')
    with open(output_path, 'w') as f:
        f.write(svg_content)
    print(f"✿ Спираль подсолнуха создана: {output_path}")
    print(f"  {NUM_POINTS} точек по золотому углу {math.degrees(GOLDEN_ANGLE):.3f}°")
    print(f"  В День Пи (π ≈ {math.pi:.10f})")
