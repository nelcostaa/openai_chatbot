#!/usr/bin/env python3
"""
PDF to Markdown Converter

Extracts text content from PDF files and converts them to Markdown format.
Preserves basic structure including headings, paragraphs, and formatting.
"""

import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is not installed.")
    print("Please install it using: pip install pdfplumber")
    sys.exit(1)


def clean_text(text):
    """Clean and normalize extracted text."""
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def detect_heading(text, font_size=None, is_bold=None):
    """
    Detect if a line of text is likely a heading based on various heuristics.
    """
    if not text:
        return 0

    text = text.strip()

    # Check for short lines that might be headings (typically < 80 chars)
    if len(text) < 80:
        # All caps might indicate a heading
        if text.isupper() and len(text.split()) <= 10:
            return 2

        # Lines ending with colon might be headings
        if text.endswith(":") and len(text.split()) <= 8:
            return 3

        # Short lines at the start might be headings
        if len(text.split()) <= 6 and not text.endswith((".", ",", ";")):
            return 3

    return 0


def pdf_to_markdown(pdf_path, output_path=None):
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Path to the output Markdown file (optional)

    Returns:
        str: The Markdown content
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if output_path is None:
        output_path = pdf_path.with_suffix(".md")
    else:
        output_path = Path(output_path)

    markdown_content = []
    markdown_content.append(f"# {pdf_path.stem}\n")
    markdown_content.append(f"*Extracted from: {pdf_path.name}*\n")
    markdown_content.append("---\n")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Processing {total_pages} pages...")

            for page_num, page in enumerate(pdf.pages, 1):
                print(f"  Processing page {page_num}/{total_pages}...", end="\r")

                # Add page marker for reference
                if page_num > 1:
                    markdown_content.append(f"\n---\n**Page {page_num}**\n")

                # Extract text from the page
                text = page.extract_text()

                if text:
                    # Split into lines and process
                    lines = text.split("\n")

                    for line in lines:
                        cleaned_line = clean_text(line)

                        if not cleaned_line:
                            markdown_content.append("")
                            continue

                        # Detect if line is a heading
                        heading_level = detect_heading(cleaned_line)

                        if heading_level > 0:
                            markdown_content.append(
                                f"\n{'#' * heading_level} {cleaned_line}\n"
                            )
                        else:
                            markdown_content.append(cleaned_line)

                    markdown_content.append("")

                # Extract tables if any
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        markdown_content.append("\n")
                        # Convert table to markdown format
                        for i, row in enumerate(table):
                            if row:
                                # Clean cells
                                cleaned_row = [
                                    clean_text(str(cell)) if cell else ""
                                    for cell in row
                                ]
                                markdown_content.append(
                                    "| " + " | ".join(cleaned_row) + " |"
                                )

                                # Add header separator after first row
                                if i == 0:
                                    markdown_content.append(
                                        "| "
                                        + " | ".join(["---"] * len(cleaned_row))
                                        + " |"
                                    )
                        markdown_content.append("")

            print(f"\n✓ Successfully processed {total_pages} pages")

    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

    # Join all content
    final_markdown = "\n".join(markdown_content)

    # Clean up excessive blank lines
    final_markdown = re.sub(r"\n{3,}", "\n\n", final_markdown)

    # Write to output file
    output_path.write_text(final_markdown, encoding="utf-8")
    print(f"✓ Markdown file saved to: {output_path}")

    return final_markdown


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_markdown.py <pdf_file> [output_file]")
        print("\nExample:")
        print("  python pdf_to_markdown.py document.pdf")
        print("  python pdf_to_markdown.py document.pdf output.md")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        pdf_to_markdown(pdf_path, output_path)
        print("\n✓ Conversion completed successfully!")
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
