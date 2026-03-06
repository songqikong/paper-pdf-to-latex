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

## Output Organization Convention

**CRITICAL**: Every decompiled paper must be saved in its own named subfolder to avoid overwriting previous results.

Given a PDF file `<name>.pdf` (e.g., `scpnet.pdf`), use `<name>` (without extension) as the folder name:

```
extracted_<name>/          # raw extraction output (JSON + figure images)
output/<name>/             # final LaTeX output
  ├── main.tex             # intermediate LaTeX with [N] citations
  ├── main_final.tex       # final LaTeX with \cite{key} citations
  ├── references.bib       # BibTeX bibliography
  └── figures/             # figure images copied from extraction
```

**Example** — for `scpnet.pdf`:
- Extraction goes to: `extracted_scpnet/`
- LaTeX output goes to: `output/scpnet/`

Never use generic names like `extracted/` or `output/` directly, as they will be overwritten by subsequent conversions.

## Basic extraction workflow

For simple documents with straightforward layout:

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`docs/01-extraction.md`](docs/01-extraction.md) (~390 lines) completely from start to finish. **NEVER set any range limits when reading this file.** This document contains critical extraction parameters and troubleshooting guidance.
2. Determine `<name>` from the PDF filename (strip the `.pdf` extension).
3. Run extraction script: `python pdf-to-latex/scripts/extract_pdf.py <input.pdf> -o extracted_<name>/`
4. Review extracted content in `extracted_<name>/extracted_content.json`
5. Use LLM to convert structured content to LaTeX (see conversion templates below)
6. Save output to `output/<name>/` using templates in `assets/latex_template/`

## Full conversion workflow

For academic papers with complex layouts, formulas, and references:

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`docs/01-extraction.md`](docs/01-extraction.md) completely for extraction parameters.
2. **MANDATORY - READ ENTIRE FILE**: Read [`docs/02-conversion.md`](docs/02-conversion.md) (~410 lines) for LLM conversion strategies and prompt templates.
3. Determine `<name>` from the PDF filename (strip the `.pdf` extension). Create output dirs: `mkdir -p extracted_<name> output/<name>`
4. Extract PDF content: `python pdf-to-latex/scripts/extract_pdf.py paper/<name>.pdf -o extracted_<name>/`
5. Generate BibTeX from references: `python pdf-to-latex/scripts/convert_references.py extracted_<name>/extracted_content.json -o extracted_<name>/references.bib`
6. Use LLM to convert main content following chunking strategy in `docs/02-conversion.md`; write output to `output/<name>/main.tex`. **Write \cite{} keys directly** in main.tex using the key mapping printed by step 5 (do NOT use [N] placeholders — see "Citation Mapping" section below).
7. Assemble and post-process following [`docs/03-post-processing.md`](docs/03-post-processing.md)
8. Copy figures and bib into output folder: `cp extracted_<name>/references.bib output/<name>/ && cp -r extracted_<name>/figures output/<name>/`

> **Removed step**: The `-t` tex-conversion flag of `convert_references.py` produces wrong citation mapping for two-column papers (see Known Issues). Write `\cite{key}` directly in main.tex instead.

## Formula-enhanced workflow

For documents with complex mathematical formulas requiring visual extraction:

### Workflow
1. Complete steps 1-2 from Full conversion workflow
2. Determine `<name>` and create dirs (step 3 above)
3. Extract PDF content: `python pdf-to-latex/scripts/extract_pdf.py paper/<name>.pdf -o extracted_<name>/`

   > **Note**: `--extract-formula-images` and `--dpi` flags are **not implemented** in the current script. Formula images cannot be extracted automatically. Use `text_by_page` content and LLM reasoning to reconstruct formulas manually.

4. **Use LLM reasoning** to reconstruct formulas from the extracted text in `text_by_page`, using surrounding context to infer correct LaTeX syntax.
5. Continue with steps 5-8 from Full conversion workflow

## Reference mapping workflow

When you have an existing BibTeX file and want to preserve citation keys:

### Workflow
1. Complete steps 1-2 from Full conversion workflow
2. Determine `<name>` and create dirs (step 3 above)
3. Extract PDF content: `python pdf-to-latex/scripts/extract_pdf.py paper/<name>.pdf -o extracted_<name>/`
4. Generate BibTeX mapping: `python pdf-to-latex/scripts/convert_references.py extracted_<name>/extracted_content.json -o extracted_<name>/references.bib`
5. The script prints a reference-number → BibTeX key mapping. Use this mapping to write `\cite{key}` directly in the LaTeX source.

> **Warning**: The `-b existing.bib -t main.tex` combination of `convert_references.py` remaps citations sequentially (ignoring reference numbers), producing wrong output for two-column papers. Always use the printed mapping and write `\cite{}` directly.

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
extracted_<name>/
├── extracted_content.json    # Main structured content — see JSON structure below
├── figures/                  # Extracted images
│   ├── fig_1_1.png          # Page 1, image 1
│   ├── fig_2_1.png
│   └── ...
└── references.bib            # Generated after running convert_references.py
```

> **Note**: `formulas.json`, `tables.json`, and `formulas/` are documented in `docs/01-extraction.md` but may **not** be produced by the current script version. Formulas and tables are embedded inside `extracted_content.json`.

### Actual JSON structure of `extracted_content.json`

The actual top-level keys differ from some older documentation:

```python
{
  "metadata": {
    "title": "...",
    "authors": None,       # often None — extract from page 1 text instead
    "total_pages": None    # often None
  },
  "text_by_page": [        # PRIMARY content source — list of per-page dicts
    {"page_num": 1, "text": "full page text..."},
    ...
  ],
  "text_by_sections": {    # UNRELIABLE — usually only {"abstract": "...", "references": "..."}
    "abstract": "...",
    "references": "..."
  },
  "images": [...],         # key is "images", NOT "figures"
  "tables": [...],
  "formulas": [...],
  "references": [          # list of dicts with keys "number" and "text"
    {"number": "1", "text": "raw reference text..."},
    ...
  ],
  "citations": [...]
}
```

**Key differences from docs:**
- Use `text_by_page` for full paper content — `text_by_sections` only reliably contains `abstract` and `references`
- Images key is `images`, not `figures`
- Reference items have `number` (str) and `text` keys, not `reference_number` / `raw_text`
- `authors` and `total_pages` in metadata are usually `None`; extract from page 1 text

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

### Principle: Output Organization
Each decompiled paper must go into its own named subfolder (see "Output Organization Convention" above). Never write to generic paths like `extracted/` or `output/` — always use `extracted_<name>/` and `output/<name>/` derived from the PDF filename.

### Principle: Citation Handling
Citation conversion workflow:
1. Run `convert_references.py ... -o references.bib` — the script prints a `[N] -> \cite{key}` mapping
2. Use that printed mapping to write `\cite{key}` **directly** in the LaTeX source during LLM conversion
3. Do **not** use the `-t` tex flag of `convert_references.py` for two-column papers — it remaps by list position, not by reference number, producing wrong keys (see Known Issues)

**Correct citation replacement script** (use when you already have a main.tex with `[N]` placeholders):

```python
import re

mapping = {  # fill from convert_references.py printed output
    '1': 'smith2023deep',
    '2': 'jones2022method',
    # ...
}

def replace_cite(m):
    keys = []
    for part in re.split(r',\s*', m.group(1)):
        part = part.strip()
        rng = re.match(r'(\d+)\s*[-–]\s*(\d+)', part)
        if rng:
            for n in range(int(rng.group(1)), int(rng.group(2))+1):
                keys.append(mapping.get(str(n), f'ref{n}'))
        else:
            keys.append(mapping.get(part, f'ref{part}'))
    return r'\cite{' + ','.join(keys) + '}'

with open('output/<name>/main.tex') as f:
    content = f.read()
content = re.sub(r'\[(\d+(?:[,\s–-]\d+)*)\](?!\s*{)', replace_cite, content)
with open('output/<name>/main.tex', 'w') as f:
    f.write(content)
```

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

## Reference Material

Additional LaTeX syntax reference for common academic paper elements:
- [`references/latex_guide.md`](references/latex_guide.md)

## Known Issues (discovered during real conversions)

### Issue: Script not found — wrong path
**Symptom**: `python: can't open file 'scripts/extract_pdf.py': No such file or directory`
**Cause**: SKILL.md previously used `python scripts/...` but scripts live under `pdf-to-latex/scripts/`
**Fix**: Always use `python pdf-to-latex/scripts/extract_pdf.py` from the workspace root

### Issue: `--extract-formula-images`, `--dpi`, `--ocr-fallback` flags not implemented
**Symptom**: `error: unrecognized arguments: --extract-formula-images --dpi 200`
**Cause**: The actual `extract_pdf.py` only supports `-o` (`--output`). Extended flags described in docs are not yet implemented.
**Fix**: Run extraction without those flags. Reconstruct formulas from extracted text using LLM reasoning.

### Issue: `convert_references.py -t` produces wrong citation mapping
**Symptom**: `[1] -> \cite{cchoy}` when [1] should map to a completely different paper
**Cause**: The `-t` (tex conversion) mode maps citations sequentially by list position (1st extracted ref → [1], 2nd → [2]), ignoring the actual `number` field stored in the JSON. For two-column papers, reference extraction is interleaved (left column and right column refs mixed), so list order ≠ citation number order.
**Fix**: Use the printed mapping from the `-o` (BibTeX generation) run, and replace `[N]` → `\cite{key}` manually with the Python script shown in "Principle: Citation Handling".

### Issue: `text_by_sections` only extracts `abstract` and `references`
**Symptom**: `text_by_sections` dict has only two keys; all body sections are missing
**Cause**: Section heading detection heuristics fail for most conference/journal paper fonts
**Fix**: Use `text_by_page` as the primary content source. Parse section boundaries from page text manually.

### Issue: Two-column text extraction is interleaved
**Symptom**: Left-column and right-column text is mixed within the same page string
**Cause**: PDF text extraction reads characters in PDF order, not visual reading order, for two-column layouts
**Impact**: Some sentences appear mid-paragraph from the opposite column; formula variables may appear in wrong positions
**Fix**: Use LLM judgment to reconstruct logical reading order. Focus on meaning rather than raw string order.

### Issue: Hundreds of tiny images extracted from complex figures
**Symptom**: `extracted_<name>/figures/` contains 100+ images, most 9×16 or 15×32 pixels
**Cause**: Some PDF figures are composed of many individual vector/raster elements that each get extracted separately
**Fix**: When referencing figure images, only use images with reasonable dimensions (typically > 200px in both dimensions). Skip tiny sub-elements. Use `data['images']` filtering:
```python
large_imgs = [im for im in data['images'] if im['width'] > 200 and im['height'] > 200]
```

### Issue: `metadata.authors` and `metadata.total_pages` are None
**Symptom**: `data['metadata']['authors']` is `None`
**Cause**: Author extraction is not reliably implemented
**Fix**: Extract title and authors from `text_by_page[0]['text']` (page 1 content)

## Troubleshooting

### Issue: Garbled text extraction
**Cause**: PDF uses custom font encoding without ToUnicode map
**Solution**: No automatic fix currently (OCR fallback not implemented). Try processing individual pages and using LLM to correct obvious garbling.

### Issue: Missing formulas
**Cause**: Formulas rendered as images or embedded as vector paths
**Solution**: `--extract-formula-images` flag is not implemented. Reconstruct formulas by reading the `text` field in `extracted_content.json['formulas']` and using surrounding paragraph context. For complex formulas, view the original PDF directly.

### Issue: Table extraction errors
**Cause**: Complex table layouts or merged cells
**Solution**: Manual correction using table data in `extracted_content.json['tables']`

### Issue: Wrong citation mapping
**Cause**: `convert_references.py -t` uses sequential position, not reference numbers (see Known Issues above)
**Solution**: Use the manual Python citation replacement script from "Principle: Citation Handling"

## Version History

### v1.3.0 (Current)
- **Fixed script paths**: all commands now use `pdf-to-latex/scripts/` prefix
- **Removed unsupported flags**: `--extract-formula-images`, `--dpi`, `--ocr-fallback` removed from workflow commands (not implemented in script)
- **Fixed citation workflow**: replaced broken `-t` tex-flag approach with direct `\cite{key}` writing + manual Python replacement script
- **Updated JSON structure docs**: corrected key names (`text_by_page`, `images`, `references[].number/.text`); noted that `text_by_sections` is unreliable
- **Added Known Issues section**: 7 real issues discovered during conversions of `diffssc.pdf` (IROS 2025, two-column) and `dtt.pdf` (arXiv preprint, single-column)
- **Removed obsolete step 5** (`convert_formula.py`) from Full conversion workflow
- **Improved Troubleshooting** to reflect actual script limitations

### v1.2.0
- Added "Output Organization Convention": each paper gets its own `extracted_<name>/` + `output/<name>/` folder
- Added "Principle: Output Organization" to Critical Principles
- Updated all workflow commands to use `<name>`-based paths

### v1.1.0
- Fixed formulas output structure (formulas.json is metadata file; formula images go in formulas/ directory)
- Added references/latex_guide.md to documentation
- Corrected doc line count estimates

### v1.0.0
- Restructured documentation following docx skill patterns
- Added comprehensive workflow decision tree
- Separated detailed guides into docs/ directory
- Enhanced chunking and batching strategies
- Improved cross-reference preservation guidance
