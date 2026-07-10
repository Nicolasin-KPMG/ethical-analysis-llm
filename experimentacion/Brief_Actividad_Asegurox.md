# Actividad de experimentación — App de gestión ética y priorización de requisitos

## Qué es
Sesión guiada de **~60 min** con **3–4 participantes** que **usan una herramienta web**
(no definen requisitos: los reciben ya redactados). La app sistematiza un método de
**8 fases** que, para cada requisito de un proyecto de software con IA, detecta
implicancias éticas, propone cómo tratarlas y calcula un ranking que equilibra
**valor vs. riesgo**. La tarea del grupo es **analizar, decidir el tratamiento y
priorizar** los requisitos.

## El caso: "Asegurox"
Aseguradora ficticia (Chile) con desorden en la **gestión de accesos**
(certificaciones que no se hacían, permisos incompatibles, cuentas de exempleados).
Encargó una **plataforma con IA** que certifique accesos y controle la **segregación
de funciones**. Ya hay **15 requisitos cargados** en el proyecto; la mayoría son
operativos y unos pocos tienen tensión ética.

## Acceso
- URL: **http://159.223.124.246:3001**
- Usuario: **demo@example.com** · Clave: **demo1234**
- Trabajen sobre el proyecto **"Asegurox — Certificación de accesos"** (limpio, para
  la sesión). Existe también una copia **"(DEMO resuelta)"** solo como referencia de
  cómo se ve terminado.

## Actividades a realizar (flujo completo, 8 fases)

### Fase 1 · Registro
El proyecto y los 15 requisitos ya están cargados; solo revisarlos.

### Fases 2–3 · Análisis ético con IA
1. Correr el **cribado**: marca qué requisitos podrían tener riesgo ético (los demás
   quedan como operativos).
2. Para cada requisito marcado, ejecutar el **análisis** y revisar las **3 capas**:
   - **Capa 1:** tema ético, actor afectado, tipo de daño y **norma tensionada con
     citas reales** a la normativa.
   - **Capa 2:** mapa de actores y tensiones entre valores.
   - **Capa 3:** deliberación: opciones de tratamiento, reformulaciones y requisitos
     derivados.
3. **Decidir el tratamiento** de cada uno: **aceptar / reformular / mitigar /
   eliminar**.
   - *Mitigar* genera requisitos **derivados** de control.
   - *Reformular* crea una nueva versión del requisito.
   - *Eliminar* lo saca del ranking (queda como historial, no se borra).

### Fase 4 · Dimensiones
Definir y **ponderar (peso 1–5)** las dimensiones de priorización: **beneficio** y
**valor ético** (suman), **costo** y **riesgo ético** (restan). Las de **riesgo
ético** las propone la IA en el análisis; las de beneficio/costo las define el equipo.

> **Requisito del área de Seguridad de la Información / Auditoría:** para que la
> priorización sirva a cumplimiento, **deben estar presentes al menos estas
> dimensiones**:
>
> | Dimensión | Tipo | Qué mide |
> |---|---|---|
> | Cierre de hallazgos de auditoría | Beneficio | Cuánto ayuda el requisito a cerrar las observaciones de la auditoría. |
> | Reducción del riesgo de accesos indebidos / fraude | Beneficio | Cuánto baja la exposición a permisos incompatibles y cuentas indebidas. |
> | Costo de implementación | Costo | Esfuerzo técnico y de tiempo para construirlo. |
> | Fricción operativa | Costo | Carga que agrega a jefaturas y usuarios (revisiones, aprobaciones). |
>
> El área quiere asegurarse de que la decisión no mire solo "valor" genérico, sino
> también el **impacto en cumplimiento** y el **esfuerzo real**.

### Fase 5 · Evaluación
Completar la **matriz requisito × dimensión**, indicando con qué intensidad
(0 = no aplica … 5 = muy alta) cada requisito expresa cada dimensión.

### Fase 6 · Ranking
La app calcula, de forma **determinista y sin IA**:

```
Puntaje = Σ(beneficio) + Σ(valor ético) − Σ(costo) − Σ(riesgo ético)
```

Observar cómo los requisitos con alto riesgo ético caen en la lista, y cómo los
**derivados de una mitigación** aparecen **como bloque bajo su requisito padre**
(no compiten sueltos en el ranking).

### Fases 7–8 · Trazabilidad y tablero
Revisar los derivados y su trazabilidad, la **bandera ética** por requisito en el
tablero, y **exportar el proyecto** (entregable).

## Entregable
Proyecto **analizado, tratado y priorizado**, con el ranking a la vista, y el
**archivo exportado**. Al cierre, feedback de usabilidad.

## Qué observar (para el feedback)
- ¿La app ayudó a detectar tensiones que no eran evidentes? ¿Alguna inesperada?
- ¿Las **citas normativas** y las **propuestas de tratamiento** fueron pertinentes?
- ¿El **ranking** reflejó bien el equilibrio beneficio/riesgo?
- ¿Qué paso costó más o confundió?
