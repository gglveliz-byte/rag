# DIRECTRICES PARA AGENTES AUTÓNOMOS (AGENTS.MD)

Bienvenido. Como asistente o agente de desarrollo en este repositorio **RAG (Knowledge Engine)**, estás sujeto a las siguientes reglas obligatorias e inviolables:

---

## 1. Regla Estricta de Tamaño de Archivos (Máximo 800 Líneas)
- **Ningún archivo** (Python, TypeScript, CSS, HTML, etc.) debe superar las **800 líneas de código**.
- Si un componente o módulo se acerca a este límite, **debe ser descompuesto inmediatamente** en submódulos, subcomponentes o utilidades especializadas con nombres claros (ej. `ModulePart2.tsx`, `sub_service.py`, etc.).
- Mantén siempre una alta precisión y modularidad en cada cambio.

---

## 2. Actualización Obligatoria de Documentación (Skill `documentacion`)
- Cada vez que crees, modifiques, refactorices o elimines cualquier archivo del proyecto, **DEBES actualizar inmediatamente** el inventario y resumen en:
  `[.agents/skills/documentacion/SKILL.md](file:///c:/Users/HP/OneDrive/Documentos/GitHub/RAG/.agents/skills/documentacion/SKILL.md)`
- La documentación debe reflejar:
  - Nombre y ruta del archivo.
  - Conteo aproximado de líneas (verificando que sea < 800).
  - Propósito y responsabilidades principales.
  - Último cambio realizado.
- **Antes de tocar código**, lee siempre `SKILL.md` de documentación para entender el mapa global del sistema.

---

## 3. Coherencia de Estilos y Diseño (Skill `estilos`)
- Toda modificación en la interfaz visual (Landing Page, Workspace, Modales, Explorador) debe adherirse a los lineamientos documentados en:
  `[.agents/skills/estilos/SKILL.md](file:///c:/Users/HP/OneDrive/Documentos/GitHub/RAG/.agents/skills/estilos/SKILL.md)`
- Estética HUD técnica, tipografía suiza, micro-interacciones sutiles y diseño responsive.
