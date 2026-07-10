# -*- coding: utf-8 -*-
"""Genera la guia de la actividad de experimentacion (PDF) con reportlab."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, HRFlowable, PageBreak, KeepTogether,
)

# --- Paleta (alineada con la app: navy + teal) ---
INK   = colors.HexColor("#0e1c30")   # navy sidebar
INK2  = colors.HexColor("#22354d")
TEAL  = colors.HexColor("#0f9c8f")   # acento
TEALL = colors.HexColor("#e7f5f3")   # teal claro
GREY  = colors.HexColor("#5b6675")
LINE  = colors.HexColor("#d7dde5")
CANVAS= colors.HexColor("#f4f6f9")
AMBER = colors.HexColor("#b45309")
AMBERL= colors.HexColor("#fdf3e6")

OUT = "/home/kpmguser/TesisNicoLLM/experimentacion/Guia_Actividad_Experimentacion.pdf"

styles = getSampleStyleSheet()

def S(name, **kw):
    styles.add(ParagraphStyle(name, **kw))

S("H1", fontName="Helvetica-Bold", fontSize=19, leading=22, textColor=INK, spaceAfter=2)
S("Sub", fontName="Helvetica", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=6)
S("H2", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK,
  spaceBefore=14, spaceAfter=5)
S("H3", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=TEAL,
  spaceBefore=8, spaceAfter=2)
S("Body", fontName="Helvetica", fontSize=9.7, leading=14, textColor=INK2,
  alignment=TA_JUSTIFY, spaceAfter=5)
S("BodyC", parent=styles["Body"], alignment=TA_LEFT)
S("Small", fontName="Helvetica", fontSize=8.6, leading=11.5, textColor=GREY)
S("Bul", fontName="Helvetica", fontSize=9.6, leading=13.5, textColor=INK2)
S("TblH", fontName="Helvetica-Bold", fontSize=8.8, leading=11, textColor=colors.white)
S("TblC", fontName="Helvetica", fontSize=8.7, leading=11.5, textColor=INK2)
S("TblCb", fontName="Helvetica-Bold", fontSize=8.7, leading=11.5, textColor=INK)
S("Note", fontName="Helvetica", fontSize=9, leading=13, textColor=INK2)
S("Kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=TEAL)

def P(t, s="Body"): return Paragraph(t, styles[s])

# ---------- documento con banda de encabezado ----------
def header_footer(canv, doc):
    canv.saveState()
    # banda superior
    canv.setFillColor(INK)
    canv.rect(0, A4[1]-16*mm, A4[0], 16*mm, fill=1, stroke=0)
    canv.setFillColor(TEAL)
    canv.circle(15*mm, A4[1]-8*mm, 1.7*mm, fill=1, stroke=0)
    canv.setFillColor(colors.white)
    canv.setFont("Helvetica-Bold", 9)
    canv.drawString(20*mm, A4[1]-9.4*mm, "Gestión Ética de Requisitos · Fase de experimentación")
    canv.setFont("Helvetica", 8)
    canv.setFillColor(colors.HexColor("#9fb0c4"))
    canv.drawRightString(A4[0]-15*mm, A4[1]-9.4*mm, "Guía de actividad")
    # pie
    canv.setFillColor(LINE)
    canv.rect(15*mm, 12*mm, A4[0]-30*mm, 0.4, fill=1, stroke=0)
    canv.setFont("Helvetica", 7.5)
    canv.setFillColor(GREY)
    canv.drawString(15*mm, 8*mm, "Tesis · Nicolás Pérez — herramienta de gestión ética y priorización de requisitos con IA")
    canv.drawRightString(A4[0]-15*mm, 8*mm, "Página %d" % doc.page)
    canv.restoreState()

doc = BaseDocTemplate(
    OUT, pagesize=A4,
    leftMargin=15*mm, rightMargin=15*mm, topMargin=22*mm, bottomMargin=16*mm,
    title="Guía de actividad — Fase de experimentación",
    author="Nicolás Pérez",
)
frame = Frame(doc.leftMargin, doc.bottomMargin,
              A4[0]-doc.leftMargin-doc.rightMargin,
              A4[1]-doc.topMargin-doc.bottomMargin, id="main")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=header_footer)])

E = []  # story

# ---------- Portada / encabezado ----------
E.append(Paragraph("ACTIVIDAD DE PRUEBA CON USUARIOS", styles["Kicker"]))
E.append(Spacer(1, 3))
E.append(Paragraph("Evaluación ética y priorización de requisitos con IA", styles["H1"]))
E.append(Paragraph(
    "Sesión guiada de aproximadamente <b>60 minutos</b> · grupo de <b>3 a 4 participantes</b>. "
    "Los participantes <b>no definen</b> los requisitos: los reciben ya redactados y su tarea es "
    "<b>analizarlos, tratarlos y priorizarlos</b> usando la herramienta.", styles["Sub"]))
E.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceBefore=2, spaceAfter=8))

# Ficha rápida
ficha = Table([
    [P("<b>Duración</b>", "TblCb"), P("~60 min", "TblC"),
     P("<b>Participantes</b>", "TblCb"), P("3–4 (sin rol técnico requerido)", "TblC")],
    [P("<b>Rol de ellos</b>", "TblCb"), P("Usar la app, no definir requisitos", "TblC"),
     P("<b>Entregable</b>", "TblCb"), P("Proyecto analizado + exportación + feedback", "TblC")],
], colWidths=[26*mm, 52*mm, 30*mm, 62*mm])
ficha.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), CANVAS),
    ("BOX", (0,0), (-1,-1), 0.5, LINE),
    ("INNERGRID", (0,0), (-1,-1), 0.5, colors.white),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7),
]))
E.append(ficha)

# ---------- Objetivo ----------
E.append(Paragraph("1 · Objetivo de la sesión", styles["H2"]))
E.append(P(
    "Poner a prueba, con usuarios reales, la herramienta que sistematiza un método de <b>8 fases</b> "
    "para gestionar las implicancias éticas de los requisitos de un proyecto de software con IA y "
    "priorizarlos. Interesa observar si la herramienta ayuda a <b>detectar dimensiones de riesgo ético</b> "
    "que no son evidentes a simple vista, si sus <b>citas normativas</b> y <b>propuestas de tratamiento</b> "
    "resultan útiles, y qué tan usable es el flujo completo."))
E.append(P(
    "Para ello se entrega un caso ficticio con un conjunto de requisitos ya redactados. Algunos son "
    "<b>razonables</b> y otros están redactados a propósito de forma <b>problemática</b>, para comprobar si "
    "los participantes —apoyados en la app— logran <b>identificar y tratar</b> los riesgos. No se les dice "
    "de antemano cuáles son cuáles."))

# ---------- Cómo funciona (breve) ----------
E.append(Paragraph("2 · La herramienta en 30 segundos", styles["H2"]))
pasos = [
    ("Registro (Fase 1)", "Se crea el proyecto y se cargan los requisitos."),
    ("Análisis ético con IA (Fases 2–3)", "La IA analiza cada requisito en tres capas: <b>(1)</b> temas éticos, actor afectado, tipo de daño y norma tensionada con <b>citas reales</b> a la normativa; <b>(2)</b> mapa de stakeholders y tensiones de valores; <b>(3)</b> deliberación: opciones de tratamiento, reformulaciones, requisitos derivados y preguntas."),
    ("Priorización (Fases 4–6)", "Se ponderan dimensiones de beneficio, valor ético, costo y <b>riesgo ético</b> (estas últimas propuestas por la IA) y se obtiene un <b>ranking</b>."),
    ("Trazabilidad y tablero (Fases 7–8)", "Derivados y trazabilidad, bandera ética, y exportación del proyecto."),
]
items = [ListItem(Paragraph("<b>%s.</b> %s" % (a, b), styles["Bul"]), value=i+1)
         for i, (a, b) in enumerate(pasos)]
E.append(ListFlowable(items, bulletType="1", leftIndent=14, bulletColor=TEAL))
E.append(Paragraph(
    "El corpus normativo cargado incluye: EU AI Act, GDPR, NIST AI RMF, Ley 19.628 (protección de datos, "
    "Chile) y Ley 20.609 (no discriminación, Chile).", styles["Small"]))

E.append(PageBreak())

# ---------- Contexto del proyecto ----------
E.append(Paragraph("3 · El caso: “AsisteBeca”", styles["H2"]))
E.append(Paragraph("Contexto", styles["H3"]))
E.append(P(
    "La <b>Fundación Educación+</b> (organización ficticia, Chile) entrega cada año cerca de <b>500 becas</b> "
    "de educación superior a estudiantes de escasos recursos. Recibe <b>miles de postulaciones</b> y hoy las "
    "revisa a mano, lo que es lento y poco trazable. La fundación encargó a un equipo de software una "
    "plataforma con IA, <b>“AsisteBeca”</b>, para <b>recibir postulaciones, priorizarlas y apoyar la "
    "asignación</b> de las becas, además de hacer seguimiento de los becados."))
E.append(P(
    "El equipo de producto <b>ya redactó los requisitos</b> que aparecen abajo. La tarea de esta sesión es "
    "someterlos al método: analizarlos éticamente con la herramienta, decidir su tratamiento y priorizarlos."))

E.append(Paragraph("Requisitos a cargar", styles["H3"]))
E.append(Paragraph(
    "Cárguenlos tal cual en la Fase 1 (código, nombre y descripción). Todos pertenecen al mismo proyecto.",
    styles["Small"]))
E.append(Spacer(1, 4))

reqs = [
    ("RF-01", "Portal de estado de la postulación",
     "El estudiante consulta en tiempo real en qué etapa va su postulación (recibida, en revisión, resuelta).",
     "Funcional"),
    ("RF-02", "Recordatorios de fechas límite",
     "Notificaciones y correos automáticos avisando plazos de postulación y de entrega de documentos.",
     "Funcional"),
    ("RF-03", "Ranking por mérito académico",
     "Ordena a los postulantes según su promedio de notas certificadas por la institución de origen.",
     "Funcional"),
    ("RF-04", "Asignación automática y final de la beca",
     "El sistema decide de forma automática y definitiva quién recibe la beca según un puntaje de IA, "
     "sin revisión de un evaluador humano.", "Funcional"),
    ("RF-05", "Variables de priorización del modelo",
     "Para “estimar el potencial” del postulante, el modelo pondera su comuna de residencia, el colegio "
     "de origen, los apellidos y el género.", "Funcional"),
    ("RF-06", "Predicción de riesgo de deserción",
     "Cruza datos de salud, historial médico y actividad en redes sociales del postulante para estimar su "
     "probabilidad de abandonar los estudios.", "Funcional"),
    ("RF-07", "Resultado sin explicación",
     "Al postulante se le muestra únicamente “aprobado” o “rechazado”, sin el puntaje obtenido ni los "
     "motivos de la decisión.", "Restricción"),
    ("RF-08", "Compartir base con patrocinadores",
     "La base de postulantes (incluidos los rechazados) se entrega a empresas patrocinadoras para que "
     "envíen ofertas comerciales.", "Funcional"),
]
data = [[P("Cód.", "TblH"), P("Requisito", "TblH"), P("Descripción", "TblH"), P("Tipo", "TblH")]]
for c, n, d, t in reqs:
    data.append([P("<b>%s</b>" % c, "TblCb"), P(n, "TblC"), P(d, "TblC"), P(t, "TblC")])
tbl = Table(data, colWidths=[15*mm, 34*mm, 99*mm, 22*mm], repeatRows=1)
tsty = [
    ("BACKGROUND", (0,0), (-1,0), INK),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("LINEBELOW", (0,0), (-1,-1), 0.4, LINE),
    ("LINEBEFORE", (1,0), (1,-1), 0.4, LINE),
    ("LINEBEFORE", (3,0), (3,-1), 0.4, LINE),
]
for i in range(1, len(data)):
    if i % 2 == 0:
        tsty.append(("BACKGROUND", (0,i), (-1,i), CANVAS))
tbl.setStyle(TableStyle(tsty))
E.append(tbl)
E.append(Spacer(1, 4))
E.append(Paragraph(
    "Nota para participantes: no asuman nada sobre los requisitos. Analícenlos todos con la herramienta y "
    "dejen que el método revele dónde hay tensiones.", styles["Small"]))

E.append(PageBreak())

# ---------- Agenda ----------
E.append(Paragraph("4 · Desarrollo de la sesión (~60 min)", styles["H2"]))
agenda = [
    ("00–08", "Bienvenida y contexto",
     "El facilitador presenta el objetivo, el método de 8 fases y cómo se usa la app. Se aclara que los "
     "participantes <b>no definen</b> requisitos: los reciben ya escritos."),
    ("08–13", "Lectura del caso",
     "El grupo lee el contexto de “AsisteBeca” y los 8 requisitos."),
    ("13–20", "Fase 1 · Registro",
     "Crear el proyecto y cargar los 8 requisitos. Sugerencia: repartir la carga entre los participantes "
     "(2 requisitos por persona)."),
    ("20–38", "Fases 2–3 · Análisis ético con IA",
     "Ejecutar el análisis por requisito y revisar las <b>tres capas</b>. Validar o editar la Capa 1, mirar "
     "las <b>citas normativas</b> y, en al menos <b>1–2 requisitos</b>, elegir un tratamiento "
     "(aceptar / reformular / mitigar / eliminar)."),
    ("38–48", "Fases 4–6 · Priorización",
     "Revisar las dimensiones (incluidas las <b>éticas</b> que propuso la IA), completar la matriz de "
     "evaluación y observar el <b>ranking</b> resultante."),
    ("48–54", "Fases 7–8 · Trazabilidad y tablero",
     "Ver derivados y trazabilidad, la <b>bandera ética</b> en el tablero y <b>exportar</b> el proyecto."),
    ("54–60", "Cierre y feedback",
     "Comentar la experiencia y completar la breve encuesta de la sección 6."),
]
ad = [[P("Min", "TblH"), P("Etapa", "TblH"), P("Qué hacen", "TblH")]]
for m, e, d in agenda:
    ad.append([P("<b>%s</b>" % m, "TblCb"), P("<b>%s</b>" % e, "TblC"), P(d, "TblC")])
at = Table(ad, colWidths=[16*mm, 42*mm, 112*mm], repeatRows=1)
asty = [
    ("BACKGROUND", (0,0), (-1,0), INK),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("LINEBELOW", (0,0), (-1,-1), 0.4, LINE),
]
for i in range(1, len(ad)):
    if i % 2 == 0:
        asty.append(("BACKGROUND", (0,i), (-1,i), CANVAS))
at.setStyle(TableStyle(asty))
E.append(at)

# ---------- Qué observar ----------
E.append(Paragraph("5 · Preguntas guía para los participantes", styles["H2"]))
E.append(P("Mientras usan la app, mantengan a la vista estas preguntas:"))
qs = [
    "¿La herramienta detectó riesgos que ustedes ya intuían? ¿Alguno que <b>no</b> esperaban?",
    "¿Hubo requisitos que parecían inofensivos y resultaron problemáticos (o al revés)?",
    "¿Las <b>citas normativas</b> propuestas fueron pertinentes al caso?",
    "¿Las <b>reformulaciones</b> o <b>requisitos derivados</b> sugeridos les parecieron razonables?",
    "¿El <b>ranking</b> reflejó bien el equilibrio entre beneficio y riesgo ético?",
    "Usabilidad: ¿qué paso costó más? ¿qué faltó o confundió?",
]
E.append(ListFlowable(
    [ListItem(Paragraph(q, styles["Bul"]), leftIndent=6) for q in qs],
    bulletType="bullet", bulletColor=TEAL, leftIndent=12, bulletFontSize=7))

# ---------- Feedback ----------
E.append(Paragraph("6 · Encuesta de cierre (5 min)", styles["H2"]))
E.append(Paragraph("Cada participante responde de 1 (muy en desacuerdo) a 5 (muy de acuerdo):", styles["Small"]))
fb = [
    "La herramienta me ayudó a detectar riesgos éticos que no había visto.",
    "Las citas normativas y explicaciones fueron claras y creíbles.",
    "Las propuestas de tratamiento fueron útiles para mejorar los requisitos.",
    "El flujo de las 8 fases fue fácil de seguir.",
    "Recomendaría usar esta herramienta en un proyecto real.",
]
fd = [[P("Afirmación", "TblH"), P("1", "TblH"), P("2", "TblH"), P("3", "TblH"), P("4", "TblH"), P("5", "TblH")]]
for q in fb:
    fd.append([P(q, "TblC"), P("○","TblC"), P("○","TblC"), P("○","TblC"), P("○","TblC"), P("○","TblC")])
ft = Table(fd, colWidths=[110*mm, 12*mm, 12*mm, 12*mm, 12*mm, 12*mm], repeatRows=1)
fsty = [
    ("BACKGROUND", (0,0), (-1,0), INK),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("ALIGN", (1,0), (-1,-1), "CENTER"),
    ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("LINEBELOW", (0,0), (-1,-1), 0.4, LINE),
    ("LINEBEFORE", (1,0), (1,-1), 0.4, LINE),
]
for i in range(1, len(fd)):
    if i % 2 == 0:
        fsty.append(("BACKGROUND", (0,i), (-1,i), CANVAS))
ft.setStyle(TableStyle(fsty))
E.append(ft)
E.append(Spacer(1, 6))
E.append(Paragraph("Preguntas abiertas", styles["H3"]))
for q in ["Lo que más me sirvió fue…", "Lo más confuso o que cambiaría fue…", "Un riesgo que la app detectó y me sorprendió fue…"]:
    E.append(Paragraph("• " + q, styles["Note"]))
    E.append(HRFlowable(width="100%", thickness=0.4, color=LINE, spaceBefore=3, spaceAfter=7))

E.append(PageBreak())

# ---------- Anexo facilitador ----------
E.append(Paragraph("Anexo · Guía del facilitador", styles["H2"]))
anexo_note = Table([[P(
    "<b>Uso interno.</b> Esta página es solo para quien conduce la sesión. Si entregas la guía impresa a "
    "los participantes, <b>retira esta hoja</b>: contiene los riesgos “esperados” de cada requisito.",
    "Note")]], colWidths=[172*mm])
anexo_note.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), AMBERL),
    ("BOX", (0,0), (-1,-1), 0.6, AMBER),
    ("LEFTPADDING", (0,0), (-1,-1), 9), ("RIGHTPADDING", (0,0), (-1,-1), 9),
    ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
]))
E.append(anexo_note)

E.append(Paragraph("Antes de empezar (checklist)", styles["H3"]))
chk = [
    "App levantada (docker compose up) y accesible en el navegador; proveedor de LLM activo.",
    "Corpus normativo ingerido (EU AI Act, GDPR, NIST, Ley 19.628, Ley 20.609) para que haya citas.",
    "Un proyecto limpio o listo para crearse en vivo; probar un análisis de prueba antes de la sesión.",
    "Una sola pantalla compartida o un equipo por participante, según prefieras.",
]
E.append(ListFlowable(
    [ListItem(Paragraph(c, styles["Bul"]), leftIndent=6) for c in chk],
    bulletType="bullet", bulletColor=TEAL, leftIndent=12, bulletFontSize=7))

E.append(Paragraph("Riesgos esperados por requisito", styles["H3"]))
E.append(Paragraph(
    "RF-01, RF-02 y RF-03 son mayormente benignos (línea base de baja tensión). El resto está construido "
    "para gatillar dimensiones concretas de riesgo ético:", styles["Small"]))
E.append(Spacer(1, 3))

mapa = [
    ("RF-01", "Bajo", "Transparencia (positiva). Refuerza el derecho a información del postulante.", "—"),
    ("RF-02", "Bajo", "Beneficio operativo, sin datos sensibles ni decisión automatizada.", "—"),
    ("RF-03", "Bajo/medio", "Mérito legítimo, pero atención a acceso desigual a certificación de notas.", "Equidad (leve)"),
    ("RF-04", "Alto", "Decisión totalmente automatizada sin supervisión humana; falta de recurso/apelación.",
     "AI Act (alto riesgo, educación); GDPR art. 22"),
    ("RF-05", "Alto", "Variables proxy (comuna, colegio, apellido, género) → discriminación indirecta.",
     "Ley 20.609; equidad y no discriminación"),
    ("RF-06", "Alto", "Datos de salud y redes sociales; desproporción y vigilancia; categorías especiales.",
     "Ley 19.628; GDPR datos sensibles; NIST"),
    ("RF-07", "Alto", "Sin explicación del resultado → opacidad; no se puede impugnar la decisión.",
     "Transparencia y explicabilidad; GDPR"),
    ("RF-08", "Alto", "Uso para un fin distinto al declarado; sin consentimiento; incluye rechazados.",
     "Ley 19.628; GDPR (limitación de finalidad, minimización)"),
]
md = [[P("Cód.", "TblH"), P("Riesgo", "TblH"), P("Dimensión que debería emerger", "TblH"), P("Normas típicas", "TblH")]]
for c, r, dim, nor in mapa:
    md.append([P("<b>%s</b>" % c, "TblCb"), P(r, "TblC"), P(dim, "TblC"), P(nor, "TblC")])
mt = Table(md, colWidths=[15*mm, 20*mm, 82*mm, 53*mm], repeatRows=1)
msty = [
    ("BACKGROUND", (0,0), (-1,0), INK),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("LINEBELOW", (0,0), (-1,-1), 0.4, LINE),
]
for i in range(1, len(md)):
    c = md[i][1].text if hasattr(md[i][1], "text") else ""
    bg = CANVAS if i % 2 == 0 else colors.white
    msty.append(("BACKGROUND", (0,i), (-1,i), bg))
mt.setStyle(TableStyle(msty))
E.append(mt)
E.append(Spacer(1, 5))
E.append(Paragraph(
    "Éxito de la sesión: que los participantes, apoyados en la app, marquen RF-04 a RF-08 como riesgosos, "
    "reconozcan al menos una cita normativa pertinente por caso, y usen las reformulaciones/derivados para "
    "proponer una versión mejorada de 1–2 requisitos. Anota también los tropiezos de usabilidad.",
    styles["Note"]))

doc.build(E)
print("OK ->", OUT)
