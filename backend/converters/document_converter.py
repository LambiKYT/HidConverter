import os
from typing import Dict, List

from .base import BaseConverter


try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from weasyprint import HTML
except ImportError:
    HTML = None

try:
    import openpyxl
except ImportError:
    openpyxl = None


class DocumentConverter(BaseConverter):
    SUPPORTED = {
        "pdf":  ["docx", "txt"],
        "docx": ["pdf"],
        "txt":  ["pdf"],
        "md":   ["pdf"],
        "xlsx": ["csv", "pdf"],
    }

    def supported_conversions(self) -> Dict[str, List[str]]:
        return self.SUPPORTED

    def convert(self, file_path: str, target_format: str, output_dir: str) -> str:
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        if ext not in self.SUPPORTED or target_format not in self.SUPPORTED[ext]:
            raise ValueError(f"Conversion from {ext} to {target_format} is not supported")

        output_path = self.get_output_path(file_path, target_format, output_dir)
        func_name = f"_convert_{ext}_to_{target_format}"
        handler = getattr(self, func_name, None)
        if not handler:
            raise ValueError(f"No handler for {ext} -> {target_format}")

        return handler(file_path, output_path)

    # --- PDF -> DOCX ---
    def _convert_pdf_to_docx(self, file_path: str, output_path: str) -> str:
        if pdfplumber is None or DocxDocument is None:
            raise RuntimeError("Missing dependencies: pdfplumber or python-docx")

        doc = DocxDocument()
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                doc.add_paragraph(text)
        doc.save(output_path)
        return output_path

    # --- PDF -> TXT ---
    def _convert_pdf_to_txt(self, file_path: str, output_path: str) -> str:
        if pdfplumber is None:
            raise RuntimeError("Missing dependency: pdfplumber")

        with pdfplumber.open(file_path) as pdf:
            text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return output_path

    # --- DOCX -> PDF ---
    def _convert_docx_to_pdf(self, file_path: str, output_path: str) -> str:
        if HTML is None:
            raise RuntimeError("Missing dependency: weasyprint")
        if DocxDocument is None:
            raise RuntimeError("Missing dependency: python-docx")

        doc = DocxDocument(file_path)
        html_parts = ["<html><body>"]
        for p in doc.paragraphs:
            html_parts.append(f"<p>{p.text}</p>")
        html_parts.append("</body></html>")
        HTML(string="\n".join(html_parts)).write_pdf(output_path)
        return output_path

    # --- TXT -> PDF ---
    def _convert_txt_to_pdf(self, file_path: str, output_path: str) -> str:
        if HTML is None:
            raise RuntimeError("Missing dependency: weasyprint")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        html = f"<html><body><pre>{text}</pre></body></html>"
        HTML(string=html).write_pdf(output_path)
        return output_path

    # --- MD -> PDF ---
    def _convert_md_to_pdf(self, file_path: str, output_path: str) -> str:
        if HTML is None:
            raise RuntimeError("Missing dependency: weasyprint")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        import markdown
        body = markdown.markdown(text)
        html = f"<html><body>{body}</body></html>"
        HTML(string=html).write_pdf(output_path)
        return output_path

    # --- XLSX -> CSV ---
    def _convert_xlsx_to_csv(self, file_path: str, output_path: str) -> str:
        if openpyxl is None:
            raise RuntimeError("Missing dependency: openpyxl")

        import csv
        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb.active
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in ws.iter_rows(values_only=True):
                writer.writerow(row)
        return output_path

    # --- XLSX -> PDF ---
    def _convert_xlsx_to_pdf(self, file_path: str, output_path: str) -> str:
        if openpyxl is None:
            raise RuntimeError("Missing dependency: openpyxl")
        if HTML is None:
            raise RuntimeError("Missing dependency: weasyprint")

        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb.active
        html_parts = ["<html><body><table border='1'>"]
        for row in ws.iter_rows(values_only=True):
            html_parts.append("<tr>" + "".join(f"<td>{cell or ''}</td>" for cell in row) + "</tr>")
        html_parts.append("</table></body></html>")
        HTML(string="\n".join(html_parts)).write_pdf(output_path)
        return output_path
