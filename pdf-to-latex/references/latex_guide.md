# LaTeX 语法参考指南

## 文档结构

### 基本文档类

```latex
% article - 标准论文 (默认)
\documentclass[12pt]{article}

% IEEE会议
\documentclass[conference]{IEEEtran}

% book - 书籍
\documentclass[12pt]{book}

% report - 报告
\documentclass[12pt]{report}
```

### 文档组成部分

```latex
\documentclass{article}
\begin{document}

\title{标题}
\author{作者}
\date{\today}

\maketitle

\begin{abstract}
摘要内容...
\end{abstract}

\section{第一节}
\subsection{子节}
\subsection*{无编号子节}

\section{第二节}

\end{document}
```

## 文本格式

### 字体命令

```latex
\textbf{粗体}
\textit{斜体}
\underline{下划线}
\textsc{小型大写}

% 字号
{\tiny 最小}
{\small 小}
{\normalsize 正常}
{\large 大}
{\Large 更大}
{\LARGE 很大}
{\huge 巨大}
```

### 特殊字符

```latex
% 特殊符号
\& \% \$ \# \_ \{ \}

% 省略号
\ldots  % 水平省略号
\cdots  % 中心省略号
vdots   % 垂直省略号
```

## 数学环境

### 行内公式

```latex
$x^2 + y^2 = z^2$

% 或
\(E = mc^2\)
```

### 行间公式

```latex
% 自动编号
\begin{equation}
    f(x) = \int_{-\infty}^{\infty} e^{-x^2} dx
\end{equation}

% 不编号
\begin{equation*}
    E = mc^2
\end{equation*}

% 手动编号
\begin{equation}
    a^2 + b^2 = c^2 \tag{1}
\end{equation}
```

### 多行公式

```latex
% align 环境
\begin{align}
    a &= b + c \\
      &= d + e + f
\end{align}

% gather 环境 (居中)
\begin{gather}
    x = 1 \\
    y = 2
\end{gather}
```

### 常用数学命令

```latex
% 分数
\frac{a}{b}

% 根号
\sqrt{x}
\sqrt[n]{x}

% 上标下标
x^2
x_i
x^{2}_{i}

% 求和积分
\sum_{i=1}^{n}
\int_{a}^{b}
\prod_{i=1}^{n}

% 极限
\lim_{x \to \infty}

% 常用符号
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

## 表格

### 基本表格

```latex
\begin{table}[htbp]
    \centering
    \caption{表格标题}
    \label{tab:example}
    \begin{tabular}{lcc}
        \toprule
        列1 & 列2 & 列3 \\
        \midrule
        内容 & 内容 & 内容 \\
        内容 & 内容 & 内容 \\
        \bottomrule
    \end{tabular}
\end{table}
```

### 表格列格式

```latex
% l - 左对齐, c - 居中, r - 右对齐
\begin{tabular}{|l|c|r|}  % | 表示垂直线

% 多列
\usepackage{multicol}
\begin{tabular}{l*3{c}}  % 3列居中

% 表格线
\toprule    % 顶线
\midrule    % 中线
\bottomrule % 底线
\cmidrule   % 部分线
```

### 跨列跨行

```latex
% 跨列
\multicolumn{2}{c}{跨两列}\\

% 跨行
\usepackage{multirow}
multirow{2}{*}  % 跨2行
```

## 图片

### 插入图片

```latex
\usepackage{graphicx}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\linewidth]{figures/fig1.png}
    \caption{图片标题}
    \label{fig:example}
\end{figure}
```

### 子图

```latex
\usepackage{subcaption}

\begin{figure}[htbp]
    \centering
    \begin{subfigure}[b]{0.4\linewidth}
        \includegraphics[width=\linewidth]{fig1.png}
        \caption{子图1}
        \label{fig:sub1}
    \end{subfigure}
    \begin{subfigure}[b]{0.4\linewidth}
        \includegraphics[width=\linewidth]{fig2.png}
        \caption{子图2}
        \label{fig:sub2}
    \end{subfigure}
    \caption{总图题}
    \label{fig:main}
\end{figure}
```

### 图片位置参数

- `h` - 当前位置
- `t` - 顶部
- `b` - 底部
- `p` - 单独页面
- `!` - 忽略浮动参数

## 列表

### 无序列表

```latex
\begin{itemize}
    \item 第一项
    \item 第二项
        \begin{itemize}
            \item 子项
        \end{itemize}
    \item 第三项
\end{itemize}
```

### 有序列表

```latex
\begin{enumerate}
    \item 第一步
    \item 第二步
    \item 第三步
\end{enumerate}
```

### 描述列表

```latex
\begin{description}
    \item[Term 1] 描述1
    \item[Term 2] 描述2
\end{description}
```

## 参考文献

### BibTeX 格式

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

### 引用方式

```latex
% 引用
\cite{key2023}

% 多个引用
\cite{key1,key2,key3}

% 上标引用
\supercite{key2023}
```

### 参考文献样式

```latex
\usepackage{natbib}
\bibliographystyle{plainnat}  % 字母顺序
\bibliographystyle{abbrvnat}  % 缩写
\bibliographystyle{acm}       % ACM风格
\bibliographystyle{ieeetr}    % IEEE风格

\bibliography{references}
```

## 代码环境

### 使用 listings

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

### 使用 minted

```latex
\usepackage{minted}

\begin{minted}{python}
def hello():
    print("Hello, World!")
\end{minted}
```

## 定理环境

```latex
\usepackage{amsthm}

\newtheorem{theorem}{Theorem}
\newtheorem lemma{Lemma}
\newtheorem definition{Definition}
\newtheorem proposition{Proposition}
\newtheorem corollary{Corollary}

\begin{theorem}
    定理内容...
\end{theorem}

\begin{Proof}
    证明...
\end{Proof}
```

## 常用宏包

```latex
% 数学
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}

% 图形
\usepackage{graphicx}
\usepackage{subcaption}

% 表格
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{longtable}

% 链接
\usepackage{hyperref}

% 颜色
\usepackage{xcolor}

% 代码
\usepackage{listings}
\usepackage{minted}
```

## 常见问题

### 图片不显示

1. 确认文件路径正确
2. 确认文件格式支持 (png, jpg, pdf)
3. 使用 `width=\linewidth` 代替固定宽度

### 公式编译错误

1. 检查括号匹配
2. 检查 `_` 和 `^` 后是否有内容
3. 使用 `\operatorname` 定义运算符

### 参考文献顺序

1. 运行 pdflatex
2. 运行 bibtex
3. 运行 pdflatex
4. 运行 pdflatex
