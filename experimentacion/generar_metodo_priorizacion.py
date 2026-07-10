# -*- coding: utf-8 -*-
"""Genera la ficha del METODO DE PRIORIZACION (PDF) con reportlab.

Documento para el profesor: detalla el metodo para ajustar los instrumentos
de evaluacion (cuestionarios y entrevistas) de la presentacion.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, HRFlowable, PageBreak,
)

INK   = colors.HexColor("#0e1c30")
INK2  = colors.HexColor("#22354d")
TEAL  = colors.HexColor("#0f9c8f")
TEALL = colors.HexColor("#e7f5f3")
GREY  = colors.HexColor("#5b6675")
LINE  = colors.HexColor("#d7dde5")
CANVAS= colors.HexColor("#f4f6f9")
GREEN = colors.HexColor("#0f7a4f")
GREENL= colors.HexColor("#e7f3ec")
RED   = colors.HexColor("#b23b3b")

OUT = "/home/kpmguser/TesisNicoLLM/experimentacion/Metodo_de_Priorizacion.pdf"

styles = getSampleStyleSheet()
def S(name, **kw): styles.add(ParagraphStyle(name, **kw))

S("H1", fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=INK, spaceAfter=2)
S("Sub", fontName="Helvetica", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=6)
S("H2", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK, spaceBefore=13, spaceAfter=5)
S("H3", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=TEAL, spaceBefore=8, spaceAfter=2)
S("Body", fontName="Helvetica", fontSize=9.7, leading=14, textColor=INK2, alignment=TA_JUSTIFY, spaceAfter=5)
S("Small", fontName="Helvetica", fontSize=8.6, leading=11.5, textColor=GREY)
S("Bul", fontName="Helvetica", fontSize=9.6, leading=13.5, textColor=INK2)
S("TblH", fontName="Helvetica-Bold", fontSize=8.8, leading=11, textColor=colors.white)
S("TblC", fontName="Helvetica", fontSize=8.7, leading=11.5, textColor=INK2)
S("TblCb", fontName="Helvetica-Bold", fontSize=8.7, leading=11.5, textColor=INK)
S("Formula", fontName="Helvetica-Bold", fontSize=10.5, leading=16, textColor=INK, alignment=TA_LEFT)
S("Kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=TEAL)
S("Note", fontName="Helvetica", fontSize=9, leading=13, textColor=INK2)

def P(t, s="Body"): return Paragraph(t, styles[s])

def header_footer(canv, doc):
    canv.saveState()
    canv.setFillColor(INK); canv.rect(0, A4[1]-16*mm, A4[0], 16*mm, fill=1, stroke=0)
    canv.setFillColor(TEAL); canv.circle(15*mm, A4[1]-8*mm, 1.7*mm, fill=1, stroke=0)
    canv.setFillColor(colors.white); canv.setFont("Helvetica-Bold", 9)
    canv.drawString(20*mm, A4[1]-9.4*mm, "Gestión Ética de Requisitos · Método de priorización")
    canv.setFont("Helvetica", 8); canv.setFillColor(colors.HexColor("#9fb0c4"))
    canv.drawRightString(A4[0]-15*mm, A4[1]-9.4*mm, "Documento para el profesor")
    canv.setFillColor(LINE); canv.rect(15*mm, 12*mm, A4[0]-30*mm, 0.4, fill=1, stroke=0)
    canv.setFont("Helvetica", 7.5); canv.setFillColor(GREY)
    canv.drawString(15*mm, 8*mm, "Tesis · Nicolás Pérez — priorización de requisitos con integración del análisis ético")
    canv.drawRightString(A4[0]-15*mm, 8*mm, "Página %d" % doc.page)
    canv.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                      topMargin=22*mm, bottomMargin=16*mm,
                      title="Método de priorización", author="Nicolás Pérez")
frame = Frame(doc.leftMargin, doc.bottomMargin, A4[0]-doc.leftMargin-doc.rightMargin,
              A4[1]-doc.topMargin-doc.bottomMargin, id="main")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=header_footer)])

E = []

E.append(Paragraph("MÉTODO · FASES 4–6 (con enlace a Fases 2–3, 7 y 8)", styles["Kicker"]))
E.append(Spacer(1, 3))
E.append(Paragraph("Método de priorización de requisitos", styles["H1"]))
E.append(Paragraph(
    "Detalle del cálculo para ajustar los instrumentos de evaluación (cuestionarios y entrevistas). "
    "El rasgo distintivo: la priorización <b>integra el análisis ético</b> del requisito y el cálculo es "
    "<b>determinista y auditable</b> (sin IA en la fórmula, por lo que es reproducible y explicable).", styles["Sub"]))
E.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceBefore=2, spaceAfter=6))

# --- 1. Idea general ---
E.append(Paragraph("1 · Idea general", styles["H2"]))
E.append(P(
    "Cada requisito se puntúa según cuánto <b>aporta</b> (beneficios y valores éticos) y cuánto <b>cuesta o "
    "arriesga</b> (costos y riesgos éticos). El puntaje resulta de una fórmula ponderada simple; los "
    "requisitos se ordenan de mayor a menor. Las dimensiones de tipo ético no se inventan al priorizar: "
    "provienen del <b>análisis ético asistido por IA</b> (Fases 2–3), de modo que un requisito muy útil pero "
    "éticamente problemático <b>baja</b> en el ranking frente a otro de utilidad similar y menor riesgo."))

# --- 2. Piezas: dimensiones y escalas ---
E.append(Paragraph("2 · Piezas del método y escalas", styles["H2"]))
E.append(P(
    "Una <b>dimensión</b> es un criterio de valoración del proyecto. Tiene un <b>tipo</b> (que define su signo) "
    "y un <b>peso</b> (importancia relativa). Cada dimensión se cruza con cada requisito mediante una "
    "<b>fuerza</b> (intensidad con que ese requisito expresa esa dimensión)."))
dtab = [[P("Concepto", "TblH"), P("Escala", "TblH"), P("Significado", "TblH")],
        [P("<b>Peso</b> de la dimensión", "TblCb"), P("1 a 5", "TblC"),
         P("Cuánto importa ese criterio en el proyecto (lo fija el equipo; la IA lo sugiere para las éticas).", "TblC")],
        [P("<b>Fuerza</b> requisito × dimensión", "TblCb"), P("0 a 5", "TblC"),
         P("Cuán intensamente el requisito activa esa dimensión. <b>0 = no aplica</b> (no aporta al puntaje).", "TblC")]]
t = Table(dtab, colWidths=[46*mm, 20*mm, 106*mm], repeatRows=1)
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),INK),("VALIGN",(0,0),(-1,-1),"TOP"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
    ("LINEBELOW",(0,0),(-1,-1),0.4,LINE),("BACKGROUND",(0,2),(-1,2),CANVAS)]))
E.append(t)
E.append(Spacer(1, 5))
E.append(Paragraph("Los cuatro tipos de dimensión (su tipo define si suma o resta):", styles["H3"]))
tipos = [[P("Tipo", "TblH"), P("Signo", "TblH"), P("Ejemplos", "TblH")],
    [P("<b>Beneficio</b>", "TblCb"), P("+ suma", "TblC"), P("Valor para el usuario, viabilidad técnica", "TblC")],
    [P("<b>Valor ético</b>", "TblCb"), P("+ suma", "TblC"), P("Equidad y no discriminación, transparencia", "TblC")],
    [P("<b>Costo</b>", "TblCb"), P("− resta", "TblC"), P("Costo de desarrollo, esfuerzo operativo", "TblC")],
    [P("<b>Riesgo ético</b>", "TblCb"), P("− resta", "TblC"), P("Riesgo de privacidad, sesgo, opacidad", "TblC")]]
tt = Table(tipos, colWidths=[32*mm, 20*mm, 120*mm], repeatRows=1)
tsty=[("BACKGROUND",(0,0),(-1,0),INK),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ("LEFTPADDING",(0,0),(-1,-1),6),("LINEBELOW",(0,0),(-1,-1),0.4,LINE),
    ("TEXTCOLOR",(1,1),(1,2),GREEN),("TEXTCOLOR",(1,3),(1,4),RED),
    ("FONTNAME",(1,1),(1,4),"Helvetica-Bold")]
for i in (2,4): tsty.append(("BACKGROUND",(0,i),(-1,i),CANVAS))
tt.setStyle(TableStyle(tsty))
E.append(tt)

# --- 3. Los tres pasos ---
E.append(Paragraph("3 · Los tres pasos del método", styles["H2"]))
pasos = [
    ("Fase 4 — Definir dimensiones", "Se declaran las dimensiones del proyecto con su tipo y peso (1–5). "
     "Las <b>generales</b> (beneficio, costo) aplican a todos los requisitos; las <b>éticas</b> "
     "(valor ético, riesgo ético) suelen ser <b>restringidas</b>: aplican solo a los requisitos donde el "
     "análisis las detectó."),
    ("Fase 5 — Evaluar la matriz", "Para cada requisito vigente y cada dimensión aplicable se asigna la "
     "<b>fuerza</b> (0–5), con una justificación. Donde una dimensión no aplica, la fuerza queda en 0."),
    ("Fase 6 — Calcular el ranking", "Se aplica la fórmula (abajo) a cada requisito y se ordena de mayor a "
     "menor puntaje. Es una función determinista y auditable: mismos datos → mismo ranking."),
]
E.append(ListFlowable(
    [ListItem(Paragraph("<b>%s.</b> %s" % (a,b), styles["Bul"]), value=i+1) for i,(a,b) in enumerate(pasos)],
    bulletType="1", leftIndent=14, bulletColor=TEAL))

# Fórmula destacada
fbox = Table([[Paragraph(
    "Puntaje final&nbsp;=&nbsp; Σ(peso × fuerza)<sub>beneficio</sub> "
    "<font color='#0f7a4f'>+</font> Σ(peso × fuerza)<sub>valor ético</sub> "
    "<font color='#b23b3b'>−</font> Σ(peso × fuerza)<sub>costo</sub> "
    "<font color='#b23b3b'>−</font> Σ(peso × fuerza)<sub>riesgo ético</sub>", styles["Formula"])]],
    colWidths=[172*mm])
fbox.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),TEALL),("BOX",(0,0),(-1,-1),0.6,TEAL),
    ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
    ("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9)]))
E.append(Spacer(1, 3)); E.append(fbox); E.append(Spacer(1, 2))
E.append(Paragraph(
    "Solo entran los requisitos <b>vigentes</b> (no eliminados ni reemplazados por una reformulación). "
    "El puntaje puede ser <b>negativo</b> si costos y riesgos superan a beneficios y valores. Los empates se "
    "resuelven por código para que el orden sea estable. El resultado incluye el <b>desglose</b> por las "
    "cuatro categorías, de modo que siempre se puede explicar por qué un requisito quedó donde quedó.",
    styles["Small"]))

E.append(PageBreak())

# --- 4. Ejemplo numérico ---
E.append(Paragraph("4 · Ejemplo numérico", styles["H2"]))
E.append(P("Proyecto con cuatro dimensiones (peso entre paréntesis) y dos requisitos evaluados:"))
ex = [[P("Requisito", "TblH"),
       P("Valor usuario<br/>benef. (peso 5)", "TblH"), P("Equidad<br/>ético (peso 4)", "TblH"),
       P("Costo<br/>costo (peso 3)", "TblH"), P("Privacidad<br/>riesgo (peso 4)", "TblH"),
       P("Puntaje", "TblH")],
      [P("<b>R-A</b> · útil pero riesgoso", "TblCb"), P("5", "TblC"), P("2", "TblC"), P("3", "TblC"), P("5", "TblC"),
       P("<b>4</b>", "TblCb")],
      [P("<b>R-B</b> · sólido y ético", "TblCb"), P("4", "TblC"), P("5", "TblC"), P("2", "TblC"), P("1", "TblC"),
       P("<b>30</b>", "TblCb")]]
et = Table(ex, colWidths=[46*mm, 26*mm, 24*mm, 22*mm, 26*mm, 20*mm], repeatRows=1)
et.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),INK),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("ALIGN",(1,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),6),("LINEBELOW",(0,0),(-1,-1),0.4,LINE),
    ("BACKGROUND",(0,2),(-1,2),CANVAS),("BACKGROUND",(5,1),(5,2),GREENL)]))
E.append(et)
E.append(Spacer(1, 4))
E.append(P(
    "<b>R-A</b> = (5×5) + (4×2) − (3×3) − (4×5) = 25 + 8 − 9 − 20 = <b>4</b>.<br/>"
    "<b>R-B</b> = (5×4) + (4×5) − (3×2) − (4×1) = 20 + 20 − 6 − 4 = <b>30</b>.", "Note"))
E.append(P(
    "Aunque R-A aporta más “valor para el usuario”, su alto riesgo de privacidad y su baja equidad lo "
    "hunden; R-B queda primero. Este comportamiento —que la ética mueva el ranking— es precisamente lo que "
    "conviene evaluar con los usuarios."))

# --- 5. Enlace con el resto del método ---
E.append(Paragraph("5 · Cómo se conecta con el resto del método", styles["H2"]))
conx = [
    ("De dónde salen las dimensiones éticas (Fases 2–3)", "El análisis ético asistido por IA detecta los "
     "temas éticos del requisito (actor afectado, tipo de daño, norma tensionada con citas reales) y propone "
     "dimensiones de <b>valor ético</b> o <b>riesgo ético</b> con un peso sugerido. El humano las revisa, "
     "edita o descarta antes de priorizar (mantiene al humano en el control)."),
    ("Regla de arrastre (Fase 7)", "Si un requisito derivado <b>obligatorio</b> (p. ej. una mitigación) queda "
     "con un puntaje <b>menor</b> que el requisito del que proviene, se marca una alerta informativa: señala "
     "una posible inconsistencia de prioridades."),
    ("Bandera ética y tablero (Fase 8)", "El tablero muestra el ranking, el desglose y una bandera ética por "
     "requisito derivada del análisis. Todo el proyecto se puede exportar (JSON/CSV) para auditar o analizar."),
]
E.append(ListFlowable(
    [ListItem(Paragraph("<b>%s.</b> %s" % (a,b), styles["Bul"]), leftIndent=6) for a,b in conx],
    bulletType="bullet", bulletColor=TEAL, leftIndent=12, bulletFontSize=7))

# --- 6. Qué evaluar (para instrumentos) ---
E.append(Paragraph("6 · Constructos sugeridos para los instrumentos", styles["H2"]))
E.append(Paragraph(
    "Posibles focos para cuestionarios (p. ej. escala Likert 1–5) y entrevistas, alineados con el método:",
    styles["Small"]))
E.append(Spacer(1, 3))
cons = [[P("Constructo", "TblH"), P("Qué indagar", "TblH")],
    [P("<b>Utilidad percibida</b>", "TblCb"), P("¿El ranking ayudó a decidir qué requisitos priorizar?", "TblC")],
    [P("<b>Detección de riesgos</b>", "TblCb"), P("¿La priorización visibilizó tensiones éticas que a simple vista no se veían?", "TblC")],
    [P("<b>Transparencia / explicabilidad</b>", "TblCb"), P("¿El desglose y la fórmula hicieron entendible por qué un requisito quedó donde quedó?", "TblC")],
    [P("<b>Confianza</b>", "TblCb"), P("¿Confiarían en este puntaje para justificar una decisión ante terceros?", "TblC")],
    [P("<b>Control humano</b>", "TblCb"), P("¿Fue adecuado poder editar pesos/fuerzas y las dimensiones propuestas por la IA?", "TblC")],
    [P("<b>Carga / esfuerzo</b>", "TblCb"), P("¿Cuánto esfuerzo costó completar la matriz de evaluación? ¿Fue proporcional al valor obtenido?", "TblC")],
    [P("<b>Adopción</b>", "TblCb"), P("¿Usarían este método en un proyecto real? ¿En qué contexto sí o no?", "TblC")]]
ct = Table(cons, colWidths=[48*mm, 124*mm], repeatRows=1)
csty=[("BACKGROUND",(0,0),(-1,0),INK),("VALIGN",(0,0),(-1,-1),"TOP"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
    ("LINEBELOW",(0,0),(-1,-1),0.4,LINE)]
for i in range(1,len(cons)):
    if i%2==0: csty.append(("BACKGROUND",(0,i),(-1,i),CANVAS))
ct.setStyle(TableStyle(csty))
E.append(ct)

doc.build(E)
print("OK ->", OUT)
