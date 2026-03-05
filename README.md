# paper-pdf-to-latex

将学术论文 PDF 逆向还原为可编辑 LaTeX 源码的工具集，支持文本、数学公式、表格、图片及参考文献的完整提取与转换流程。

## 功能特性

- **多格式支持**：适配 CVPR/ICCV/NeurIPS 会议论文、IEEE 期刊、arXiv 预印本等常见格式
- **公式提取**：混合字体检测与图像裁剪，支持调用 GPT-4V / Claude 3 视觉能力识别复杂公式
- **表格提取**：同时支持有边框表格（pdfplumber）和无边框表格（空白对齐检测）
- **参考文献转换**：自动生成 BibTeX，并将正文中的 `[1]`、`[2-4]` 等数字引用替换为 `\cite{key}`
- **双栏布局**：正确处理学术论文常见的双栏排版

## 项目结构

```
pdf-to-latex/
├── scripts/
│   ├── extract_pdf.py          # PDF 内容提取脚本
│   ├── convert_formula.py      # 公式转换脚本
│   └── convert_references.py  # 参考文献 BibTeX 生成 & 引用替换
├── docs/
│   ├── 01-extraction.md        # 提取阶段详细指南
│   ├── 02-conversion.md        # LLM 转换策略与 Prompt 模板
│   └── 03-post-processing.md  # 后处理（引用、图片、编译）指南
├── assets/
│   └── latex_template/
│       ├── article.tex         # 通用学术论文模板
│       ├── cvpr.tex            # CVPR 模板
│       └── IEEEtran.tex        # IEEE 模板
├── references/
│   └── latex_guide.md          # LaTeX 语法参考
├── SKILL.md                    # AI Agent 使用指引
└── requirements.txt
```

提取后的输出目录结构：

```
output/
├── extracted_content.json      # 结构化内容（文本、章节、元数据）
├── figures/                    # 提取的图片（fig_{page}_{index}.png）
├── formulas/                   # 公式图片（使用 --extract-formula-images 时）
└── tables.json                 # 表格结构化数据
```

## 安装

```bash
pip install -r pdf-to-latex/requirements.txt
```

主要依赖：

| 包 | 用途 |
|----|------|
| `pymupdf >= 1.23.0` | PDF 解析、图片与公式区域提取 |
| `pdfplumber >= 0.10.0` | 文本与表格精确提取 |
| `pillow >= 10.0.0` | 图像处理 |

## 快速开始

### 工作流选择

| 场景 | 推荐工作流 |
|------|-----------|
| 简单单栏文档，无复杂公式 | 基础工作流 |
| CVPR / ICCV / NeurIPS 会议论文 | 完整工作流 |
| 公式密集型文档 | 公式增强工作流 |
| 已有 BibTeX 文件 | 引用映射工作流 |

### 基础工作流

```bash
# 1. 提取 PDF 内容
python pdf-to-latex/scripts/extract_pdf.py paper.pdf -o output/

# 2. 查看提取结果
cat output/extracted_content.json

# 3. 使用 LLM（如 Claude / GPT-4）将结构化内容转换为 LaTeX
#    参考 docs/02-conversion.md 中的 Prompt 模板

# 4. 使用 assets/latex_template/ 中的模板组装文档
```

### 完整工作流（推荐用于会议论文）

```bash
# 1. 提取 PDF，并保存公式图片
python pdf-to-latex/scripts/extract_pdf.py paper.pdf -o output/ \
  --extract-formula-images --dpi 200

# 2. 使用 LLM 分批次转换各章节为 LaTeX（参考 docs/02-conversion.md）

# 3. 生成 BibTeX
python pdf-to-latex/scripts/convert_references.py output/extracted_content.json \
  -o references.bib

# 4. 将正文中的数字引用替换为 \cite{}
python pdf-to-latex/scripts/convert_references.py output/extracted_content.json \
  -t main.tex --output-tex final.tex -b references.bib

# 5. 编译
cd output/ && latexmk -pdf main.tex
```

### 公式增强工作流

```bash
# 提取时保存公式区域图片，然后用视觉 LLM 识别
python pdf-to-latex/scripts/extract_pdf.py paper.pdf -o output/ \
  --extract-formula-images --dpi 200

# 将 output/formulas/ 下的图片喂给 GPT-4V / Claude 3 进行公式识别
```

### 使用已有 BibTeX 文件

```bash
python pdf-to-latex/scripts/convert_references.py output/extracted_content.json \
  -b existing.bib -t main.tex --output-tex final.tex
```

## 脚本参数

### `extract_pdf.py`

```
positional arguments:
  input_pdf                    输入 PDF 文件路径

optional arguments:
  -o, --output DIR             输出目录（默认: extracted/）
  --extract-formula-images     将公式区域保存为独立图片
  --start-page N               起始页（1-indexed）
  --end-page N                 结束页
  --dpi N                      图片提取 DPI（默认: 150）
  --ocr-fallback               文本层损坏时使用 OCR
  --check-text                 检测文本层可提取性
  --low-memory                 低内存模式，逐张处理图片
```

### `convert_references.py`

```
positional arguments:
  input_file                   extracted_content.json 或文本文件

optional arguments:
  -o, --output FILE            输出 BibTeX 文件路径
  -t, --tex-file FILE          需要转换引用的 LaTeX 文件
  --output-tex FILE            转换后的 LaTeX 文件输出路径
  -b, --bibtex FILE            已有的 BibTeX 文件（用于建立数字→key 映射）
```

## 提取结果说明

`extracted_content.json` 包含以下字段：

```json
{
  "metadata": { "title": "...", "authors": [...], "abstract": "..." },
  "sections": [{ "number": "1", "title": "Introduction", "content": "..." }],
  "figures":  [{ "id": "fig_1_1", "path": "figures/fig_1_1.png" }],
  "formulas": [...],
  "tables":   [...],
  "references": [...],
  "citations": [{ "number": 1, "context": "...as shown in [1]..." }]
}
```

快速核验提取结果：

```bash
python -c "
import json
d = json.load(open('output/extracted_content.json'))
print(f'章节: {len(d[\"sections\"])}, 图片: {len(d[\"figures\"])}, 参考文献: {len(d[\"references\"])}')
"
```

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 提取文字乱码 | PDF 使用自定义字体且无 ToUnicode 映射 | 使用 `--ocr-fallback` |
| 公式缺失 | 公式以图片或矢量形式渲染 | 使用 `--extract-formula-images` + 视觉 LLM |
| 表格内容错位 | 复杂布局或合并单元格 | 参考 `tables.json` 手动修正 |
| 参考文献顺序错误 | 跨栏提取顺序混乱 | 对比 PDF 手动调整 `extracted_content.json` |
| 引用映射错误 | 参考文献提取顺序与 PDF 不一致 | 核验 `extracted_content.json` 中的 references 顺序 |

## 详细文档

- [01-extraction.md](pdf-to-latex/docs/01-extraction.md)：提取架构、参数调优、各内容类型处理细节
- [02-conversion.md](pdf-to-latex/docs/02-conversion.md)：LLM 分批转换策略、各模型配置、Prompt 模板
- [03-post-processing.md](pdf-to-latex/docs/03-post-processing.md)：BibTeX 生成、引用替换、图片优化、编译流程
