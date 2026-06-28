#!/usr/bin/env bash
# Convierte todos los PDF de backend/datos/ a .txt limpios, listos para ingerir.
# Se ejecuta DENTRO del contenedor del backend (que ya trae pdftotext):
#
#   docker compose exec backend bash convertir_pdf.sh
#
# Notas:
# - -nopgbrk quita los saltos de pagina; -enc UTF-8 conserva acentos y ñ.
# - Si un PDF es escaneado (imagenes), pdftotext saldra vacio: ese necesita OCR.
# - Revisa que los "Artículo N" queden al inicio de linea para un mejor chunking.
set -e

DIR="$(dirname "$0")/datos"
shopt -s nullglob

encontrados=0
for pdf in "$DIR"/*.pdf; do
    encontrados=1
    txt="${pdf%.pdf}.txt"
    echo "Convirtiendo: $(basename "$pdf") -> $(basename "$txt")"
    pdftotext -nopgbrk -enc UTF-8 "$pdf" "$txt"
    palabras=$(wc -w < "$txt")
    echo "   $palabras palabras"
    if [ "$palabras" -lt 50 ]; then
        echo "   ⚠ Muy pocas palabras: ¿PDF escaneado? Podria necesitar OCR."
    fi
done

if [ "$encontrados" -eq 0 ]; then
    echo "No se encontraron PDF en $DIR"
fi
echo "Listo."
