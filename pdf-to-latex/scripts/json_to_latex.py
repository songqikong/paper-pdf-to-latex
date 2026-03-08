#!/usr/bin/env python3
"""
将 extract_pdf.py 提取的 extracted_content.json 转为 LaTeX 主文件。
用法: python json_to_latex.py extracted_<name> output/<name> [--mapping extracted_<name>/citation_map.json]
"""

import argparse
import json
import os
import re
from pathlib import Path


def escape_latex(s: str) -> str:
    """基本 LaTeX 特殊字符转义"""
    s = s.replace('\\', '\\textbackslash{}')
    s = s.replace('&', '\\&')
    s = s.replace('%', '\\%')
    s = s.replace('#', '\\#')
    s = s.replace('_', '\\_')
    s = s.replace('{', '\\{')
    s = s.replace('}', '\\}')
    s = s.replace('$', '\\$')
    s = s.replace('~', '\\textasciitilde{}')
    s = s.replace('^', '\\textasciicircum{}')
    return s


def replace_citations(text: str, mapping: dict) -> str:
    """将 [1], [1,2], [1-3] 替换为 \\cite{key}"""
    def repl(m):
        nums_str = m.group(1)
        keys = []
        for part in re.split(r',\s*', nums_str):
            part = part.strip()
            rng = re.match(r'(\d+)\s*[-–]\s*(\d+)', part)
            if rng:
                for n in range(int(rng.group(1)), int(rng.group(2)) + 1):
                    keys.append(mapping.get(str(n), f'ref{n}'))
            else:
                keys.append(mapping.get(part, f'ref{part}'))
        return '\\cite{' + ','.join(keys) + '}'
    return re.sub(r'\[(\d+(?:[,\s–-]\d+)*)\](?!\s*\{)', repl, text)


def get_body_text(data: dict) -> str:
    """从 text_by_page 合并正文，去掉参考文献段落后面的内容"""
    pages = data.get('text_by_page', [])
    if not pages:
        return ''
    full = []
    for p in pages:
        t = p.get('text', '')
        # 去掉 REFERENCES 及之后的内容（最后一页常见）
        ref_match = re.search(r'\n\s*REFERENCES?\s*\n', t, re.IGNORECASE)
        if ref_match:
            t = t[:ref_match.start()]
        full.append(t)
    return '\n\n'.join(full)


def get_abstract(data: dict) -> str:
    """从 text_by_sections 或第一页取 abstract"""
    sections = data.get('text_by_sections', {})
    ab = sections.get('abstract', '')
    if ab:
        # 只保留 Abstract 到 Keywords 或 Introduction 之间
        ab = re.sub(r'\nKeywords[^\n]*.*', '', ab, flags=re.IGNORECASE)
        ab = re.sub(r'\nI+\.\s*INTRODUCTION.*', '', ab, flags=re.IGNORECASE)
        ab = ab.strip()
        if len(ab) > 50:
            return ab[:3000]  # 限制长度
    # 从第一页取 Abstract—... 一段
    pages = data.get('text_by_page', [])
    if pages:
        t = pages[0].get('text', '')
        m = re.search(r'Abstract[—\-]\s*(.+?)(?=\nKeywords|\nI+\.\s*INTRODUCTION|$)', t, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()[:3000]
    return ''


def get_large_figures(data: dict, min_size: int = 200) -> list:
    """返回足够大的图片列表，用于插入 figure 占位"""
    images = data.get('images', [])
    return [im for im in images if im.get('width', 0) > min_size and im.get('height', 0) > min_size]


def build_latex(extracted_dir: str, output_dir: str, mapping: dict) -> str:
    extracted_path = Path(extracted_dir)
    with open(extracted_path / 'extracted_content.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('metadata', {})
    title = meta.get('title', 'Untitled')
    title_esc = escape_latex(title)
    abstract = get_abstract(data)
    if abstract:
        abstract = escape_latex(abstract)
        abstract = replace_citations(abstract, mapping)
    body = get_body_text(data)
    body = escape_latex(body)
    body = replace_citations(body, mapping)
    # 简单段落化
    body_paras = [p.strip() for p in re.split(r'\n\s*\n', body) if p.strip() and len(p.strip()) > 20]
    # 常见章节标题转 \section
    section_pattern = re.compile(
        r'^(I{1,3}\.|IV|V|VI{0,3})\s+([A-Z][A-Z\s]+)$|^(\d+\.)\s+([A-Za-z].*)$|^(Abstract|Introduction|Conclusion|References?)\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    body_latex = []
    for p in body_paras:
        if section_pattern.match(p) and len(p) < 80:
            body_latex.append(f'\\section{{{escape_latex(p)}}}')
        else:
            body_latex.append(f'{p}\\par')
    body_text = '\n\n'.join(body_latex)

    figures = get_large_figures(data)
    fig_blocks = []
    for i, im in enumerate(figures[:30]):  # 最多 30 个图
        fn = im.get('filename', '')
        if not fn:
            continue
        fig_blocks.append(f'''
\\begin{{figure}}[htbp]
  \\centering
  \\includegraphics[width=0.8\\linewidth]{{figures/{fn}}}
  \\caption{{Figure {i+1}.}}
  \\label{{fig:{i+1}}}
\\end{{figure}}
''')

    preamble = r'''%!TEX program = pdflatex
% Decompiled from PDF using pdf-to-latex skill

\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{cite}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
'''

    doc = preamble + f'''
\\title{{{title_esc}}}
\\author{{}}
\\date{{}}
\\begin{{document}}
\\maketitle
'''
    if abstract:
        doc += f'\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n'
    doc += body_text + '\n\n'
    if fig_blocks:
        doc += '\n'.join(fig_blocks) + '\n'
    doc += r'''
\bibliographystyle{plain}
\bibliography{references}
\end{document}
'''
    return doc


def main():
    ap = argparse.ArgumentParser(description='Convert extracted_content.json to LaTeX')
    ap.add_argument('extracted_dir', help='e.g. extracted_stable_voronoi')
    ap.add_argument('output_dir', help='e.g. output/stable_voronoi')
    ap.add_argument('--mapping', help='JSON file with citation number->key mapping')
    args = ap.parse_args()

    mapping = {}
    if args.mapping and os.path.isfile(args.mapping):
        with open(args.mapping, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

    latex = build_latex(args.extracted_dir, args.output_dir, mapping)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in ('main.tex', 'main_final.tex'):
        (out / name).write_text(latex, encoding='utf-8')
    print(f"LaTeX written to {out}/main.tex and main_final.tex")


if __name__ == '__main__':
    main()
