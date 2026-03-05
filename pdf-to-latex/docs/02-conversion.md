# LLM Conversion Guide

## Overview

This document provides comprehensive guidance for converting extracted PDF content to LaTeX using Large Language Models. The conversion process is the core transformation step where structured content becomes compilable LaTeX source.

**MANDATORY**: Read this entire document before starting conversion. The chunking strategy and prompt templates are critical for successful output.

## Conversion Architecture

The LLM conversion workflow:

```
extracted_content.json
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
    ▼         ▼         ▼          ▼
Metadata   Sections   Formulas   Tables/    ──►  LLM
(title,    (chunked)  (visual    Figures         │
authors)             + text)                      │
                                                  ▼
                                            LaTeX Source
                                                  │
                                                  ▼
                                         Assembled Document
```

## Pre-Conversion Preparation

### Step 1: Analyze Extracted Content

Before sending to LLM, review:

```bash
# Check content structure
python -c "
import json
with open('extracted/extracted_content.json') as f:
    data = json.load(f)
print(f'Title: {data[\"metadata\"][\"title\"]}')
print(f'Sections: {len(data[\"sections\"])}')
print(f'Figures: {len(data[\"figures\"])}')
print(f'Tables: {len(data[\"tables\"])}')
print(f'References: {len(data[\"references\"])}')
"
```

### Step 2: Identify Special Elements

Mark content requiring special handling:

- **Complex formulas**: Note formula IDs needing visual verification
- **Wide tables**: Tables requiring `sidewaystable` or `tabularx`
- **Multi-page tables**: Need `longtable` environment
- **Vector figures**: Check if figures need PDF inclusion

### Step 3: Select Template

Choose appropriate base template:

| Paper Type | Template | Packages |
|------------|----------|----------|
| Generic academic | `article.tex` | amsmath, graphicx, booktabs |
| IEEE conference | `IEEEtran.tex` | IEEEtran, amsmath |
| CVPR/ICCV | cvpr.sty based | cvpr, eso-pic |
| arXiv preprint | `article.tex` + custom | hyperref, arxiv-style |

## Chunking Strategy

**CRITICAL**: Proper chunking prevents context overflow and improves conversion quality.

### Chunking by Section (Recommended)

Organize conversion into logical batches:

```
Batch 1: Frontmatter
  - Title and author information
  - Abstract
  - Keywords

Batch 2: Introduction
  - Section 1 content
  - Any figures/tables in introduction

Batch 3: Related Work / Background
  - Section 2 content
  - Citations (keep as [1], [2] for now)

Batch 4: Method/Approach
  - Section 3+ with main technical content
  - Formulas (convert to LaTeX)
  - Algorithm pseudocode if present

Batch 5: Experiments/Results
  - Tables (convert to tabular)
  - Result figures
  - Numbers and statistics

Batch 6: Conclusion
  - Final sections
  - Future work
```

### Chunk Size Limits

**Token limits by model:**

| Model | Max Input | Recommended Chunk | Reserve for Output |
|-------|-----------|-------------------|-------------------|
| GPT-4 | 8K-32K | 3K-4K tokens | 2K-4K tokens |
| Claude 3 | 200K | 5K-8K tokens | 3K-5K tokens |
| Gemini Pro | 32K | 4K-5K tokens | 2K-3K tokens |

**Measuring chunk size:**
```python
# Rough estimation: 1 token ≈ 0.75 words
chunk_words = len(section_content.split())
estimated_tokens = chunk_words / 0.75
```

### Cross-Chunk Consistency

Maintain consistency across chunks:

1. **Shared preamble**: Define all macros in first chunk
2. **Figure numbering**: Use `\label{fig:section_name}` consistently
3. **Citation style**: Keep [N] format; convert to \cite{} in post-processing
4. **Terminology**: Include key term definitions in each chunk context

## Prompt Templates

### Template 1: Document Setup (Batch 1)

```
Convert the following paper metadata to LaTeX preamble and frontmatter.

TITLE: {title}
AUTHORS: {authors_list}
AFFILIATIONS: {affiliations}
ABSTRACT: {abstract}
KEYWORDS: {keywords}

TEMPLATE TYPE: {article|IEEEtran|cvpr}

CONVERSION REQUIREMENTS:

1. Document Class and Packages:
   - Use appropriate \documentclass based on template type
   - Include required packages: amsmath, amssymb, graphicx, booktabs, hyperref
   - Add color package if figures use colors
   - Include algorithm/algorithmic if paper has pseudocode

2. Title Block:
   - Format \title with proper line breaks if long
   - Use \author and \affiliation commands appropriately
   - Handle multiple authors with shared affiliations

3. Abstract:
   - Use \begin{abstract} environment
   - Preserve paragraph structure
   - Include \keywords command after abstract

4. Formatting Rules:
   - Use \emph{} for emphasis (not italic tags)
   - Use \textbf{} for bold text
   - Preserve special characters with proper escaping ($, %, &, _, #)

OUTPUT: Provide only the LaTeX code from \documentclass through \end{abstract}. No markdown code blocks.
```

### Template 2: Body Content (Batches 2-6)

```
Convert the following paper section to LaTeX.

SECTION NUMBER: {section_number}
SECTION TITLE: {section_title}
PARENT CONTEXT: {parent_section_or_paper_topic}

CONTENT TO CONVERT:
{section_content}

ASSOCIATED ELEMENTS:
Figures in this section: {figure_list_with_descriptions}
Tables in this section: {table_list}
Formulas to convert: {formula_list}

CONVERSION REQUIREMENTS:

1. Section Heading:
   - Use \section{{Title}} for level 1
   - Use \subsection{{Title}} for level 2
   - Use \subsubsection{{Title}} for level 3

2. Text Formatting:
   - Preserve paragraph breaks (blank lines between paragraphs)
   - Convert "quoted text" to ``quoted text'' (LaTeX quotes)
   - Use \emph{{}} for italicized terms
   - Use \textbf{{}} for bold terms

3. Mathematical Formulas:
   - Inline math: $formula$ (no spaces around $)
   - Display math: \[ formula \] or equation environment
   - Use \begin{{align}} for multi-line equations
   - Label important equations: \label{{eq:descriptive_name}}
   - Greek letters: \alpha, \beta, \gamma, \Gamma, etc.
   - Common functions: \sin, \cos, \log, \arg\max, etc.
   - Subscripts/superscripts: x_i, x^2, x_i^j
   - Fractions: \frac{{numerator}}{{denominator}}
   - Summations: \sum_{{i=1}}^n
   - Integrals: \int_0^\infty
   - Vectors: \mathbf{{x}} or \vec{{x}}
   - Matrices: \mathbf{{A}} with bm package or array environment

4. Figure Inclusion:
   - Use \begin{{figure}}[htbp] environment
   - \centering
   - \includegraphics[width=0.8\textwidth]{{figures/fig_X_X.png}}
   - \caption{{Caption text}}
   - \label{{fig:descriptive_name}}
   - \end{{figure}}

5. Table Conversion:
   - Use \begin{{table}}[htbp] environment
   - \centering
   - \begin{{tabular}}{{column_spec}} (use l, c, r, p{{width}})
   - Column spec examples: {lc} = 2 cols (left, center), {lccr} = 4 cols
   - Use \toprule, \midrule, \bottomrule from booktabs
   - Never use vertical rules in tables
   - \caption{{Caption text}}
   - \label{{tab:descriptive_name}}

6. Citations:
   - Keep citations as [1], [2,3], [4-6] format
   - Do NOT use \cite{} yet - will be converted later
   - Preserve citation positions in text

7. Lists:
   - Bulleted: \begin{{itemize}} ... \item ... \end{{itemize}}
   - Numbered: \begin{{enumerate}} ... \item ... \end{{enumerate}}

OUTPUT: Provide only the LaTeX code for this section. No markdown code blocks, no explanations.
```

### Template 3: Formula-Heavy Section

```
Convert this formula-intensive section with extra attention to math accuracy.

SECTION: {section_title}
CONTENT: {section_text_with_formulas}

FORMULA IMAGES FOR REFERENCE:
{formula_image_paths_or_descriptions}

CRITICAL MATH CONVERSION RULES:

1. Delimiters:
   - Inline: $...$ (tight, no spaces: $x = y$, not $ x = y $)
   - Display: \[ ... \] or equation environment
   - Never use $$ ... $$ (TeX deprecated)

2. Alignment:
   - Use align environment for multiple related equations:
     \begin{{align}}
     a &= b + c \\
     d &= e + f
     \end{{align}}
   - Use & before alignment character (usually =)

3. Common Symbols:
   - Dots: \cdots (centered), \ldots (baseline), \vdots, \ddots
   - Sets: \mathbb{{R}}, \mathbb{{Z}}, \mathbb{{N}}
   - Operators: \nabla, \partial, \infty, \propto, \sim
   - Arrows: \rightarrow, \Rightarrow, \leftrightarrow, \mapsto
   - Brackets: \left(, \right), \left[, \right], \left\{, \right\}
   - Norms: \lVert \mathbf{{x}} \rVert
   - Ceiling/floor: \lceil x \rceil, \lfloor x \rfloor

4. Functions:
   - Declared: \sin, \cos, \tan, \log, \exp, \max, \min, \arg\max
   - Custom: \operatorname{{CustomFunc}}

5. Accents:
   - Hat: \hat{{x}}, wide hat: \widehat{{ABC}}
   - Bar: \bar{{x}}, wide bar: \overline{{ABC}}
   - Tilde: \tilde{{x}}, wide tilde: \widetilde{{ABC}}
   - Dot: \dot{{x}}, double dot: \ddot{{x}}

6. Arrays and Matrices:
   - Use pmatrix (parentheses), bmatrix (brackets), vmatrix (vertical bars)
   - Example: \begin{{pmatrix}} a & b \\ c & d \end{{pmatrix}}

VERIFY EACH FORMULA: Compare your LaTeX output against the original formula images for symbol accuracy.

OUTPUT: Only LaTeX code. No markdown.
```

## Model-Specific Recommendations

### GPT-4 / GPT-4o

**Strengths:**
- High formula accuracy
- Good at following complex formatting rules
- Excellent table conversion

**Configuration:**
```python
{
  "model": "gpt-4",
  "temperature": 0.2,  # Low for accuracy
  "max_tokens": 4000,
  "system_prompt": "You are an expert LaTeX typesetter. Convert academic paper content to valid, compilable LaTeX code. Follow formatting rules precisely."
}
```

### Claude 3 (Opus/Sonnet)

**Strengths:**
- Very long context window (200K)
- Can process multiple sections at once
- Good at preserving document structure

**Configuration:**
```python
{
  "model": "claude-3-opus-20240229",
  "temperature": 0.2,
  "max_tokens": 4000,
  "system": "You are an expert LaTeX typesetter specializing in academic papers."
}
```

### Claude 3 with Vision (for formulas)

**Use case:** Complex formula recognition from images

```python
{
  "model": "claude-3-opus-20240229",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Convert this formula to LaTeX:"},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}
      ]
    }
  ]
}
```

## Quality Assurance

### Immediate Verification

After each batch conversion:

1. **Check LaTeX syntax:**
   ```bash
   # Quick syntax check
   pdflatex -draftmode batch1.tex
   ```

2. **Verify math compilation:**
   - Look for `! Missing $ inserted` errors
   - Check for undefined control sequences

3. **Cross-reference check:**
   - Ensure all \label{} have unique names
   - Verify \ref{} commands point to existing labels

### Common Conversion Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing $ inserted` | Math mode not entered/closed properly | Check all formulas have $ or proper environment |
| `Undefined control sequence` | Unknown command or typo | Check spelling, add missing package |
| `Argument of \item has an extra }` | Nested braces in item content | Protect with braces: `{\command{arg}}` |
| `Overfull \hbox` | Line too long | Allow line breaks in math, adjust table column widths |
| `Citation undefined` | \cite{} used before BibTeX processing | Keep [N] format during conversion |

### Batch Integration Checklist

After all batches converted:

- [ ] Preamble only in first batch
- [ ] No duplicate package declarations
- [ ] Consistent figure labels (fig:...)
- [ ] Consistent table labels (tab:...)
- [ ] Consistent equation labels (eq:...)
- [ ] No conflicting \newcommand definitions
- [ ] All figures referenced exist in figures/

## Conversion Workflow Summary

```
1. Review extracted_content.json structure
2. Select appropriate template
3. Plan batch divisions by section
4. Convert Batch 1 (preamble + abstract)
5. Convert Batches 2-N (body sections)
6. Syntax check each batch
7. Assemble complete document
8. Compile and fix errors
9. Proceed to post-processing (references)
```
