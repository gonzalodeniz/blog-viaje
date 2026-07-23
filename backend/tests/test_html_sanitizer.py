"""Implementa: RF-R1-18."""

import pytest

from app.services.html_sanitizer import render_content_html


def _doc(*content: dict) -> dict:
    return {"type": "doc", "content": list(content)}


def _text(text: str, marks: list | None = None) -> dict:
    node = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return node


@pytest.mark.spec("RF-R1-18")
def test_content_json_vacio_o_invalido_produce_html_vacio() -> None:
    assert render_content_html(None) == ""
    assert render_content_html({}) == ""
    assert render_content_html({"type": "not-a-doc"}) == ""
    assert render_content_html("<script>alert(1)</script>") == ""  # type: ignore[arg-type]


@pytest.mark.spec("RF-R1-18")
def test_parrafo_simple() -> None:
    doc = _doc({"type": "paragraph", "content": [_text("Hola")]})
    assert render_content_html(doc) == "<p>Hola</p>"


@pytest.mark.spec("RF-R1-18")
@pytest.mark.parametrize("level", [2, 3, 4])
def test_headings_permitidos(level: int) -> None:
    doc = _doc({"type": "heading", "attrs": {"level": level}, "content": [_text("Título")]})
    assert render_content_html(doc) == f"<h{level}>Título</h{level}>"


@pytest.mark.spec("RF-R1-18")
def test_heading_con_nivel_no_permitido_cae_a_h2() -> None:
    doc = _doc({"type": "heading", "attrs": {"level": 1}, "content": [_text("Título")]})
    assert render_content_html(doc) == "<h2>Título</h2>"


@pytest.mark.spec("RF-R1-18")
def test_alineacion_permitida_se_traduce_a_style() -> None:
    doc = _doc({"type": "paragraph", "attrs": {"textAlign": "center"}, "content": [_text("Centrado")]})
    assert render_content_html(doc) == '<p style="text-align: center">Centrado</p>'


@pytest.mark.spec("RF-R1-18")
def test_alineacion_no_permitida_se_descarta() -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "attrs": {"textAlign": "left; } body { display:none"},
            "content": [_text("Texto")],
        }
    )
    assert render_content_html(doc) == "<p>Texto</p>"


@pytest.mark.spec("RF-R1-18")
def test_listas_y_blockquote_y_hr() -> None:
    doc = _doc(
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [_text("uno")]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [_text("dos")]}]},
            ],
        },
        {"type": "orderedList", "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [_text("tres")]}]}]},
        {"type": "blockquote", "content": [{"type": "paragraph", "content": [_text("cita")]}]},
        {"type": "horizontalRule"},
    )
    html_out = render_content_html(doc)
    assert html_out == (
        "<ul><li><p>uno</p></li><li><p>dos</p></li></ul>"
        "<ol><li><p>tres</p></li></ol>"
        "<blockquote><p>cita</p></blockquote>"
        "<hr>"
    )


@pytest.mark.spec("RF-R1-18")
def test_hard_break() -> None:
    doc = _doc({"type": "paragraph", "content": [_text("uno"), {"type": "hardBreak"}, _text("dos")]})
    assert render_content_html(doc) == "<p>uno<br>dos</p>"


@pytest.mark.spec("RF-R1-18")
def test_marcas_inline_basicas() -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [
                _text("negrita", [{"type": "bold"}]),
                _text("cursiva", [{"type": "italic"}]),
                _text("subrayado", [{"type": "underline"}]),
                _text("tachado", [{"type": "strike"}]),
            ],
        }
    )
    assert render_content_html(doc) == (
        "<p><strong>negrita</strong><em>cursiva</em><u>subrayado</u><s>tachado</s></p>"
    )


@pytest.mark.spec("RF-R1-18")
def test_marcas_combinadas_se_anidan_en_orden_fijo() -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [_text("texto", [{"type": "italic"}, {"type": "bold"}])],
        }
    )
    # El orden de salida no depende del orden de las marcas en el JSON.
    assert render_content_html(doc) == "<p><em><strong>texto</strong></em></p>"


@pytest.mark.spec("RF-R1-18")
def test_color_y_tamano_de_fuente_validos() -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [
                _text(
                    "coloreado",
                    [{"type": "textStyle", "attrs": {"color": "#ff0000", "fontSize": "24px"}}],
                )
            ],
        }
    )
    assert render_content_html(doc) == (
        '<p><span style="color: #ff0000; font-size: 24px">coloreado</span></p>'
    )


@pytest.mark.spec("RF-R1-18")
def test_fuente_permitida_se_incluye_y_no_permitida_se_descarta() -> None:
    permitido = _doc(
        {
            "type": "paragraph",
            "content": [_text("x", [{"type": "textStyle", "attrs": {"fontFamily": "Inter"}}])],
        }
    )
    assert render_content_html(permitido) == '<p><span style="font-family: &quot;Inter&quot;">x</span></p>'

    no_permitido = _doc(
        {
            "type": "paragraph",
            "content": [_text("x", [{"type": "textStyle", "attrs": {"fontFamily": "Comic Sans MS"}}])],
        }
    )
    assert render_content_html(no_permitido) == "<p>x</p>"


@pytest.mark.spec("RF-R1-18")
def test_highlight_valido() -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [_text("resaltado", [{"type": "highlight", "attrs": {"color": "#ffff00"}}])],
        }
    )
    assert render_content_html(doc) == '<p><span style="background-color: #ffff00">resaltado</span></p>'


@pytest.mark.spec("RF-R1-18")
@pytest.mark.parametrize(
    "color",
    [
        "red",
        "#ff",
        "#gggggg",
        "expression(alert(1))",
        "rgb(255,0,0)",
        "#fff; background: url(javascript:alert(1))",
    ],
)
def test_colores_no_hex_se_descartan(color: str) -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [_text("x", [{"type": "textStyle", "attrs": {"color": color}}])],
        }
    )
    assert render_content_html(doc) == "<p>x</p>"


@pytest.mark.spec("RF-R1-18")
@pytest.mark.parametrize("size", ["7px", "97px", "20pt", "20", "20px; } * { display:none"])
def test_tamanos_de_fuente_fuera_de_rango_se_descartan(size: str) -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [_text("x", [{"type": "textStyle", "attrs": {"fontSize": size}}])],
        }
    )
    assert render_content_html(doc) == "<p>x</p>"


@pytest.mark.spec("RF-R1-18")
def test_enlace_http_y_mailto_permitidos() -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [
                _text("sitio", [{"type": "link", "attrs": {"href": "https://example.com/ruta?x=1"}}]),
            ],
        }
    )
    assert render_content_html(doc) == (
        '<p><a href="https://example.com/ruta?x=1" rel="noopener noreferrer nofollow">sitio</a></p>'
    )


@pytest.mark.spec("RF-R1-18")
@pytest.mark.parametrize(
    "href",
    [
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        "java\tscript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "file:///etc/passwd",
        "https:",
        "  javascript:alert(1)",
    ],
)
def test_enlaces_con_esquema_peligroso_se_descartan(href: str) -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [_text("sitio", [{"type": "link", "attrs": {"href": href}}])],
        }
    )
    assert render_content_html(doc) == "<p>sitio</p>"


@pytest.mark.spec("RF-R1-18")
def test_href_se_escapa_en_el_atributo() -> None:
    doc = _doc(
        {
            "type": "paragraph",
            "content": [
                _text(
                    "sitio",
                    [{"type": "link", "attrs": {"href": 'https://example.com/"><script>alert(1)</script>'}}],
                )
            ],
        }
    )
    html_out = render_content_html(doc)
    assert "<script>" not in html_out
    assert "&quot;" in html_out


@pytest.mark.spec("RF-R1-18")
def test_texto_con_caracteres_especiales_se_escapa() -> None:
    doc = _doc({"type": "paragraph", "content": [_text("<b>hola</b> & 'amigos' \"todos\"")]})
    html_out = render_content_html(doc)
    assert "<b>hola</b>" not in html_out
    assert "&lt;b&gt;hola&lt;/b&gt;" in html_out
    assert "&amp;" in html_out


@pytest.mark.spec("RF-R1-18")
def test_nodo_desconocido_se_descarta_sin_excepcion() -> None:
    doc = _doc(
        {"type": "paragraph", "content": [_text("antes")]},
        {"type": "customEmbed", "attrs": {"src": "javascript:alert(1)"}, "content": [_text("malicioso")]},
        {"type": "paragraph", "content": [_text("despues")]},
    )
    assert render_content_html(doc) == "<p>antes</p><p>despues</p>"


@pytest.mark.spec("RF-R1-18")
def test_marca_desconocida_se_descarta_sin_excepcion() -> None:
    doc = _doc({"type": "paragraph", "content": [_text("x", [{"type": "spoiler"}])]})
    assert render_content_html(doc) == "<p>x</p>"


@pytest.mark.spec("RF-R1-18")
def test_nodo_de_texto_sin_texto_no_rompe() -> None:
    doc = _doc({"type": "paragraph", "content": [{"type": "text"}]})
    assert render_content_html(doc) == "<p></p>"


@pytest.mark.spec("RF-R1-18")
def test_href_no_string_se_descarta() -> None:
    doc = _doc(
        {"type": "paragraph", "content": [_text("x", [{"type": "link", "attrs": {"href": 123}}])]}
    )
    assert render_content_html(doc) == "<p>x</p>"


@pytest.mark.spec("RF-R1-18")
def test_marca_que_no_es_diccionario_se_ignora() -> None:
    doc = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "x", "marks": ["bold"]}]}],
    }
    assert render_content_html(doc) == "<p>x</p>"


@pytest.mark.spec("RF-R1-18")
def test_hijo_que_no_es_diccionario_se_ignora() -> None:
    doc = {"type": "doc", "content": [{"type": "paragraph", "content": ["no-es-un-nodo"]}]}
    assert render_content_html(doc) == "<p></p>"


@pytest.mark.spec("RF-R1-18")
def test_nodo_de_tipo_desconocido_dentro_de_marcas_inline_se_ignora() -> None:
    doc = _doc({"type": "paragraph", "content": [{"type": "emoji", "attrs": {"name": "smile"}}]})
    assert render_content_html(doc) == "<p></p>"
