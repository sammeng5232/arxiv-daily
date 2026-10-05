#!/usr/bin/env python3
"""Extract text from a PDF. Usage: extract_text.py in.pdf out.txt
Prints OK <nchars> on success (writes text file), or EMPTY if no text layer."""
import sys

from pypdf import PdfReader


def main():
    src, dst = sys.argv[1], sys.argv[2]
    reader = PdfReader(src)
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    text = "\n".join(parts)
    with open(dst, "w", encoding="utf-8", errors="replace") as f:
        f.write(text)
    n = len(text.strip())
    print(f"OK {n}" if n > 500 else "EMPTY")


if __name__ == "__main__":
    main()
