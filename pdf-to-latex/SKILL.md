---
name: pdf-to-latex
description: "Convert PDF academic papers to LaTeX source code with support for text extraction, mathematical formulas, tables, figures, and references. Use when users need to: (1) Convert PDF papers to LaTeX format, (2) Extract content from academic papers for recompilation, (3) Reverse engineer PDF documents to editable LaTeX, (4) Convert CVPR/ICCV conference papers to tex source"
---

# PDF to LaTeX Conversion

## Overview

This skill enables decompilation of PDF academic papers into structured LaTeX source code. A PDF file contains rendered content that must be reverse-engineered back into semantic LaTeX markup. Different workflows are available depending on the document complexity and content types.

**Supported content types:**
- Text content with section structure
- Mathematical formulas (inline and display)
- Tables with complex layouts
- Figures and images
- References and citations
- Two-column layouts (common in conference papers)

## Workflow Decision Tree

### Simple Document (Single-column, No Complex Formulas)
Use "Basic extraction workflow" with minimal post-processing

### Conference Paper (CVPR/ICCV/NeurIPS style)
Use "Full conversion workflow" with all processing steps

### Formula-Heavy Document
Use "Formula-enhanced workflow" with visual formula extraction

### Document with Existing BibTeX
Use "Reference mapping workflow" to preserve citation keys

## Basic extraction workflow

For simple documents with straightforward layout:

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`docs/01-extraction.md`](docs/01-extraction.md) (~500 lines) completely from start to finish. **NEVER set any range limits when reading this file.** This document contains critical extraction parameters and troubleshooting guidance.
2. Run extraction script: `python scripts/extract_pdf.py <input.pdf> -o output/`
3. Review extracted content in `output/extracted_content.json`
4. Use LLM to convert structured content to LaTeX (see conversion templates below)
5. Assemble final document using templates in `assets/latex_template/`

## Full conversion workflow

For academic papers with complex layouts, formulas, and references:

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`docs/01-extraction.md`](docs/01-extraction.md) completely for extraction parameters.
2. **MANDATORY - READ ENTIRE FILE**: Read [`docs/02-conversion.md`](docs/02-conversion.md) (~400 lines) for LLM conversion strategies and prompt templates.
3. Extract PDF content: `python scripts/extract_pdf.py paper.pdf -o extracted/`
4. Convert formulas if needed: `python scripts/convert_formula.py extracted/formulas.json`
5. Generate BibTeX from references: `python scripts/convert_references.py extracted/extracted_content.json -o references.bib`
6. Use LLM to convert main content following chunking strategy in docs/02-conversion.md
7. Assemble and post-process following [`docs/03-post-processing.md`](docs/03-post-processing.md)
8. Convert citation numbers to \cite{} commands: `python scripts/convert_references.py extracted/extracted_content.json -t main.tex --output-tex final.tex -b references.bib`

## Formula-enhanced workflow

For documents with complex mathematical formulas requiring visual extraction:

### Workflow
1. Complete steps 1-2 from Full conversion workflow
2. Extract with formula images: `python scripts/extract_pdf.py paper.pdf -o extracted/ --extract-formula-images`
3. **Use LLM vision capability**: Feed formula images to GPT-4V/Claude 3 for recognition
4. Cross-reference with formula text extraction for accuracy
5. Continue with steps 5-8 from Full conversion workflow

## Reference mapping workflow

When you have an existing BibTeX file and want to preserve citation keys:

### Workflow
1. Complete steps 1-2 from Full conversion workflow
2. Extract PDF content: `python scripts/extract_pdf.py paper.pdf -o extracted/`
3. Use existing BibTeX: `python scripts/convert_references.py extracted/extracted_content.json -b existing.bib -t main.tex --output-tex final.tex`
4. This maps [1], [2] citations to their corresponding BibTeX keys automatically

## Quick conversion templates

### Template for LLM conversion prompt

```
You are an expert LaTeX typesetter. Convert the following academic paper content to LaTeX source code.

Paper Title: {title}
Authors: {authors}

Abstract:
{abstract_text}

Requirements:
1. Use article document class with appropriate packages (amsmath, graphicx, booktabs)
2. Convert all mathematical formulas using proper LaTeX math environments
3. Use \begin{{table}} for tables with booktabs rules (\toprule, \midrule, \bottomrule)
4. Include figures with \includegraphics and appropriate widths
5. Preserve all section and subsection structure
6. Add \label{{}} to equations, tables, and figures for cross-referencing
7. Use \cite{{}} for citations (will be resolved later)

Content to convert:
{section_content}

Output only the LaTeX code without markdown code blocks.
```

### Template for formula conversion

```
Convert this mathematical formula to LaTeX syntax:

Formula: {formula_text}
Context: {surrounding_text}

Requirements:
1. Use appropriate math environment ($...$ for inline, \[...\] or equation for display)
2. Use \alpha, \beta for Greek letters (not Unicode)
3. Use \mathbf{{}}, \mathcal{{}} for special fonts
4. For multi-line equations, use align or align* environment
5. Ensure proper spacing with \, \: \; where needed

Output only the LaTeX code.
```

## Extraction Output Structure

After running extraction, the output directory contains:

```
output/
├── extracted_content.json    # Main structured content (text, sections, metadata)
├── figures/                  # Extracted images
│   ├── fig_1_1.png          # Page 1, image 1
│   ├── fig_2_1.png
│   └── ...
├── formulas.json            # Extracted formulas (if --extract-formula-images)
│   ├── formula_1.png
│   └── ...
└── tables.json              # Table data in structured format
```

## Chunking Strategy for Large Documents

**CRITICAL**: When converting large papers, chunk content intelligently:

**Batch by section** (recommended):
- Batch 1: Title, authors, abstract
- Batch 2: Introduction
- Batch 3: Related Work
- Batch 4: Method/Approach
- Batch 5: Experiments/Results
- Batch 6: Conclusion and references

**Batch size limits:**
- Maximum 3000 tokens per chunk for GPT-4
- Maximum 5000 tokens per chunk for Claude 3
- Include section context (parent section title) with each chunk

**Cross-reference preservation:**
- Maintain figure numbers across chunks: fig_1_1, fig_2_1, etc.
- Preserve equation numbers or use \label{eq:section_name}
- Note citation numbers for later \cite{} conversion

## Critical Principles

### Principle: Verify Formula Accuracy
Mathematical formulas are the most error-prone part of conversion. Always:
- Cross-check complex formulas against PDF images
- Use visual LLM for ambiguous symbols
- Test compile critical equations

### Principle: Preserve Document Structure
Maintain semantic structure over visual fidelity:
- Keep section hierarchy (\section, \subsection)
- Preserve list structures (itemize, enumerate)
- Maintain table of contents structure

### Principle: Citation Handling
Citation conversion is two-stage:
1. Keep [1], [2] markers in initial conversion
2. Use convert_references.py to map to \cite{key} after BibTeX generation

## Code Style Guidelines

**IMPORTANT**: When generating code for PDF-to-LaTeX operations:
- Write concise, focused scripts
- Use descriptive variable names for clarity
- Include error handling for file operations
- Log progress for long-running extractions

## Dependencies

Required dependencies (install before use):

```bash
# Python packages
pip install -r requirements.txt

# Core dependencies:
# - PyMuPDF (fitz) - PDF parsing and image extraction
# - pdfplumber - Text and table extraction
# - Pillow - Image processing
# - numpy - Array operations for table detection
```

## Troubleshooting

### Issue: Garbled text extraction
**Cause**: PDF uses custom font encoding without ToUnicode map
**Solution**: Use `--ocr-fallback` flag or preprocess with OCR

### Issue: Missing formulas
**Cause**: Formulas rendered as images or vector graphics
**Solution**: Use `--extract-formula-images` and visual LLM recognition

### Issue: Table extraction errors
**Cause**: Complex table layouts or merged cells
**Solution**: Manual correction using extracted table JSON as reference

### Issue: Wrong citation mapping
**Cause**: References extracted out of order
**Solution**: Verify `extracted_content.json` reference order matches PDF

## Version History

### v1.0.0 (Current)
- Restructured documentation following docx skill patterns
- Added comprehensive workflow decision tree
- Separated detailed guides into docs/ directory
- Enhanced chunking and batching strategies
- Improved cross-reference preservation guidance
