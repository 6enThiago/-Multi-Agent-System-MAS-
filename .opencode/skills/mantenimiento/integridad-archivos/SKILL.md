---
name: integridad-archivos
description: Verifica la integridad de los archivos del proyecto y los modifica según lo solicitado. Úsala cuando se pida revisar, validar, corregir o editar archivos, o cuando un cambio pueda afectar a otros archivos relacionados.
---

# Integridad de Archivos

1. Lee el archivo a modificar y detecta qué otros archivos dependen de él (imports, configs, referencias).
2. Verifica que estén completos, sin errores de formato y sin referencias rotas.
3. Aplica solo el cambio solicitado, de forma mínima.
4. Revisa de nuevo los archivos vinculados para confirmar que nada quedó roto.
5. Si un cambio exige tocar otros archivos, ajústalos y avisa cuáles.
6. Reporta: qué se revisó, qué se cambió y qué problemas se encontraron.

Reglas:
- Haz una copia o anota el estado previo antes de cambios grandes.
- Nunca borres archivos sin confirmación.
