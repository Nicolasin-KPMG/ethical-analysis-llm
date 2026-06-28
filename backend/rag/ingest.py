"""Ingesta del corpus normativo (offline, una vez por documento). Se implementa en M4.

Pasos previstos: cargar PDF -> limpiar -> chunquear por estructura legal
(articulo / considerando / seccion) -> generar embeddings -> guardar en pgvector.
"""
