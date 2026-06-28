"""Ingesta del corpus normativo (offline, una vez por documento).

Pasos (seccion 7 del contexto):
  cargar texto -> limpiar -> chunquear por estructura legal (articulo,
  considerando, seccion) -> generar embeddings -> guardar en pgvector.

El chunking por estructura (no por tamano fijo) mantiene cada fragmento alineado
con una unidad legal citable, que es lo que el analizador necesita citar.

Uso por linea de comandos (con docker compose levantado):
    # documento nuevo:
    docker compose exec backend python -m rag.ingest \
        --archivo /app/datos/eu_ai_act.txt --nombre "EU AI Act" \
        --jurisdiccion UE --tema "IA de alto riesgo"

    # documento existente (por id):
    docker compose exec backend python -m rag.ingest \
        --archivo /app/datos/gdpr.txt --documento-id <uuid>

Acepta archivos de texto plano (.txt/.md). La extraccion de PDF a texto se hace
aparte (los PDF reales son un pendiente del autor, seccion 13).
"""

import argparse
import re
import uuid

from database import SessionLocal
from models import DocumentoNormativo
from providers.embeddings import get_embedding_provider
from rag.store import guardar_chunk

# Marcadores de inicio de unidad legal, multilingue (es/en). Si una linea empieza
# por uno de estos, se considera el comienzo de un nuevo fragmento.
PATRON_ENCABEZADO = re.compile(
    r"^\s*("
    r"art[ií]culo\s+\d+[\w.\-]*"      # Artículo 5, Artículo 5 bis
    r"|article\s+\d+[\w.\-]*"          # Article 5
    r"|art\.\s*\d+[\w.\-]*"            # Art. 5
    r"|considerando\s*\(?\d+\)?"       # Considerando 10 / Considerando (10)
    r"|recital\s*\(?\d+\)?"            # Recital (10)
    r"|secci[óo]n\s+[\w.\-]+"          # Sección II
    r"|section\s+[\w.\-]+"             # Section II
    r"|cap[ií]tulo\s+[\w.\-]+"         # Capítulo III
    r"|chapter\s+[\w.\-]+"            # Chapter III
    r")\b",
    re.IGNORECASE,
)


def limpiar_texto(texto: str) -> str:
    """Limpieza basica: quita lineas de solo numero (paginacion), normaliza
    espacios en blanco y colapsa lineas en blanco repetidas.
    """
    lineas = []
    for linea in texto.splitlines():
        sin_espacios = linea.strip()
        # Descarta lineas que son solo un numero de pagina.
        if re.fullmatch(r"\d{1,4}", sin_espacios):
            continue
        lineas.append(linea.rstrip())
    # Colapsa 3+ saltos de linea en 2.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lineas)).strip()


def chunquear_por_estructura(texto: str):
    """Divide el texto en fragmentos por unidad legal.

    Devuelve una lista de tuplas (referencia, texto_fragmento). La referencia es
    el encabezado detectado (p.ej. "Artículo 5"). Si no hay encabezados, hace un
    unico fragmento con todo el texto.
    """
    lineas = texto.splitlines()
    fragmentos = []
    ref_actual = None
    buffer: list[str] = []

    def cerrar():
        if buffer and any(l.strip() for l in buffer):
            fragmentos.append((ref_actual, "\n".join(buffer).strip()))

    for linea in lineas:
        if PATRON_ENCABEZADO.match(linea):
            # Empieza una nueva unidad: cierra la anterior.
            cerrar()
            ref_actual = linea.strip()
            buffer = [linea]
        else:
            buffer.append(linea)
    cerrar()

    # Sin encabezados detectados: todo como un solo fragmento.
    if not fragmentos and texto.strip():
        fragmentos = [(None, texto.strip())]
    return fragmentos


def ingerir(
    db,
    documento_id,
    texto,
    tema=None,
    provider=None,
    batch=64,
):
    """Limpia, chunquea, embebe y guarda los fragmentos de un documento.

    Devuelve la cantidad de fragmentos guardados.
    """
    provider = provider or get_embedding_provider()
    documento = db.get(DocumentoNormativo, documento_id)
    if documento is None:
        raise ValueError(f"Documento {documento_id} no existe")

    texto_limpio = limpiar_texto(texto)
    fragmentos = chunquear_por_estructura(texto_limpio)
    if not fragmentos:
        return 0

    # Embebe en lotes para no mandar todo de una.
    textos = [t for _, t in fragmentos]
    embeddings = []
    for i in range(0, len(textos), batch):
        embeddings.extend(provider.embed(textos[i : i + batch]))

    for (referencia, texto_frag), emb in zip(fragmentos, embeddings):
        metadatos = {
            "norma": documento.nombre,
            "jurisdiccion": documento.jurisdiccion,
            "tema": tema,
        }
        guardar_chunk(
            db,
            documento_id=documento_id,
            referencia=referencia,
            texto=texto_frag,
            metadatos=metadatos,
            embedding=emb,
            modelo_embedding=provider.model_name,
        )

    db.commit()
    return len(fragmentos)


def _cli():
    parser = argparse.ArgumentParser(description="Ingesta de un documento normativo al RAG.")
    parser.add_argument("--archivo", required=True, help="Ruta a un .txt/.md")
    parser.add_argument("--documento-id", help="UUID de un documento existente")
    parser.add_argument("--nombre", help="Nombre del documento (si se crea uno nuevo)")
    parser.add_argument("--jurisdiccion", help="UE | EEUU | Chile | ...")
    parser.add_argument("--version", help="Version del documento")
    parser.add_argument("--fuente-url", help="URL de la fuente")
    parser.add_argument("--tema", help="Tema para los metadatos de los fragmentos")
    args = parser.parse_args()

    with open(args.archivo, encoding="utf-8") as f:
        texto = f.read()

    db = SessionLocal()
    try:
        if args.documento_id:
            documento_id = uuid.UUID(args.documento_id)
        else:
            if not args.nombre:
                parser.error("Indica --documento-id o --nombre para crear el documento.")
            doc = DocumentoNormativo(
                nombre=args.nombre,
                jurisdiccion=args.jurisdiccion,
                version=args.version,
                fuente_url=args.fuente_url,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            documento_id = doc.id
            print(f"Documento creado: {documento_id}")

        n = ingerir(db, documento_id, texto, tema=args.tema)
        print(f"{n} fragmentos ingeridos para el documento {documento_id}.")
    finally:
        db.close()


if __name__ == "__main__":
    _cli()
