"""Implementa: RF-R1-18.

Convierte el `content_json` (documento ProseMirror) de un viaje en HTML
seguro para servir en la vista de lectura. No es un sanitizador de HTML
arbitrario: recorre el árbol JSON y solo emite las etiquetas/atributos que
reconoce explícitamente (lista blanca positiva). Cualquier nodo, marca o
valor de atributo que no esté en la lista blanca se descarta en silencio en
vez de intentar repararse o pasarse tal cual.
"""

from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_FONT_SIZE_RE = re.compile(r"^([0-9]{1,2})px$")
_ALLOWED_TEXT_ALIGN = {"left", "center", "right", "justify"}
_ALLOWED_LINK_SCHEMES = {"http", "https", "mailto"}
_ALLOWED_HEADING_LEVELS = {2, 3, 4}

# Placeholder: el conjunto final de tipografías autoalojadas lo fija WP-R1-5
# (frontend). Mantener sincronizado con lo que ofrezca el editor.
ALLOWED_FONT_FAMILIES = {"Inter", "Merriweather", "Fira Mono"}

_BLOCK_TAGS = {
    "paragraph": "p",
    "blockquote": "blockquote",
}

_HTML_ESCAPE_TABLE = str.maketrans(
    {
        '"': "&quot;",
        "'": "&#x27;",
    }
)


def _escape_attr(value: str) -> str:
    return html.escape(value, quote=True).translate(_HTML_ESCAPE_TABLE)


def _valid_font_size(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = _FONT_SIZE_RE.match(value)
    if not match:
        return None
    size = int(match.group(1))
    if 8 <= size <= 96:
        return value
    return None


def _valid_color(value: object) -> str | None:
    if isinstance(value, str) and _COLOR_RE.match(value):
        return value
    return None


def _valid_font_family(value: object) -> str | None:
    if isinstance(value, str) and value in ALLOWED_FONT_FAMILIES:
        return value
    return None


def _valid_href(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    # Descarta esquemas peligrosos escondidos tras caracteres de control o
    # espacios en blanco intercalados (p. ej. "java\tscript:alert(1)"):
    # se elimina todo carácter de control/espacio antes de interpretar el
    # esquema, igual que hacen los navegadores.
    stripped = re.sub(r"[\x00-\x20]", "", value)
    try:
        parts = urlsplit(stripped)
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_LINK_SCHEMES:
        return None
    if scheme in ("http", "https") and not parts.netloc:
        return None
    return stripped


def _text_align_style(attrs: dict) -> str:
    align = attrs.get("textAlign") if isinstance(attrs, dict) else None
    if align in _ALLOWED_TEXT_ALIGN:
        return f' style="text-align: {align}"'
    return ""


def _render_marks(text: str, marks: list) -> str:
    """Envuelve el texto (ya escapado) con las marcas permitidas, en orden fijo."""
    span_styles: list[str] = []
    link_href: str | None = None
    has_bold = has_italic = has_underline = has_strike = False

    for mark in marks or []:
        if not isinstance(mark, dict):
            continue
        mark_type = mark.get("type")
        attrs = mark.get("attrs") if isinstance(mark.get("attrs"), dict) else {}

        if mark_type == "bold":
            has_bold = True
        elif mark_type == "italic":
            has_italic = True
        elif mark_type == "underline":
            has_underline = True
        elif mark_type == "strike":
            has_strike = True
        elif mark_type == "link":
            href = _valid_href(attrs.get("href"))
            if href is not None:
                link_href = href
        elif mark_type == "textStyle":
            color = _valid_color(attrs.get("color"))
            if color is not None:
                span_styles.append(f"color: {color}")
            font_family = _valid_font_family(attrs.get("fontFamily"))
            if font_family is not None:
                span_styles.append(f'font-family: "{font_family}"')
            font_size = _valid_font_size(attrs.get("fontSize"))
            if font_size is not None:
                span_styles.append(f"font-size: {font_size}")
        elif mark_type == "highlight":
            color = _valid_color(attrs.get("color"))
            if color is not None:
                span_styles.append(f"background-color: {color}")
        # Cualquier otro tipo de marca se descarta.

    result = text
    if span_styles:
        style_attr = _escape_attr("; ".join(span_styles))
        result = f'<span style="{style_attr}">{result}</span>'
    if has_bold:
        result = f"<strong>{result}</strong>"
    if has_italic:
        result = f"<em>{result}</em>"
    if has_underline:
        result = f"<u>{result}</u>"
    if has_strike:
        result = f"<s>{result}</s>"
    if link_href is not None:
        href_attr = _escape_attr(link_href)
        result = f'<a href="{href_attr}" rel="noopener noreferrer nofollow">{result}</a>'
    return result


def _render_inline(node: dict) -> str:
    node_type = node.get("type")
    if node_type == "text":
        text = node.get("text")
        if not isinstance(text, str):
            return ""
        return _render_marks(html.escape(text), node.get("marks") or [])
    if node_type == "hardBreak":
        return "<br>"
    return ""


def _render_children(content: list) -> str:
    parts: list[str] = []
    for child in content:
        if not isinstance(child, dict):
            continue
        parts.append(_render_node(child))
    return "".join(parts)


def _render_node(node: dict) -> str:
    node_type = node.get("type")
    attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
    content = node.get("content") if isinstance(node.get("content"), list) else []

    if node_type in ("text", "hardBreak"):
        return _render_inline(node)

    if node_type in _BLOCK_TAGS:
        tag = _BLOCK_TAGS[node_type]
        return f"<{tag}{_text_align_style(attrs)}>{_render_children(content)}</{tag}>"

    if node_type == "heading":
        level = attrs.get("level")
        if level not in _ALLOWED_HEADING_LEVELS:
            level = 2
        tag = f"h{level}"
        return f"<{tag}{_text_align_style(attrs)}>{_render_children(content)}</{tag}>"

    if node_type == "bulletList":
        return f"<ul>{_render_children(content)}</ul>"

    if node_type == "orderedList":
        return f"<ol>{_render_children(content)}</ol>"

    if node_type == "listItem":
        return f"<li>{_render_children(content)}</li>"

    if node_type == "horizontalRule":
        return "<hr>"

    if node_type == "doc":
        return _render_children(content)

    # Nodo desconocido: se descarta por completo (no se renderiza ni su
    # contenido), para no filtrar estructura inesperada.
    return ""


def render_content_html(content_json: dict | None) -> str:
    """Renderiza un documento ProseMirror como HTML seguro por lista blanca."""
    if not isinstance(content_json, dict):
        return ""
    if content_json.get("type") != "doc":
        return ""
    return _render_node(content_json)
