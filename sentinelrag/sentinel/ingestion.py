from __future__ import annotations

import io

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extracts plain text from an uploaded file so it can be stored as a
    document's content. Deliberately simple for this phase -- no chunking,
    no OCR. A real company's documents will be far larger than the test
    fixtures; chunking for retrieval-at-scale is a Phase 3 (RAG) concern,
    not this one."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in (".txt", ".md"):
        return file_bytes.decode("utf-8", errors="replace")

    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".docx":
        import docx

        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs)

    raise ValueError(
        f"Unsupported file type '{ext or filename}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )
