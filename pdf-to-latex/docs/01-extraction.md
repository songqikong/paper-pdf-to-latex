# PDF Content Extraction Guide

## Overview

This document provides detailed guidance for extracting content from PDF academic papers using the `extract_pdf.py` script. The extraction process uses a hybrid approach combining PyMuPDF (fitz) for structural analysis and pdfplumber for text accuracy.

**MANDATORY**: Read this entire document before performing extraction. Understanding the extraction parameters is critical for successful conversion.

## Extraction Architecture

The extraction pipeline consists of multiple specialized extractors:

```
PDF Input
    │
    ├──► Text Extractor (pdfplumber) ─────► Structured text by sections
    │
    ├──► Image Extractor (PyMuPDF) ───────► figures/
    │
    ├──► Formula Detector (hybrid) ───────► formulas.json / formulas/
    │
    ├──► Table Extractor (pdfplumber) ────► tables.json
    │
    ├──► Metadata Extractor (PyMuPDF) ────► Title, authors, etc.
    │
    └──► Reference Extractor (text) ──────► References list
```

## Basic Usage

### Command Line Interface

```bash
python scripts/extract_pdf.py <input_pdf> [options]
```

**Required argument:**
- `input_pdf`: Path to the PDF file

**Optional arguments:**
- `-o, --output`: Output directory (default: `extracted/`)
- `--extract-formula-images`: Save formula regions as separate images
- `--start-page`: First page to extract (1-indexed)
- `--end-page`: Last page to extract
- `--dpi`: DPI for image extraction (default: 150)

### Basic Extraction Example

```bash
# Extract all content from paper.pdf to output/ directory
python scripts/extract_pdf.py paper.pdf -o output/

# Extract only first 5 pages
python scripts/extract_pdf.py paper.pdf -o output/ --end-page 5

# Extract with formula images for visual recognition
python scripts/extract_pdf.py paper.pdf -o output/ --extract-formula-images --dpi 200
```

## Extraction Methods Deep Dive

### Text Extraction Strategy

The script uses **pdfplumber** as the primary text extractor because it provides:
- Better character positioning information
- Preserved reading order
- Font metadata (size, name, flags)

**Text organization levels:**

1. **By Page**: Raw text per page with coordinates
   ```python
   {
     "page_number": 1,
     "text": "full page text...",
     "width": 612.0,
     "height": 792.0
   }
   ```

2. **By Section**: Hierarchically organized by headings
   ```python
   {
     "section_number": "1",
     "section_title": "Introduction",
     "level": 1,
     "content": "paragraph text...",
     "page_range": [1, 2]
   }
   ```

**Section detection heuristics:**
- Font size > 12pt and bold flags
- Numeric patterns: "1.", "1.1", "2.3.1"
- Common section keywords: "Introduction", "Related Work", "Method", "Experiments", "Conclusion"
- Position in first 1/3 of page for top-level sections

### Image Extraction

Images are extracted using PyMuPDF's image enumeration:

```python
# Extraction process
for page_num in range(len(pdf)):
    page = pdf[page_num]
    images = page.get_images()
    for img_index, img in enumerate(images):
        xref = img[0]
        pix = fitz.Pixmap(pdf, xref)
        # Save as PNG/JPEG based on image type
```

**Image naming convention:**
- Format: `fig_{page}_{index}.{ext}`
- Example: `fig_3_2.png` = Page 3, second image on that page

**Image filtering:**
- Images smaller than 50x50 pixels are skipped (likely icons)
- Vector graphics are rasterized at specified DPI
- Alpha channel handling for transparent images

### Formula Extraction

Formula detection uses multiple signals:

1. **Font-based detection**: Mathematical symbols (α, β, ∑, ∫) in text
2. **Position-based**: Display formulas often centered, between paragraphs
3. **Visual extraction**: Cropping image regions when `--extract-formula-images` is used

**Formula metadata:**
```python
{
  "formula_id": "eq_5_3",
  "page": 5,
  "type": "display",  # or "inline"
  "bbox": [100, 200, 400, 250],  # x0, y0, x1, y1
  "text": "E = mc^2",
  "image_path": "formulas/formula_5_3.png"  # if --extract-formula-images
}
```

**Best practices for formula extraction:**
- Always use `--extract-formula-images` for papers with complex math
- Set DPI ≥ 200 for clear formula recognition by LLM vision
- Verify extracted formula text against images manually for critical papers

### Table Extraction (Enhanced)

The enhanced table extractor handles both single-column and double-column layouts:

**Method 1: pdfplumber tables**
- Uses pdfplumber's built-in table detection
- Works well for bordered tables
- Returns cell coordinates and content

**Method 2: Text alignment detection (fallback)**
- Analyzes whitespace patterns
- Detects column alignment by character position
- Works for borderless tables

**Table output format:**
```python
{
  "table_id": "table_2",
  "page": 3,
  "bbox": [50, 100, 550, 300],
  "method": "pdfplumber",  # or "text_alignment"
  "num_rows": 5,
  "num_cols": 4,
  "data": [
    ["Header1", "Header2", "Header3", "Header4"],
    ["row1col1", "row1col2", "row1col3", "row1col4"],
    # ...
  ],
  "caption": "Table 2: Comparison results"
}
```

**Double-column handling:**
- Detects column layout by analyzing text block positions
- Applies different table detection thresholds per column
- Handles tables that span columns (rare but possible)

### Reference Extraction (Enhanced)

The enhanced reference extractor supports various bibliography layouts:

**Supported formats:**
- Numbered: `[1] Author. Title. Journal. Year.`
- Author-year: `Author (Year) Title...`
- Mixed layouts in double-column papers

**Filtering strategies:**
1. **Table row filtering**: Removes rows that look like table content (too short, numeric-heavy)
2. **Line grouping**: Merges wrapped reference lines
3. **Number pattern matching**: Identifies [1], [2] patterns

**Reference metadata:**
```python
{
  "reference_number": 1,
  "raw_text": "[1] Smith, J. et al. Title of paper. Conference 2023.",
  "type": "conference",  # or "journal", "book", etc.
  "authors": ["Smith, J.", "Doe, A."],
  "title": "Title of paper",
  "venue": "Conference",
  "year": 2023
}
```

**Double-column reference handling:**
- Detects column breaks in reference sections
- Merges references that span column breaks
- Maintains correct numbering order

### Citation Extraction

Extracts in-text citations for later mapping:

```python
{
  "citations": [
    {
      "number": 1,
      "context": "As shown in previous work [1], the approach...",
      "page": 2,
      "position": [100, 150]  # x, y on page
    }
  ]
}
```

This enables the `convert_references.py` script to replace `[1]` with `\cite{key}`.

## Output File Reference

### extracted_content.json

Main output file containing all extracted structured data:

```json
{
  "metadata": {
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "abstract": "Abstract text...",
    "keywords": ["keyword1", "keyword2"],
    "total_pages": 8
  },
  "sections": [
    {
      "number": "1",
      "title": "Introduction",
      "level": 1,
      "content": "...",
      "page_start": 1
    }
  ],
  "figures": [
    {
      "id": "fig_1_1",
      "page": 1,
      "path": "figures/fig_1_1.png",
      "width": 400,
      "height": 300
    }
  ],
  "formulas": [...],
  "tables": [...],
  "references": [...],
  "citations": [...]
}
```

## Extraction Parameters and Tuning

### For Conference Papers (CVPR/ICCV/NeurIPS)

```bash
python scripts/extract_pdf.py paper.pdf -o output/ \
  --extract-formula-images \
  --dpi 200 \
  --start-page 1
```

**Why these settings:**
- Conference papers have dense formulas requiring visual extraction
- 200 DPI ensures clear formula images for LLM recognition
- Full page range needed for references

### For Journal Papers

```bash
python scripts/extract_pdf.py paper.pdf -o output/ \
  --extract-formula-images \
  --dpi 150
```

**Differences from conference papers:**
- May have different reference formats
- Often single-column (simpler table extraction)

### For Documents with Poor Text Layer

Some PDFs have corrupted or missing text layers:

```bash
# First check text extractability
python scripts/extract_pdf.py paper.pdf -o output/ --check-text

# If garbled, use OCR preprocessing (requires Tesseract)
python scripts/extract_pdf.py paper.pdf -o output/ --ocr-fallback
```

## Common Issues and Solutions

### Issue: Missing sections in extraction

**Symptoms**: Section structure not detected, all text appears as one block

**Causes and solutions:**
1. **Non-standard fonts**: Section headings use unusual fonts
   - Solution: Adjust font size threshold in script
2. **No bold flag**: Headings not marked as bold in PDF metadata
   - Solution: Use position-based detection (top of page)
3. **Custom numbering**: Sections use "I.", "A.", etc. instead of "1."
   - Solution: Update regex patterns in section detection

### Issue: Formulas not detected

**Symptoms**: Math symbols appear as regular text or are missing

**Solutions:**
1. Enable visual extraction: `--extract-formula-images`
2. Post-process with LLM vision on formula regions
3. Manually review `formulas.json` against PDF

### Issue: Table content garbled

**Symptoms**: Table cells misaligned or merged incorrectly

**Solutions:**
1. Check `method` field in tables.json
2. If "text_alignment", try adjusting column detection threshold
3. For complex tables, use extracted bbox to crop manually

### Issue: References incomplete or wrong

**Symptoms**: Missing references, wrong order, table content mixed in

**Solutions:**
1. Check if references span multiple columns
2. Verify reference section detection (look for "References" heading)
3. Use `--strict-reference-filter` for cleaner extraction

## Performance Optimization

### For Large Documents (>50 pages)

```bash
# Process in chunks
python scripts/extract_pdf.py paper.pdf -o output/ --start-page 1 --end-page 25
python scripts/extract_pdf.py paper.pdf -o output/ --start-page 26 --end-page 50
# Merge JSON results manually
```

### Memory Considerations

- Image extraction is memory-intensive
- For papers with 100+ images, increase available RAM or process in batches
- Use `--low-memory` flag to process images one at a time (slower but stable)

## Verification Checklist

After extraction, verify:

- [ ] `extracted_content.json` exists and is valid JSON
- [ ] Metadata (title, authors) correctly extracted
- [ ] Section structure matches PDF outline
- [ ] Figure count matches PDF (check `figures/` directory)
- [ ] Formula regions look correct in `formulas/` (if using visual extraction)
- [ ] Table row/column counts reasonable
- [ ] Reference count matches PDF bibliography
- [ ] Citation numbers appear in extracted text

**Quick verification command:**
```bash
python -c "import json; d=json.load(open('output/extracted_content.json')); print(f\"Sections: {len(d['sections'])}, Figures: {len(d['figures'])}, References: {len(d['references'])}\")"
```
