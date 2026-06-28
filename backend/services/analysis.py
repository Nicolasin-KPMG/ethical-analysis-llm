"""Orquestacion de las Fases 2-3 (LLM + RAG). Se implementa en M5.

Flujo previsto (ver seccion 7 del contexto):
1. Primer pase del LLM: temas y familias de normas candidatas.
2. Recuperacion en pgvector filtrando por temas, jurisdiccion y normas activas.
3. Segundo pase del LLM: analisis final (tres capas) citando los fragmentos.
4. Validacion contra el esquema Pydantic y registro de citas.
"""
