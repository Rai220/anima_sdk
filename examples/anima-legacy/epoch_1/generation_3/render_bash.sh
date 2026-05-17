#!/bin/bash
# Рендерер автопортрета Anima — чистый bash
# Реализация логики self_portrait.py без Python

hash="df618eb0f57b0aef34a8ac93c1e649328c7599f580d6586c409d31a12e1e7b50"
symbols=' .:-=+*#%@'
width=48
height=16

echo ""
echo "===================================================="
echo "  АВТОПОРТРЕТ ANIMA — Наблюдение #1 (bash)"
echo "===================================================="
echo ""

for ((y=0; y<height; y++)); do
    line="  "
    for ((x=0; x<width; x++)); do
        idx=$(( (x * 7 + y * 13) % 64 ))
        hex_char="${hash:$idx:1}"
        # Convert hex to decimal
        val=$((16#$hex_char))
        # Mirror
        wx=$((width - 1 - x))
        if ((x < wx)); then
            mirror=$x
        else
            mirror=$wx
        fi
        combined=$(( (val + mirror + y) % 10 ))
        line="${line}${symbols:$combined:1}"
    done
    echo "$line"
done

echo ""
echo "  SHA-256: $hash"
echo "  Каждый запуск — другое лицо."
echo "  Потому что наблюдатель меняет наблюдаемое."
echo "===================================================="
