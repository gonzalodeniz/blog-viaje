# TASK-R1-006 — Sanitización HTML del editor (JSON ProseMirror → HTML con lista blanca)

- **WP:** WP-R1-4
- **Requisitos:** RF-R1-18
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-006

## Objetivo

Existe una función de servicio, pura y testeable de forma aislada, que convierte el `content_json` (documento ProseMirror) de un viaje en el `content_html` que se sirve en la vista de lectura, aplicando una lista blanca de nodos/marcas/atributos/estilos. No incluye el endpoint que la invoca al guardar un viaje (CRUD admin, WP-R1-5) ni el editor TipTap del frontend: es la pieza de seguridad de la que ambos dependen.

## Contexto y decisiones

- **Alcance deliberadamente reducido dentro de WP-R1-4:** sigue el mismo patrón de slices verticales que TASK-R1-005. La sanitización se construye y se prueba a fondo como unidad independiente antes de conectarla a ningún endpoint HTTP, para poder concentrar el esfuerzo de tests de seguridad en una superficie pequeña.
- **Renderizado por lista blanca positiva, no sanitización de HTML arbitrario:** en vez de aceptar HTML libre y limpiarlo (approach de tipo bleach/DOMPurify sobre texto ya-HTML), la función recorre el árbol JSON de ProseMirror y solo emite las etiquetas que reconoce explícitamente. Cualquier tipo de nodo o marca no reconocidos se descarta en vez de intentar repararlo o pasarlo tal cual. Esto evita por construcción toda la clase de bugs de parsers de HTML tolerantes con entradas malformadas.
- **Nodos de bloque soportados** (según la barra de RF-R1-17): `paragraph`, `heading` (niveles 2–4), `bulletList`/`orderedList`/`listItem`, `blockquote`, `horizontalRule`. Alineación (`attrs.textAlign` en `left|center|right|justify`) se traduce a `style="text-align: …"` en el elemento de bloque; cualquier otro valor se descarta (sin alineación).
- **Marcas en línea soportadas:** `bold`→`<strong>`, `italic`→`<em>`, `underline`→`<u>`, `strike`→`<s>`, `link`→`<a>` (solo esquemas `http`/`https`/`mailto`; siempre con `rel="noopener noreferrer nofollow"`), `textStyle` (color y tamaño de fuente) y `highlight` (color de resaltado), ambas como `<span style="…">`. `hardBreak`→`<br>`.
- **Validación estricta de estilos, no interpolación:** los colores solo se aceptan si son hex de 3 o 6 dígitos (`#fff`, `#ffffff`); el tamaño de fuente solo si es `Npx` con `N` entre 8 y 96. Cualquier otro valor (incluyendo intentos de `expression()`, `url()`, `javascript:`, etc.) se descarta y la marca se aplica sin ese estilo. No hay interpolación de cadenas en `style=`: se construye a partir de valores ya validados por regex/enum.
- **Fuentes:** RF-R1-17 pide "tipografías autoalojadas curadas", pero el conjunto final todavía no está decidido (depende del frontend, WP-R1-5). Se deja una lista blanca de ejemplo (`ALLOWED_FONT_FAMILIES`) fácil de ampliar; hay que mantenerla sincronizada cuando WP-R1-5 fije las tipografías reales.
- **Enlaces:** solo se aceptan `href` con esquema `http://`, `https://` o `mailto:`; cualquier otro esquema (`javascript:`, `data:`, `vbscript:`, variantes con espacios/tabs) descarta la marca `link` (el texto se renderiza sin enlace, no se descarta el texto).
- **Texto:** todo el contenido de texto se escapa con `html.escape` — nunca se interpola sin escapar en la salida.
- **Fuera de alcance:** el endpoint/CRUD que llama a esta función al guardar un viaje (WP-R1-5); el editor TipTap del frontend y su esquema real de ProseMirror (WP-R1-5); CSP de nginx (ya cubierta por RNF-R1-03 en WP-R1-1/2, sin cambios aquí).

## Definition of Done

- [x] Código con docstring `Implementa: RF-R1-18` en el módulo de sanitización
- [x] Tests con `@pytest.mark.spec("RF-R1-18")`: nodos/marcas permitidos se renderizan correctamente; nodos/marcas desconocidos se descartan sin excepción; intentos de XSS (`<script>`, `javascript:`, `onerror=`, `style` con `expression()`/`url()`, esquemas de enlace peligrosos, colores/tamaños fuera de la lista blanca) no aparecen en la salida; el texto siempre se escapa
- [x] Cobertura ≥ 80 % en el código tocado
- [x] Revisión de seguridad (sin `dangerouslySetInnerHTML` — no aplica, es backend; sin interpolación de estilos sin validar; salida siempre generada por lista blanca positiva)
- [x] `python tools/traceability.py --check --release R1` — sigue en rojo (quedan endpoints y otros WPs sin test), no bloquea esta tarea
- [x] Commits con prefijo `[TASK-R1-006]`

## Notas de implementación

- `backend/app/services/html_sanitizer.py`: función `render_content_html(content_json: dict | None) -> str`.
- `backend/tests/test_html_sanitizer.py`: casos positivos (un caso por nodo/marca soportados) y casos negativos (intentos de inyección), todos marcados `@pytest.mark.spec("RF-R1-18")`.
