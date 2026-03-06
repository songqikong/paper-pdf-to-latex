# AAAI 论文逆编译注意事项

本文档总结在将 **AAAI 格式**学术论文从 PDF 逆编译为 LaTeX 源码时需要注意的要点，与 CVPR、IEEE 等格式的差异，以及实践中可采取的变通方法。基于对 `js3cnet.pdf`（AAAI 2021）的完整逆编译经验整理。

## 1. 格式与模板差异

### 1.1 文档类与样式
- **AAAI** 官方要求使用 `\documentclass[letterpaper]{article}` 配合 `\usepackage{aaai}`（aaai21.sty 等），参考文献样式为 **aaai21.bst**。
- **CVPR/ICCV** 使用 `cvpr` 宏包与 `ieee_fullname` 等 bst；**IEEE** 使用 `IEEEtran` 文档类。
- **逆编译时**：若本地无 `aaai.sty`，可先用 `\documentclass[11pt,twocolumn]{article}` + 常用宏包（amsmath, graphicx, booktabs, cite）生成可编译的中间稿，并在说明中注明“需替换为官方 AAAI 模板后再投递”。

### 1.2 双栏与版面
- AAAI 与 CVPR 类似，均为**双栏**。提取出的 `text_by_page` 会出现**左右栏交错**（同一页字符串内左栏与右栏内容交替出现）。
- 逆编译时：以**语义和段落逻辑**为准重组正文，不必拘泥于原始提取顺序；可结合 PDF 目视核对章节边界。

## 2. 参考文献与引用

### 2.1 参考文献列表格式
- AAAI 正文中多为 **Author–Year 引用**（如 “(Thomas et al. 2019)”、“Dai et al. 2017”），文末参考文献列表多为**无数字编号**的 Author. Year. Title. Venue 形式。
- 提取脚本依赖的 `references` 字段若为空，说明当前 extractor 未识别 AAAI 的无编号参考文献格式。

### 2.2 从正文/章节中恢复参考文献
- 可从 `text_by_sections["references"]` 或 `text_by_page` 最后一两页的文本中**解析参考文献**。
- AAAI 双栏会导致一条 ref 被拆成多段、或两条 ref 混在一段。建议按“新条目起始”的启发式切分，例如：
  - 以 “`LastName, Initial(s).`” 或 “`Year.`” 后接标题/会议名作为新条目起点；
  - 用正则如 `(?<=\.)\s+(?=[A-Z][a-z]+,\s*[A-Z]\.?\s*[;])` 在句号后、下一作者名前切分。
- 切分后得到若干条 `{ "number": "1", "text": "..." }` 写入 `extracted_content.json` 的 `references` 数组，再运行 `convert_references.py` 生成 `references.bib` 和 `[N] -> \cite{key}` 映射。

### 2.3 引用在正文中的写法
- 原文为 Author–Year 时，逆编译后的 LaTeX 应使用 **\cite{key}**（key 由 convert_references 生成，如 thomas2019, behley2019）。
- 不要使用 `convert_references.py -t` 的 tex 替换模式做双栏论文的 [N]→\cite{key}：列表顺序可能与正文引用编号不一致（参见 SKILL.md Known Issues）。

## 3. 图片与图表

### 3.1 图片过多与过滤
- AAAI 论文中复杂 figure（如流程图、多子图）在 PDF 内常由大量小图元组成，提取后可能得到**上百张**小图（如 50×50、4×265 等）。
- 按 SKILL.md 建议：**只保留宽高均大于约 200px 的图片**用于正文 `\includegraphics`，避免引用到装饰性/线条类小图。
- 子图（如 Fig.1 (a)(b)(c)(d)）对应多张图时，用 `\includegraphics` + `subcaption` 或并排多图组合为一张 figure。

### 3.2 表格
- 表格提取仍以 `extracted_content.json` 的 `tables` 及 `text_by_page` 中的表格文本为主；复杂表格需人工校对合并单元格与对齐方式。

## 4. 元数据与第一页

### 4.1 标题与作者
- `metadata.title` / `metadata.authors` 常为**空**（与 SKILL.md 一致）。应从 **`text_by_page[0]["text"]`** 中解析：
  - 第一段多为标题；
  - 其后为作者行（含上标 1,2,†,* 等）、单位、邮箱。
- AAAI 常见 “*Corresponding author. † Equal first authorship.” 及版权声明 “Copyright © 2021, Association for the Advancement of Artificial Intelligence (www.aaai.org). All rights reserved.”，逆编译时可保留在作者注释或 acknowledgments 附近。

## 5. 公式与数学

- 公式以 `text_by_page` 中的 Unicode/纯文本形式出现，可能缺符号或错位（尤其双栏时）。需结合 PDF 原版**人工核对**关键公式。
- 若未实现 `--extract-formula-images`，则依赖 LLM 根据上下文将公式文本转为 LaTeX（如 `\[...\]`、`align` 等）。

## 6. 与 SKILL.md 的灵活运用

- 遇到 AAAI 特有情况时**可不拘泥** SKILL 中针对 CVPR/IEEE 的硬性约定，例如：
  - 模板优先采用 **article + twocolumn** 或官方 AAAI 模板（若已提供）；
  - 参考文献从 `text_by_sections["references"]` 自行解析并写回 JSON，再跑 convert_references；
  - 引用一律用 **\cite{key}**，key 以 convert_references 打印的映射为准。
- 输出目录仍建议遵循 **`extracted_<name>/`** 与 **`output/<name>/`**，便于多篇论文并存。

## 7. 检查清单（AAAI 逆编译后）

- [ ] 标题、作者、单位、邮箱来自第 1 页文本且格式正确。
- [ ] Abstract 与正文章节来自 `text_by_page`，双栏交错已按语义重排。
- [ ] 参考文献条数与原 PDF 末尾 References 一致或接近；BibTeX 的 key 与正文 \cite{} 一致。
- [ ] 仅使用宽高均足够大的图片（如 >200px），子图与图题对应正确。
- [ ] 公式与原文一致，必要时对照 PDF 逐式检查。
- [ ] 若需投递 AAAI，将当前文档替换为官方 aaai 模板并改用 aaai21.bst 再编译。

---

*本文档基于 pdf-to-latex 对 AAAI 2021 论文 js3cnet.pdf 的逆编译实践整理，供后续 AAAI 格式论文逆编译时参考。*
