"""PDF export utilities."""

from __future__ import annotations

from datetime import datetime, timezone
import textwrap


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
        return _build_minimal_pdf(lines)

    class MealPlanPDF(FPDF):
        def footer(self) -> None:
            self.set_y(-10)
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(120, 120, 120)
            self.cell(
                0,
                8,
                f"NutriAI Meal Plan | Page {self.page_no()}",
                align="C",
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
            )

    pdf = MealPlanPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_fill_color(76, 105, 113)
    pdf.rect(10, 10, 190, 18, style="F")

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 12)
    pdf.cell(190, 10, "NutriAI Personalized Meal Plan", align="C")

    pdf.ln(20)
    pdf.set_text_color(35, 35, 35)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(
        0,
        8,
        f"Generated for: {_normalize_pdf_value(full_name)} (Age {age})",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.cell(
        0,
        8,
        f"Date: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    for key, value in profile.items():
        pdf.cell(
            0,
            8,
            f"{_normalize_pdf_value(key)}: {_normalize_pdf_value(value)}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    pdf.ln(4)
    for section in sections:
        name = _normalize_pdf_value(section.get("name", "Section"))
        options = section.get("options", [])

        pdf.set_fill_color(244, 171, 79)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, name, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("Helvetica", "", 11)
        if isinstance(options, list):
            for option in options:
                safe_option = _normalize_pdf_value(option)
                wrapped = textwrap.wrap(
                    f"- {safe_option}",
                    width=78,
                    break_long_words=True,
                    break_on_hyphens=False,
                )
                for row in wrapped or ["-"]:
                    pdf.cell(0, 7, row, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(1)

    output = pdf.output()
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    return output.encode("latin1")
