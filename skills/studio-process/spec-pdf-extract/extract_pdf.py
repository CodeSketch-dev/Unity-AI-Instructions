"""Extract text and embedded images from a spec PDF (e.g. a Google Sheet exported as PDF with DEMO screenshots).

Usage:  python -I extract_pdf.py <pdf> <out_dir>
Writes  <out_dir>/text.txt  and  <out_dir>/p<page>_<n>_<name>.png  (then open the images with the Read tool).
Needs:  pip install --user pypdf pillow   (the Read tool cannot render PDFs without poppler/pdftoppm).
"""
import os
import sys

import pypdf


def main(pdf_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    reader = pypdf.PdfReader(pdf_path)
    text_parts, count = [], 0
    for page_index, page in enumerate(reader.pages, 1):
        text_parts.append(f"===== page {page_index} =====\n{page.extract_text()}\n")
        for image in page.images:
            count += 1
            path = os.path.join(out_dir, f"p{page_index}_{count}_{image.name}")
            with open(path, "wb") as handle:
                handle.write(image.data)
            print("image", path)
    with open(os.path.join(out_dir, "text.txt"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(text_parts))
    print(f"pages={len(reader.pages)} images={count}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
