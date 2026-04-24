"""PDF export utilities."""

from __future__ import annotations

from datetime import datetime, timezone
import textwrap


PAGE_WIDTH = 210
PAGE_HEIGHT = 297
LEFT_MARGIN = 14
RIGHT_MARGIN = 14
TOP_MARGIN = 16
BOTTOM_MARGIN = 16

COLOR_BACKGROUND = (250, 248, 245)
COLOR_SURFACE = (255, 255, 255)
COLOR_SURFACE_ALT = (246, 240, 233)
COLOR_TEXT = (41, 37, 36)
COLOR_MUTED = (116, 106, 98)
COLOR_DIVIDER = (228, 220, 213)
COLOR_BRAND = (180, 83, 9)
COLOR_VIBRANT = (217, 119, 6)
COLOR_WATERMARK = (233, 227, 221)


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_minimal_pdf(lines: list[str]) -> bytes:
    stream_rows = ["BT", "/F1 12 Tf", "50 770 Td"]
    for index, line in enumerate(lines):
        escaped = _escape_pdf_text(line)
        if index == 0:
            stream_rows.append(f"({escaped}) Tj")
        else:
            stream_rows.append(f"0 -16 Td ({escaped}) Tj")
    stream_rows.append("ET")
    stream_bytes = "\n".join(stream_rows).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
        + stream_bytes
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(offsets) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("ascii")
    )
    return bytes(pdf)


def _normalize_pdf_value(value: object) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    ascii_text = "".join(ch if 31 < ord(ch) < 127 else " " for ch in text)
    compact = " ".join(ascii_text.split())

    if not compact:
        return "-"

    tokens: list[str] = []
    for token in compact.split(" "):
        if len(token) <= 26:
            tokens.append(token)
            continue

        tokens.extend(token[index : index + 26] for index in range(0, len(token), 26))

    return " ".join(tokens)


def _fallback_pdf_lines(
    *,
    full_name: str,
    age: int,
    profile: dict[str, str],
    sections: list[dict[str, object]],
) -> list[str]:
    lines = [
        "NutriAI Personalized Meal Plan",
        f"Generated for: {_normalize_pdf_value(full_name)} (Age {age})",
        f"Date: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')}",
    ]
    lines.extend(f"{_normalize_pdf_value(key)}: {_normalize_pdf_value(value)}" for key, value in profile.items())
    for section in sections:
        name = _normalize_pdf_value(section.get("name", "Section"))
        lines.append(f"{name}:")
        options = section.get("options", [])
        if isinstance(options, list):
            lines.extend([f"- {_normalize_pdf_value(option)}" for option in options])
    return lines


def build_meal_plan_pdf(
    *,
    full_name: str,
    age: int,
    profile: dict[str, str],
    sections: list[dict[str, object]],
) -> bytes:
    """Generate a meal plan PDF as bytes."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ModuleNotFoundError:
        return _build_minimal_pdf(
            _fallback_pdf_lines(full_name=full_name, age=age, profile=profile, sections=sections)
        )

    class MealPlanPDF(FPDF):
        def __init__(self) -> None:
            super().__init__(orientation="P", unit="mm", format="A4")
            self.set_auto_page_break(auto=False)
            self.alias_nb_pages()

        def header(self) -> None:
            self._draw_page_shell()
            if self.page_no() > 1:
                self._draw_compact_header()

        def footer(self) -> None:
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*COLOR_MUTED)
            self.cell(0, 5, "NutriAI personalized wellness companion", align="L")
            self.set_y(-12)
            self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="R")

        def _draw_page_shell(self) -> None:
            self.set_fill_color(*COLOR_BACKGROUND)
            self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, style="F")

            self.set_fill_color(*COLOR_SURFACE)
            self.rect(8, 8, PAGE_WIDTH - 16, PAGE_HEIGHT - 16, style="F")

            self.set_draw_color(*COLOR_DIVIDER)
            self.set_line_width(0.5)
            self.rect(8, 8, PAGE_WIDTH - 16, PAGE_HEIGHT - 16)

            self._draw_watermark()

        def _draw_watermark(self) -> None:
            self.set_text_color(*COLOR_WATERMARK)
            self.set_font("Helvetica", "B", 42)
            self.rotate(34, x=132, y=180)
            self.text(72, 180, "NUTRIAI")
            self.rotate(0)

        def _draw_compact_header(self) -> None:
            self.set_fill_color(*COLOR_SURFACE_ALT)
            self.rect(LEFT_MARGIN, TOP_MARGIN - 2, PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN, 18, style="F")

            self.set_fill_color(*COLOR_VIBRANT)
            self.rect(LEFT_MARGIN + 4, TOP_MARGIN + 3, 26, 8, style="F")
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 10)
            self.set_xy(LEFT_MARGIN + 4, TOP_MARGIN + 3.3)
            self.cell(26, 7, "NutriAI", align="C")

            self.set_text_color(*COLOR_TEXT)
            self.set_font("Helvetica", "B", 18)
            self.set_xy(LEFT_MARGIN + 35, TOP_MARGIN + 1.5)
            self.cell(0, 8, "Personalized Meal Plan")

            self.set_font("Helvetica", "", 9)
            self.set_text_color(*COLOR_MUTED)
            self.set_xy(LEFT_MARGIN + 35, TOP_MARGIN + 9)
            self.cell(0, 5, "Balanced nutrition guidance tailored to your goals")

        def _section_card(self, x: float, y: float, w: float, h: float, fill: tuple[int, int, int]) -> None:
            self.set_fill_color(*fill)
            self.rect(x, y, w, h, style="F")

        def _ensure_space(self, needed_height: float) -> None:
            if self.get_y() + needed_height <= PAGE_HEIGHT - BOTTOM_MARGIN:
                return
            self.add_page()
            self.set_y(TOP_MARGIN + 22)

    pdf = MealPlanPDF()
    pdf.add_page()

    printable_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    today = datetime.now(tz=timezone.utc).strftime("%d %b %Y")
    display_name = _normalize_pdf_value(full_name)

    pdf.set_y(TOP_MARGIN)
    pdf.set_fill_color(*COLOR_BRAND)
    pdf.rect(LEFT_MARGIN, TOP_MARGIN, printable_width, 34, style="F")

    pdf.set_fill_color(*COLOR_VIBRANT)
    pdf.rect(LEFT_MARGIN + 4, TOP_MARGIN + 4, 34, 10, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(LEFT_MARGIN + 4, TOP_MARGIN + 4.2)
    pdf.cell(34, 9, "NutriAI", align="C")

    pdf.set_xy(LEFT_MARGIN + 44, TOP_MARGIN + 5)
    pdf.set_font("Helvetica", "B", 25)
    pdf.cell(0, 9, "Personalized Meal Plan")

    pdf.set_xy(LEFT_MARGIN + 44, TOP_MARGIN + 17)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "A practical daily food plan designed around your body, routine, and goal.")

    pdf.set_xy(LEFT_MARGIN + 44, TOP_MARGIN + 24)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(255, 245, 235)
    pdf.cell(0, 5, f"Prepared for {display_name} | Generated on {today}")

    pdf.set_y(TOP_MARGIN + 42)
    pdf.set_fill_color(*COLOR_SURFACE_ALT)
    pdf.rect(LEFT_MARGIN, pdf.get_y(), printable_width, 28, style="F")

    left_card_width = 80
    right_card_x = LEFT_MARGIN + left_card_width + 4
    right_card_width = printable_width - left_card_width - 4
    card_y = pdf.get_y()

    pdf.set_fill_color(*COLOR_SURFACE)
    pdf.rect(LEFT_MARGIN + 3, card_y + 3, left_card_width - 6, 22, style="F")
    pdf.rect(right_card_x, card_y + 3, right_card_width - 3, 22, style="F")

    pdf.set_text_color(*COLOR_MUTED)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(LEFT_MARGIN + 8, card_y + 7)
    pdf.cell(0, 4, "CLIENT")
    pdf.set_xy(LEFT_MARGIN + 8, card_y + 12)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 7, display_name)
    pdf.set_xy(LEFT_MARGIN + 8, card_y + 19)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(0, 4, f"Age {age}")

    pdf.set_xy(right_card_x + 4, card_y + 7)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "PLAN FOCUS")
    pdf.set_xy(right_card_x + 4, card_y + 12)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, _normalize_pdf_value(profile.get("Goal", "Personal wellness plan")))
    pdf.set_xy(right_card_x + 4, card_y + 18.5)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(
        0,
        4,
        f"{_normalize_pdf_value(profile.get('Diet', '-'))} | {_normalize_pdf_value(profile.get('Cuisine', '-'))}",
    )

    pdf.set_y(card_y + 34)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, "Profile Snapshot", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(
        0,
        5,
        "NutriAI generated this plan from your current profile inputs and intended nutrition direction.",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    chip_items = [(str(key), str(value)) for key, value in profile.items()]
    chip_width = (printable_width - 8) / 2
    chip_height = 14
    pdf.ln(3)
    for index, (label, value) in enumerate(chip_items):
        x = LEFT_MARGIN + (index % 2) * (chip_width + 8)
        y = pdf.get_y()
        if index > 0 and index % 2 == 0:
            y += chip_height + 4
            pdf.set_y(y)
        pdf.set_fill_color(*COLOR_SURFACE_ALT)
        pdf.rect(x, y, chip_width, chip_height, style="F")
        pdf.set_xy(x + 4, y + 3)
        pdf.set_text_color(*COLOR_MUTED)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(0, 3, _normalize_pdf_value(label).upper())
        pdf.set_xy(x + 4, y + 7)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(chip_width - 8, 4, _normalize_pdf_value(value))
        if index % 2 == 1:
            pdf.set_y(y)
    if chip_items:
        rows = (len(chip_items) + 1) // 2
        pdf.set_y(pdf.get_y() + chip_height + 6)

    pdf.set_draw_color(*COLOR_DIVIDER)
    pdf.line(LEFT_MARGIN, pdf.get_y(), PAGE_WIDTH - RIGHT_MARGIN, pdf.get_y())
    pdf.ln(5)

    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, "Daily Plan", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.multi_cell(
        0,
        5,
        "Use the sections below as a flexible framework. Swap equivalent foods within the same meal category while keeping portions balanced.",
    )
    pdf.ln(2)

    accent_palette = [
        (255, 243, 224),
        (248, 236, 224),
        (245, 239, 231),
        (250, 242, 235),
    ]

    for index, section in enumerate(sections):
        name = _normalize_pdf_value(section.get("name", "Section"))
        options = section.get("options", [])
        safe_options = options if isinstance(options, list) else []

        estimated_rows = sum(max(1, len(textwrap.wrap(_normalize_pdf_value(str(option)), width=68))) for option in safe_options)
        estimated_height = 18 + max(12, estimated_rows * 7)
        pdf._ensure_space(estimated_height + 10)

        card_x = LEFT_MARGIN
        card_y = pdf.get_y()
        card_w = printable_width

        pdf._section_card(card_x, card_y, card_w, 12, accent_palette[index % len(accent_palette)])
        pdf.set_xy(card_x + 5, card_y + 2.5)
        pdf.set_text_color(*COLOR_BRAND)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 6, name)

        current_y = card_y + 15
        for option_index, option in enumerate(safe_options, start=1):
            safe_option = _normalize_pdf_value(option)
            wrapped = textwrap.wrap(
                safe_option,
                width=74,
                break_long_words=True,
                break_on_hyphens=False,
            ) or ["-"]

            block_height = 7 + max(0, len(wrapped) - 1) * 5
            pdf._ensure_space(block_height + 6)

            pdf.set_fill_color(*COLOR_SURFACE)
            pdf.rect(card_x + 2, current_y, card_w - 4, block_height + 3, style="F")

            pdf.set_xy(card_x + 6, current_y + 2)
            pdf.set_text_color(*COLOR_VIBRANT)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(8, 5, f"{option_index:02d}")

            pdf.set_xy(card_x + 15, current_y + 1.6)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(card_w - 21, 5.2, "\n".join(wrapped))
            current_y = max(current_y + block_height + 5, pdf.get_y() + 2)

        pdf.set_y(current_y + 2)

    pdf._ensure_space(28)
    pdf.set_fill_color(*COLOR_SURFACE_ALT)
    pdf.rect(LEFT_MARGIN, pdf.get_y(), printable_width, 20, style="F")
    pdf.set_xy(LEFT_MARGIN + 5, pdf.get_y() + 4)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, "NutriAI note")
    pdf.set_xy(LEFT_MARGIN + 5, pdf.get_y() + 5)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.set_font("Helvetica", "", 8.7)
    pdf.multi_cell(
        printable_width - 10,
        4.4,
        "This meal plan is for informational guidance and consistency support. Adjust portions with your clinician or dietitian if you have a medical condition, allergy, or performance-specific target.",
    )

    output = pdf.output()
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    return output.encode("latin1")
