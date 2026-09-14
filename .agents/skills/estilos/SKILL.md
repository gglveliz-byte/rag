---
name: estilos
description: Guía de diseño visual, tokens CSS, componentes y arquitectura de estilos para Knowledge Engine (RAG).
---

# Skill de Estilos y Diseño — Knowledge Engine (RAG)

Esta skill documenta las decisiones de diseño, tokens de CSS, componentes y estética aplicada en la interfaz del sistema.

---

## 1. Filosofía de Diseño
- **Estética:** *Swiss Engineering Precision* y estética HUD técnica para herramientas de inteligencia artificial y memoria vectorial.
- **Tipografía:**
  - Principal: `Inter` (sans-serif moderno y legible).
  - Técnica / Monospace: `JetBrains Mono` / `SF Mono` para badges, chips, contadores, hashes y código.
- **Paleta de Colores:**
  - Fondos de estudio: `#E7E9EC` a `#F6F7F9` (modo claro arquitectónico).
  - Acento oscuro: `#0F172A` (Slate 900) para botones primarios y encabezados.
  - Bordes técnicos: `rgba(0, 0, 0, 0.06)` a `rgba(0, 0, 0, 0.12)`.
  - Estados: Verde esmeralda para éxitos/SSE activo (`#10B981`), azul zafiro para embeddings y acentos (`#3B82F6`).

---

## 2. Landing Page (`frontend/src/landing.css`)
- **Imágenes Responsivas con `<picture>`:**
  - **Desktop (`min-width: 769px`):** Ilustración panorámica (`/assets/landing_hero_full.png`, 1983x793) con lienzo contenido en estudio `#E7E9EC`.
  - **Móvil (`max-width: 768px`):** Composición vertical nativa (`/assets/landing_hero_mobile.png`, 576x1024) adaptada a pantallas táctiles.
- **Protección Integral de Imagen (Cero Copiado / Cero Arrastre):**
  - Propiedades CSS: `pointer-events: none; user-select: none; -webkit-user-drag: none; -webkit-touch-callout: none;`.
  - Atributos HTML: `draggable={false}`, `onContextMenu={e => e.preventDefault()}`, `onDragStart={e => e.preventDefault()}`.
  - La imagen es completamente inerte y no responde a clics ni selecciones; la navegación se ejecuta exclusivamente a través de los botones.
- **Acciones Flotantes en Desktop (`.landing-overlay-topbar`):**
  - Esquina superior derecha (`top: 24px; right: 36px; z-index: 30`).
  - Botón **"INICIAR SESIÓN"** (`.btn-overlay-login`): Cristal esmerilado translúcido con efecto hover inverso.
  - Botón **"COMENZAR AHORA"** (`.btn-overlay-start`): Botón oscuro satinado con flecha interactiva.
- **Experiencia Móvil de Ingeniería (`.landing-mobile-dock`):**
  - **Encabezado Limpio:** En pantallas móviles, el topbar de escritorio se oculta para dejar visible y despejado el logotipo `KNOWLEDGE ENGINE`.
  - **Target de Menú:** Botón invisible sobre el icono hamburguesa (`.btn-mobile-menu-target`) en la esquina superior derecha que abre el modal de autenticación.
  - **Dock Inferior Flotante:** Barra flotante fija en `bottom: 14px; left: 14px; right: 14px;` con `backdrop-filter: blur(16px)` y esquinas redondeadas de 12px, con acceso táctil ergonómico para el pulgar a "INICIAR SESIÓN" y "COMENZAR AHORA".

---

## 3. Workspace del Motor (`frontend/src/index.css` & `src/App.tsx`)
- **Navegación Limpia y Minimalista:**
  - **Botón de Inicio:** Únicamente el icono de la casita `<Home size={16} />` en el encabezado superior, sin etiquetas de texto redundantes como "Presentación", "Landing" o "Inicio".
  - **Sidebar de Precisión:** Elementos de menú vertical en la barra lateral para ingesta, Google Drive, búsqueda semántica, explorador, backups y API keys.
  - **Depuración de Elementos Innecesarios:** Se eliminó la barra inferior fija de navegación redundante y la tarjeta de estado del motor ("Estado del Motor / Modo Persistencia") para maximizar el espacio visual y la limpieza HUD del entorno.
- **Formularios e Inputs:** Campos con etiquetas mono pequeñas, bordes sutiles y transiciones de foco limpias.
- **Tarjetas y Paneles:** Estructura modular con bordes de 1px y fondos blancos o grises ultra suaves.

---

## 4. Sistema de Modales y Autenticación (`.modal-card` & `AuthModal.tsx`)
- **Tarjeta Arquitectónica Suiza:**
  - Fondo blanco sólido `#FFFFFF` con borde `rgba(226, 232, 240, 0.95)`, radio de `20px` y sombra de elevación profunda `0 25px 60px -15px rgba(15, 23, 42, 0.28)`.
  - Animación de entrada con curva cúbica natural (`modalScaleIn`) y desenfoque de fondo (`backdrop-filter: blur(10px)`).
- **Control Segmentado de Pestañas (`.auth-segmented-tabs`):**
  - Selector tipo cápsula con fondo gris suave `#F1F5F9` para alternar instantáneamente entre **"Iniciar Sesión"** y **"Crear Cuenta"**.
  - Pestaña activa con pastilla blanca satinada `#FFFFFF`, texto oscuro `#0F172A` y micro-sombra.
- **Campos de Entrada de Alta Precisión:**
  - Contenedores con iconos contextuales (`Mail`, `Lock`), fondo `#F8FAFC`, bordes nítidos de 1px y anillos de enfoque sutiles.
  - Botón de alternancia de visibilidad de contraseña (`Eye` / `EyeOff`) con respuesta táctil.
  - Validación de coincidencia de contraseñas en tiempo real para el modo de registro.
- **Botón de Acción Satinado (`.auth-submit-btn`):**
  - Fondo carbón `#0F172A`, texto blanco, micro-animación de traslación en hover y flecha indicadora.
- **Insignias y Confianza:**
  - Badge técnico superior `ACCESO SEGURO` con escudo esmeralda y pie de seguridad con detalle de cifrado multi-tenant y hashing bcrypt.
