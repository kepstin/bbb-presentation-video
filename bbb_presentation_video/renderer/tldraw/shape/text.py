# SPDX-FileCopyrightText: 2022 BigBlueButton Inc. and by respective authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TypeVar

import cairo
import gi

from bbb_presentation_video.renderer.tldraw import vec
from bbb_presentation_video.renderer.tldraw.shape import (
    LabelledShapeProto,
    TextShape,
    TriangleShape,
    apply_shape_rotation,
)
from bbb_presentation_video.renderer.tldraw.utils import (
    FONT_FACES,
    FONT_SIZES,
    LETTER_SPACING,
    STROKES,
    DashStyle,
    AlignStyle,
    Style,
    triangle_centroid,
)

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo


def set_pango_font(pctx: Pango.Context, style: Style) -> Pango.FontDescription:
    font = Pango.FontDescription()
    font.set_family(FONT_FACES[style.font])
    font.set_absolute_size(FONT_SIZES[style.size] * style.scale * Pango.SCALE)

    fo = cairo.FontOptions()
    fo.set_antialias(cairo.ANTIALIAS_GRAY)
    fo.set_hint_metrics(cairo.HINT_METRICS_ON)
    fo.set_hint_style(cairo.HINT_STYLE_NONE)
    PangoCairo.context_set_font_options(pctx, fo)

    return font


CairoSomeSurface = TypeVar("CairoSomeSurface", bound="cairo.Surface")


def finalize_text(
    ctx: "cairo.Context[CairoSomeSurface]", id: str, shape: TextShape
) -> None:
    print(f"\tTldraw: Finalizing Text: {id}")

    apply_shape_rotation(ctx, shape)

    style = shape.style

    pctx = PangoCairo.create_context(ctx)
    font = set_pango_font(pctx, style)

    attrs = Pango.AttrList()
    letter_spacing_attr = Pango.attr_letter_spacing_new(
        int(LETTER_SPACING * FONT_SIZES[style.size] * style.scale * Pango.SCALE)
    )
    attrs.insert(letter_spacing_attr)

    layout = Pango.Layout(pctx)
    layout.set_auto_dir(True)
    layout.set_attributes(attrs)
    layout.set_font_description(font)
    layout.set_line_spacing(0.4)

    if style.textAlign == AlignStyle.START:
        layout.set_alignment(Pango.Alignment.LEFT)
    elif style.textAlign == AlignStyle.MIDDLE:
        layout.set_alignment(Pango.Alignment.CENTER)
    elif style.textAlign == AlignStyle.END:
        layout.set_alignment(Pango.Alignment.RIGHT)
    elif style.textAlign == AlignStyle.JUSTIFY:
        layout.set_alignment(Pango.Alignment.LEFT)
        layout.set_justify(True)

    layout.set_text(shape.text, -1)

    ctx.set_source_rgb(*STROKES[style.color])

    PangoCairo.show_layout(ctx, layout)


def finalize_label(
    ctx: "cairo.Context[CairoSomeSurface]", shape: LabelledShapeProto
) -> None:
    if shape.label is None or shape.label == "":
        return

    print(f"\tTldraw: Finalizing Label")

    style = shape.style

    pctx = PangoCairo.create_context(ctx)
    font = set_pango_font(pctx, style)

    attrs = Pango.AttrList()
    letter_spacing_attr = Pango.attr_letter_spacing_new(
        int(LETTER_SPACING * FONT_SIZES[style.size] * style.scale * Pango.SCALE)
    )
    attrs.insert(letter_spacing_attr)

    layout = Pango.Layout(pctx)
    layout.set_auto_dir(True)
    layout.set_font_description(font)
    layout.set_attributes(attrs)
    layout.set_line_spacing(0.4)
    layout.set_alignment(Pango.Alignment.CENTER)

    layout.set_text(shape.label, -1)

    (layout_width, layout_height) = layout.get_pixel_size()
    if style.dash is DashStyle.DRAW or isinstance(shape, TriangleShape):
        width_offset = (shape.size.width - layout_width) * shape.labelPoint.x
        height_offset = (shape.size.height - layout_height) * shape.labelPoint.y
    else:
        width_offset = (-layout_width) * shape.labelPoint.x
        height_offset = (-layout_height) * shape.labelPoint.y

    if isinstance(shape, TriangleShape):
        # label of triangle has an offset
        center = vec.div([shape.size.width, shape.size.height], 2)
        centroid = triangle_centroid(shape.size.width, shape.size.height)
        offsetY = (centroid[1] - center[1]) * 0.72
        height_offset += offsetY

    ctx.translate(width_offset, height_offset)

    ctx.set_source_rgb(*STROKES[style.color])

    PangoCairo.show_layout(ctx, layout)
