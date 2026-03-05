# Post-Processing Guide

## Overview

This document covers the final stages of PDF-to-LaTeX conversion: reference handling, citation mapping, figure optimization, and document assembly. These steps transform raw LLM output into a complete, compilable academic paper.

**MANDATORY**: Read this entire document before post-processing. Reference conversion and citation mapping require careful handling to maintain accuracy.

## Post-Processing Pipeline

```
LaTeX Source (from LLM)
         │
    ┌────┴────┬─────────────┬──────────────┐
    │         │             │              │
    ▼         ▼             ▼              ▼
References  Citations    Figures      Final Assembly
   │            │            │               │
   ▼            ▼            ▼               ▼
BibTeX    \cite{} refs   Optimized    Compilable
(.bib)    in .tex        images       Document
   │            │            │               │
   └────────────┴────────────┴───────────────┘
                   │
                   ▼
              Final Output
         (main.tex + references.bib + figures/)
```

## Step 1: Reference Conversion

### Generating BibTeX from Extracted References

Convert the extracted references to BibTeX format:

```bash
python scripts/convert_references.py extracted/extracted_content.json -o references.bib
```

This command:
1. Parses each reference from `extracted_content.json`
2. Identifies reference type (article, inproceedings, book, etc.)
3. Extracts fields: author, title, year, venue, pages, etc.
4. Generates BibTeX citation keys
5. Outputs formatted `references.bib` file

### BibTeX Entry Format

Generated entries follow standard BibTeX conventions:

```bibtex
@inproceedings{smith2023title,
  title={Title of the Paper},
  author={Smith, John and Doe, Jane},
  booktitle={Proceedings of Conference Name},
  pages={123--130},
  year={2023},
  organization={Publisher}
}

@article{johnson2022method,
  title={A New Method for Something},
  author={Johnson, Alice},
  journal={Journal Name},
  volume={15},
  number={3},
  pages={100--115},
  year={2022},
  publisher={Publisher}
}
```

### Citation Key Generation Rules

Keys follow format: `{lastname}{year}{firstword}`

Examples:
- Smith et al., "Deep Learning Methods", 2023 → `smith2023deep`
- Johnson, "A Survey of AI", 2022 → `johnson2022survey`

**Collision handling:**
- If duplicate keys: append letter `smith2023deepa`, `smith2023deepb`
- Configurable via `--key-format` option

### Using Existing BibTeX Files

If you have an existing BibTeX file (e.g., from conference website):

```bash
python scripts/convert_references.py extracted/extracted_content.json \
  -b existing.bib \
  -t main.tex \
  --output-tex main_cited.tex
```

This creates a mapping between `[N]` citations in the text and keys in `existing.bib`.

### Reference Verification Checklist

After generating references.bib:

- [ ] Entry count matches PDF reference list
- [ ] All required fields present (title, author, year)
- [ ] Author names properly formatted (Last, First and Last2, First2)
- [ ] Special characters properly escaped ({\"o} for ö, etc.)
- [ ] Page ranges use double hyphen (`--`)

## Step 2: Citation Mapping

### Converting [N] to \cite{key}

Replace numeric citations with BibTeX citations:

```bash
# Basic conversion using generated references
python scripts/convert_references.py extracted/extracted_content.json \
  -t main.tex \
  --output-tex main_final.tex

# Using existing BibTeX file
python scripts/convert_references.py extracted/extracted_content.json \
  -t main.tex \
  --output-tex main_final.tex \
  -b references.bib
```

### Citation Format Handling

The script handles various citation styles:

| Input Pattern | Output |
|--------------|--------|
| `[1]` | `\cite{key1}` |
| `[1, 2]` | `\cite{key1,key2}` |
| `[1-3]` | `\cite{key1,key2,key3}` |
| `[1, 3-5]` | `\cite{key1,key3,key4,key5}` |

### Manual Citation Review

Always review citations in the final document:

```bash
# Find all citations in the document
grep -n "\\cite{" main_final.tex

# Check for unconverted citations
grep -n "\[ *[0-9]" main_final.tex
```

### Citation Package Options

Add to preamble based on needs:

```latex
% Basic citations
\usepackage{cite}

% Author-year citations
\usepackage[numbers]{natbib}

% Advanced citations with compression
\usepackage[style=numeric,compress]{biblatex}
\addbibresource{references.bib}
```

## Step 3: Figure Optimization

### Image Format Conversion

Convert extracted figures to optimal formats:

```bash
# Convert PNG to PDF for vector quality
for img in figures/*.png; do
  convert "$img" "${img%.png}.pdf"
done

# Update figure paths in LaTeX
sed -i 's/\.png/.pdf/g' main.tex
```

### Image Size Optimization

Check and adjust figure sizes:

```bash
# Check image dimensions
identify figures/*.png

# Resize oversized images
convert figures/fig_1_1.png -resize 1200x figures/fig_1_1.png
```

### Figure Inclusion Best Practices

In LaTeX document:

```latex
% Standard figure
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/fig_1_1}
  \caption{Description of the figure content.}
  \label{fig:method_overview}
\end{figure}

% Subfigures (requires subcaption package)
\usepackage{subcaption}

\begin{figure}[htbp]
  \centering
  \begin{subfigure}[b]{0.48\textwidth}
    \includegraphics[width=\textwidth]{figures/fig_2_1}
    \caption{First subfigure.}
    \label{fig:sub1}
  \end{subfigure}
  \hfill
  \begin{subfigure}[b]{0.48\textwidth}
    \includegraphics[width=\textwidth]{figures/fig_2_2}
    \caption{Second subfigure.}
    \label{fig:sub2}
  \end{subfigure}
  \caption{Overall figure caption.}
  \label{fig:comparison}
\end{figure}
```

## Step 4: Document Assembly

### Template Integration

Assemble the final document using a template:

```latex
% main.tex structure
\documentclass[10pt,a4paper]{article}

% Packages
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}
\usepackage{cite}

% Document info
\title{Paper Title}
\author{Author Names}
\date{}

\begin{document}

\maketitle

\begin{abstract}
Abstract text...
\end{abstract}

\section{Introduction}
% ... LLM converted content ...

\bibliographystyle{plain}
\bibliography{references}

\end{document}
```

### Preamble Customization

Add paper-specific configurations:

```latex
% Math operators
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}

% Custom commands
\newcommand{\methodname}{\textsc{OurMethod}}
\newcommand{\dataset}{\textsc{Dataset}}

% Hyperref setup
\hypersetup{
  colorlinks=true,
  linkcolor=blue,
  citecolor=blue,
  urlcolor=magenta
}

% Line spacing
\usepackage{setspace}
\onehalfspacing
```

## Step 5: Compilation and Verification

### Compilation Sequence

```bash
# Standard compilation
cd output/
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex  # Second pass for references

# Or use latexmk for automatic handling
latexmk -pdf main.tex
```

### Error Resolution

Common post-processing errors:

**"Citation `key' on page N undefined"**
- Cause: BibTeX entry missing or misspelled key
- Fix: Check `references.bib` for the entry; verify key spelling

**"File `figures/fig_X_X' not found"**
- Cause: Figure path incorrect or file missing
- Fix: Check figure directory; update path in LaTeX

**"Overfull \hbox" in tables**
- Cause: Table content too wide
- Fix: Use `p{width}` column type; reduce font size with `\small`

**"Undefined control sequence" for math symbols**
- Cause: Missing package or typo
- Fix: Add `amssymb` package; check symbol spelling

### Verification Checklist

Before declaring conversion complete:

- [ ] Document compiles without errors
- [ ] All citations resolved (no [?] in output)
- [ ] All figures display correctly
- [ ] All tables formatted properly
- [ ] References match PDF bibliography
- [ ] Page count roughly matches original
- [ ] Section structure preserved
- [ ] Math formulas render correctly

## Advanced Post-Processing

### Automated Quality Checks

Create a verification script:

```bash
#!/bin/bash
# verify.sh

echo "=== Verification Report ==="

# Check for unconverted citations
echo "Unconverted citations:"
grep -n "\[ *[0-9]" main.tex || echo "  None found ✓"

# Check for unresolved references
echo "Compilation warnings:"
pdflatex -interaction=nonstopmode main.tex 2>&1 | grep -i "warning" || echo "  No warnings ✓"

# Count elements
echo "Document stats:"
echo "  Sections: $(grep -c "\\section{" main.tex)"
echo "  Figures: $(grep -c "\\begin{figure}" main.tex)"
echo "  Tables: $(grep -c "\\begin{table}" main.tex)"
echo "  Citations: $(grep -o "\\cite{[^}]*}" main.tex | wc -l)"
```

### Template-Specific Adjustments

#### IEEEtran Template

```latex
\documentclass[conference]{IEEEtran}

% IEEE specific
\IEEEoverridecommandlockouts
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}

\begin{document}

\title{Paper Title}

\author{
  \IEEEauthorblockN{Author One}
  \IEEEauthorblockA{Institution \\ Email}
  \and
  \IEEEauthorblockN{Author Two}
  \IEEEauthorblockA{Institution \\ Email}
}

\maketitle

\begin{abstract}
...
\end{abstract}

\IEEEpeerreviewmaketitle

\section{Introduction}
...

\bibliographystyle{IEEEtran}
\bibliography{references}

\end{document}
```

#### CVPR Template

```latex
\documentclass[10pt,twocolumn,letterpaper]{article}

\usepackage{cvpr}
\usepackage{times}
\usepackage{epsfig}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}

\cvprfinalcopy

\def\cvprPaperID{****}
\def\httilde{\mbox{\tt\raisebox{-.5ex}{\symbol{126}}}}

\begin{document}

\title{Paper Title}

\author{Authors}

\maketitle

\begin{abstract}
...
\end{abstract}

\section{Introduction}
...

{\small
\bibliographystyle{ieee_fullname}
\bibliography{references}
}

\end{document}
```

## Final Output Structure

The completed conversion should have this structure:

```
output/
├── main.tex              # Main LaTeX document
├── references.bib        # BibTeX bibliography
├── figures/              # Figure images
│   ├── fig_1_1.pdf
│   ├── fig_1_2.pdf
│   └── ...
├── main.pdf              # Compiled output
└── cvpr.sty              # Template style files (if needed)
```

## Troubleshooting Post-Processing Issues

### Issue: Citation numbers don't match original

**Cause**: References extracted in wrong order
**Solution**:
```bash
# Manually edit extracted_content.json to reorder
# Or use --reference-offset to adjust numbering
```

### Issue: Bibliography style doesn't match target venue

**Solution**:
```bash
# Download correct .bst file
wget https://example.com/venue_template.bst -O venue.bst

# Update document
# \bibliographystyle{venue}
```

### Issue: Figures too low resolution

**Solution**:
```bash
# Re-extract with higher DPI
python scripts/extract_pdf.py paper.pdf -o output/ --dpi 300
```

## Post-Processing Summary

```
1. Generate BibTeX from extracted references
2. Convert [N] citations to \cite{key}
3. Optimize figure formats and sizes
4. Assemble complete document with template
5. Compile and resolve errors
6. Verify against original PDF
7. Deliver final output package
```
