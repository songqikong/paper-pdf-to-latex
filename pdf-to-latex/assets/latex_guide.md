# LaTeX Syntax Reference Guide

## Document Structure

### Basic Document Classes

```latex
% article - standard paper (default)
\documentclass[12pt]{article}

% IEEE conference
\documentclass[conference]{IEEEtran}

% book
\documentclass[12pt]{book}

% report
\documentclass[12pt]{report}
```

### Document Components

```latex
\documentclass{article}
\begin{document}

\title{Title}
\author{Author}
\date{\today}

\maketitle

\begin{abstract}
Abstract content...
\end{abstract}

\section{First Section}
\subsection{Subsection}
\subsection*{Unnumbered subsection}

\section{Second Section}

\end{document}
```

## Text Formatting

### Font Commands

```latex
\textbf{bold}
\textit{italic}
\underline{underline}
\textsc{small caps}

% Font sizes
{\tiny smallest}
{\small small}
{\normalsize normal}
{\large large}
{\Large larger}
{\LARGE very large}
{\huge huge}
```

### Special Characters

```latex
% Special symbols
\& \% \$ \# \_ \{ \}

% Ellipsis
\ldots  % horizontal ellipsis
\cdots  % centered ellipsis
\vdots  % vertical ellipsis
```

## Math Environments

### Inline Math

```latex
$x^2 + y^2 = z^2$

% or
\(E = mc^2\)
```

### Display Math

```latex
% Auto-numbered
\begin{equation}
    f(x) = \int_{-\infty}^{\infty} e^{-x^2} dx
\end{equation}

% Unnumbered
\begin{equation*}
    E = mc^2
\end{equation*}

% Manual numbering
\begin{equation}
    a^2 + b^2 = c^2 \tag{1}
\end{equation}
```

### Multi-line Equations

```latex
% align environment
\begin{align}
    a &= b + c \\
      &= d + e + f
\end{align}

% gather environment (centered)
\begin{gather}
    x = 1 \\
    y = 2
\end{gather}
```

### Common Math Commands

```latex
% Fractions
\frac{a}{b}

% Roots
\sqrt{x}
\sqrt[n]{x}

% Superscripts and subscripts
x^2
x_i
x^{2}_{i}

% Sum, integral, product
\sum_{i=1}^{n}
\int_{a}^{b}
\prod_{i=1}^{n}

% Limits
\lim_{x \to \infty}

% Common symbols
\alpha \beta \gamma \delta
\epsilon \zeta \eta \theta
\lambda \mu \nu \xi \pi
\sigma \tau \phi \psi \omega

\pm \times \div \cdot
\leq \geq \neq \approx
\in \subset \cup \cap
\rightarrow \leftarrow \leftrightarrow
\Rightarrow \Leftarrow \Leftrightarrow
```

## Tables

### Basic Table

```latex
\begin{table}[htbp]
    \centering
    \caption{Table caption}
    \label{tab:example}
    \begin{tabular}{lcc}
        \toprule
        Col1 & Col2 & Col3 \\
        \midrule
        content & content & content \\
        content & content & content \\
        \bottomrule
    \end{tabular}
\end{table}
```

### Table Column Alignment

```latex
% l - left, c - center, r - right
\begin{tabular}{|l|c|r|}  % | for vertical rules

% Multiple columns
\usepackage{multicol}
\begin{tabular}{l*3{c}}  % 3 centered columns

% Table rules
\toprule    % top rule
\midrule    % middle rule
\bottomrule % bottom rule
\cmidrule   % partial rule
```

### Column and Row Spanning

```latex
% Column span
\multicolumn{2}{c}{Span two columns}\\

% Row span
\usepackage{multirow}
\multirow{2}{*}  % span 2 rows
```

## Figures

### Inserting Figures

```latex
\usepackage{graphicx}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\linewidth]{figures/fig1.png}
    \caption{Figure caption}
    \label{fig:example}
\end{figure}
```

### Subfigures

```latex
\usepackage{subcaption}

\begin{figure}[htbp]
    \centering
    \begin{subfigure}[b]{0.4\linewidth}
        \includegraphics[width=\linewidth]{fig1.png}
        \caption{Subfigure 1}
        \label{fig:sub1}
    \end{subfigure}
    \begin{subfigure}[b]{0.4\linewidth}
        \includegraphics[width=\linewidth]{fig2.png}
        \caption{Subfigure 2}
        \label{fig:sub2}
    \end{subfigure}
    \caption{Overall caption}
    \label{fig:main}
\end{figure}
```

### Float Placement Options

- `h` - here (current position)
- `t` - top of page
- `b` - bottom of page
- `p` - separate page
- `!` - override float parameters

## Lists

### Unordered List

```latex
\begin{itemize}
    \item First item
    \item Second item
        \begin{itemize}
            \item Sub-item
        \end{itemize}
    \item Third item
\end{itemize}
```

### Ordered List

```latex
\begin{enumerate}
    \item First step
    \item Second step
    \item Third step
\end{enumerate}
```

### Description List

```latex
\begin{description}
    \item[Term 1] Description 1
    \item[Term 2] Description 2
\end{description}
```

## References

### BibTeX Format

```bibtex
@article{key2023,
    author = {Author, A. and Coauthor, B.},
    title = {Title of the Paper},
    journal = {Journal Name},
    year = {2023},
    volume = {1},
    pages = {1--10}
}

@conference{key2023,
    author = {Author, A.},
    title = {Title of the Conference Paper},
    booktitle = {Proceedings of Conference Name},
    year = {2023},
    pages = {1--8}
}

@misc{key2023,
    author = {Author, A.},
    title = {Title},
    howpublished = {\url{https://example.com}},
    year = {2023}
}
```

### Citation Commands

```latex
% Cite
\cite{key2023}

% Multiple citations
\cite{key1,key2,key3}

% Superscript citation
\supercite{key2023}
```

### Bibliography Styles

```latex
\usepackage{natbib}
\bibliographystyle{plainnat}  % alphabetical
\bibliographystyle{abbrvnat}  % abbreviated
\bibliographystyle{acm}       % ACM style
\bibliographystyle{ieeetr}    % IEEE style

\bibliography{references}
```

## Code Environments

### Using listings

```latex
\usepackage{listings}
\usepackage{xcolor}

\lstset{
    basicstyle=\ttfamily,
    numbers=left,
    numberstyle=\tiny,
    keywordstyle=\color{blue},
    stringstyle=\color{red},
    commentstyle=\color{green}
}

\begin{lstlisting}[language=Python]
def hello():
    print("Hello, World!")
\end{lstlisting}
```

### Using minted

```latex
\usepackage{minted}

\begin{minted}{python}
def hello():
    print("Hello, World!")
\end{minted}
```

## Theorem Environments

```latex
\usepackage{amsthm}

\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{definition}{Definition}
\newtheorem{proposition}{Proposition}
\newtheorem{corollary}{Corollary}

\begin{theorem}
    Theorem content...
\end{theorem}

\begin{proof}
    Proof...
\end{proof}
```

## Common Packages

```latex
% Math
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}

% Graphics
\usepackage{graphicx}
\usepackage{subcaption}

% Tables
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{longtable}

% Links
\usepackage{hyperref}

% Color
\usepackage{xcolor}

% Code
\usepackage{listings}
\usepackage{minted}
```

## Troubleshooting

### Figures not showing

1. Verify file path is correct
2. Verify file format is supported (png, jpg, pdf)
3. Use `width=\linewidth` instead of fixed width

### Formula compilation errors

1. Check bracket matching
2. Check that `_` and `^` are followed by content
3. Use `\operatorname` for operator names

### Reference order (BibTeX)

1. Run pdflatex
2. Run bibtex
3. Run pdflatex
4. Run pdflatex
