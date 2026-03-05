#!/usr/bin/env python3
"""
PDF论文内容提取脚本
用于从PDF学术论文中提取文本、公式、图片、表格等内容
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

# 尝试导入PDF处理库
try:
    import fitz  # PyMuPDF
except ImportError:
    print("请安装PyMuPDF: pip install pymupdf")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("请安装pdfplumber: pip install pdfplumber")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("请安装Pillow: pip install pillow")
    sys.exit(1)


class PDFExtractor:
    """PDF内容提取器"""
    
    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.figures_dir = self.output_dir / "figures"
        self.figures_dir.mkdir(exist_ok=True)
        
        # 加载PDF
        self.doc = fitz.open(pdf_path)
        self.pdf = pdfplumber.open(pdf_path)
        
    def extract_metadata(self) -> Dict:
        """提取论文元信息"""
        meta = self.doc.metadata
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "page_count": len(self.doc)
        }
    
    def extract_text_by_page(self) -> List[Dict]:
        """按页提取文本内容"""
        pages = []
        for page_num, page in enumerate(self.pdf.pages, 1):
            text = page.extract_text()
            pages.append({
                "page_num": page_num,
                "text": text
            })
        return pages
    
    def extract_text_by_sections(self) -> Dict:
        """按章节组织文本"""
        full_text = ""
        for page in self.pdf.pages:
            full_text += page.extract_text() + "\n\n"
        
        # 简单的章节识别（基于常见标题模式）
        sections = {}
        current_section = "abstract"
        current_content = []
        
        lines = full_text.split('\n')
        section_pattern = re.compile(
            r'^(Abstract|Introduction|Related Work|Methodology|Experiment|Results|Conclusion|References|Acknowledgments)'
            r'(\s|$)',
            re.IGNORECASE
        )
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            match = section_pattern.match(line)
            if match:
                # 保存上一节
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                # 开始新节
                current_section = match.group(1).lower()
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一节
        if current_content:
            sections[current_section] = "\n".join(current_content)
        
        return sections
    
    def extract_images(self) -> List[Dict]:
        """提取所有图片"""
        images = []
        img_count = 0
        
        for page_num, page in enumerate(self.doc, 1):
            for img_index, img in enumerate(page.get_images()):
                xref = img[0]
                base_image = self.doc.extract_image(xref)
                
                img_count += 1
                img_ext = base_image["ext"]
                img_data = base_image["image"]
                
                # 保存图片
                img_name = f"fig_{page_num}_{img_index + 1}.{img_ext}"
                img_path = self.figures_dir / img_name
                
                with open(img_path, "wb") as f:
                    f.write(img_data)
                
                images.append({
                    "image_id": img_count,
                    "page": page_num,
                    "index": img_index,
                    "filename": img_name,
                    "path": str(img_path),
                    "width": base_image["width"],
                    "height": base_image["height"]
                })
        
        return images
    
    def extract_tables(self) -> List[Dict]:
        """提取表格 - 增强版，支持多种检测方式"""
        tables = []
        
        for page_num, page in enumerate(self.pdf.pages, 1):
            # 方法1: 使用pdfplumber的tables检测
            page_tables = page.extract_tables()
            
            for table_idx, table in enumerate(page_tables):
                if table and len(table) > 1:
                    tables.append({
                        "page": page_num,
                        "table_idx": table_idx,
                        "method": "pdfplumber",
                        "data": table,
                        "row_count": len(table)
                    })
            
            # 方法2: 备用 - 基于文本行的表格检测
            # 检测含有多个制表符或对齐文本的行
            if not any(t.get("page") == page_num for t in tables):
                text = page.extract_text()
                lines = text.split('\n')
                table_candidates = []
                
                for line in lines:
                    # 检测是否是多列对齐的表格行
                    if '\t' in line or (len(line.split()) >= 3 and '  ' in line):
                        table_candidates.append(line.split('\t') if '\t' in line else line.split())
                
                if len(table_candidates) >= 2:
                    tables.append({
                        "page": page_num,
                        "table_idx": len([t for t in tables if t.get("page") == page_num]),
                        "method": "text_alignment",
                        "data": table_candidates,
                        "row_count": len(table_candidates)
                    })
        
        return tables
    
    def extract_formulas(self) -> List[Dict]:
        """提取数学公式（作为文本候选区域）"""
        # 注意：PDF中的公式通常是文本而非图片
        # 这里我们提取包含数学符号的行作为公式候选
        formulas = []
        
        math_indicators = [
            r'\(', r'\)', r'\[', r'\]',  # LaTeX公式标记
            r'∫', r'∑', r'∏', r'∂',     # 数学符号
            r'α', r'β', r'γ', r'δ', r'θ',  # 希腊字母
            r'∈', r'⊂', r'∪', r'∩',      # 集合符号
            r'→', r'←', r'↔', r'⇒',      # 箭头
        ]
        
        math_pattern = re.compile('|'.join(math_indicators))
        
        for page_num, page in enumerate(self.pdf.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            for line_idx, line in enumerate(lines):
                if math_pattern.search(line):
                    formulas.append({
                        "page": page_num,
                        "line": line_idx,
                        "text": line.strip()
                    })
        
        return formulas
    
    def extract_citations(self) -> Dict[int, str]:
        """提取正文中的引用映射 (数字 -> 引用上下文)"""
        citations = {}
        
        for page_num, page in enumerate(self.pdf.pages, 1):
            text = page.extract_text()
            
            # 匹配各种引用格式: [1], [1,2], [1-3], (1), (1,2)
            citation_patterns = [
                r'\[(\d+(?:[,\s\-–]\d+)*)\]',  # [1], [1,2], [1-3]
                r'\((\d+(?:[,\s\-–]\d+)*)\)',  # (1), (1,2)
            ]
            
            for pattern in citation_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    ref_nums = match.group(1)
                    # 解析数字列表
                    nums = re.findall(r'\d+', ref_nums)
                    for num in nums:
                        citations[int(num)] = {
                            "page": page_num,
                            "context": text[max(0, match.start()-50):match.end()+50].strip()
                        }
        
        return citations
    
    def extract_references(self) -> List[Dict]:
        """提取参考文献列表（增强版 - 支持双栏布局）"""
        references = []
        
        # 获取最后几页（参考文献通常在文档末尾）
        num_pages = len(self.pdf.pages)
        start_page = max(0, num_pages - 5)
        
        # 收集参考文献部分的文本
        ref_text = ""
        in_refs = False
        references_started = False
        
        for page in self.pdf.pages[start_page:]:
            text = page.extract_text()
            lines = text.split('\n')
            
            for line in lines:
                line_stripped = line.strip()
                
                # 检测References标题（多种格式）
                # 格式1: 单独一行的 "References"
                # 格式2: 行首的 "REFERENCES ..."（双栏布局中可能紧跟其他文本）
                # 格式3: 嵌入在其他文本中的 "REFERENCES"
                if not in_refs:
                    if re.search(r'^(?:References|Bibliography|Literature\s+Cited)\s*$', line_stripped, re.IGNORECASE):
                        in_refs = True
                        references_started = True
                        continue
                    elif re.search(r'^REFERENCES\s', line_stripped, re.IGNORECASE):
                        # 格式: "REFERENCES Systems,S.Koyejo,..."
                        in_refs = True
                        references_started = True
                        # 提取REFERENCES之后的内容
                        ref_match = re.search(r'^REFERENCES\s+(.*)$', line_stripped, re.IGNORECASE)
                        if ref_match:
                            ref_text += ref_match.group(1) + " "
                        continue
                    elif re.search(r'REFERENCES', line_stripped) and not references_started:
                        # 可能混入其他文本，检查是否是标题
                        if len(line_stripped) < 50:
                            in_refs = True
                            references_started = True
                            continue
                
                # 检测新章节（结束参考文献）
                if in_refs and re.match(r'^(?:Appendix|Appendices|Acknowledgments|Acknowledgements)\s*$', line_stripped, re.IGNORECASE):
                    break
                
                if in_refs:
                    # 跳过空行和表格线
                    if not line_stripped or re.match(r'^[\s\-_=]+$', line_stripped):
                        continue
                    ref_text += line + " "
        
        # 解析参考文献 - 使用多种模式匹配
        if ref_text:
            references = self._parse_references_multi_pattern(ref_text)
        
        return references
    
    def _parse_references_multi_pattern(self, text: str) -> List[Dict]:
        """使用多种模式解析参考文献"""
        references = []
        
        # 模式1: [N] 格式 (最常见)
        pattern1 = re.compile(
            r'\[(\d+)\]\s*([^\[]+)',
            re.DOTALL
        )
        
        # 模式2: N. 格式
        pattern2 = re.compile(
            r'(?:^|\n)\s*(\d+)\.\s+([A-Z][^\n]*(?:\n(?![\n\d]\.|\[\d+\])[^\n]*)*)',
            re.MULTILINE
        )
        
        # 模式3: (N) 格式
        pattern3 = re.compile(
            r'\((\d+)\)\s+([A-Z][^(]+)',
            re.DOTALL
        )
        
        # 尝试模式1
        matches = list(pattern1.finditer(text))
        if len(matches) >= 2:
            for i, match in enumerate(matches):
                ref_num = match.group(1)
                ref_content = match.group(2).strip()
                
                # 清理内容
                ref_content = re.sub(r'\s+', ' ', ref_content)
                
                # 限制长度（到下一条引用之前）
                if i + 1 < len(matches):
                    next_start = matches[i + 1].start()
                    ref_content = text[match.end(1)+1:next_start].strip()
                    ref_content = re.sub(r'\s+', ' ', ref_content)
                
                if ref_content and len(ref_content) > 15 and not self._is_table_row(ref_content):
                    references.append({
                        'number': ref_num,
                        'text': ref_content
                    })
        
        # 如果模式1失败，尝试模式2
        if not references:
            matches = list(pattern2.finditer(text))
            for match in matches:
                ref_num = match.group(1)
                ref_content = match.group(2).strip()
                ref_content = re.sub(r'\s+', ' ', ref_content)
                
                if ref_content and len(ref_content) > 15 and not self._is_table_row(ref_content):
                    references.append({
                        'number': ref_num,
                        'text': ref_content
                    })
        
        # 如果还是失败，尝试简单分割
        if not references:
            # 简单按 [N] 分割
            parts = re.split(r'\[(\d+)\]', text)
            if len(parts) > 2:
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        ref_num = parts[i]
                        ref_content = parts[i + 1].strip()
                        ref_content = re.sub(r'\s+', ' ', ref_content)
                        
                        # 限制到下一条之前
                        if i + 2 < len(parts):
                            next_ref_idx = parts[i + 2].find('[')
                            if next_ref_idx > 0:
                                ref_content = ref_content[:next_ref_idx]
                        
                        if ref_content and len(ref_content) > 15 and not self._is_table_row(ref_content):
                            references.append({
                                'number': ref_num,
                                'text': ref_content
                            })
        
        return references
    
    def _parse_reference_lines(self, lines: List[str]) -> List[Dict]:
        """解析参考文献行，处理双栏布局"""
        references = []
        current_ref = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测参考文献编号
            num_match = re.match(r'^\[?(\d+)\]?[.\s]+', line)
            
            if num_match:
                # 保存前一条参考文献
                if current_ref:
                    references.append(current_ref)
                
                ref_num = num_match.group(1)
                ref_text = line[num_match.end():].strip()
                
                if ref_text and len(ref_text) > 5 and not self._is_table_row(ref_text):
                    current_ref = {
                        'number': ref_num,
                        'text': re.sub(r'\s+', ' ', ref_text)
                    }
            elif current_ref:
                # 继续前一条参考文献（跨行情况）
                current_ref['text'] += ' ' + re.sub(r'\s+', ' ', line)
        
        # 保存最后一条
        if current_ref:
            references.append(current_ref)
        
        return references
    
    def _is_table_row(self, text: str) -> bool:
        """检测是否为表格行"""
        # 表格行特征：包含多个制表符、或者多列短文本用空格分隔
        if '\t' in text:
            return True
        
        # 检测是否像表格行（多列等长文本）
        parts = text.split()
        if len(parts) >= 3:
            # 检查是否有等长列
            if len(set(len(p) for p in parts)) <= 2:
                return True
        
        # 表格常见关键词
        table_keywords = ['accuracy', 'precision', 'recall', 'fps', 'map', 'iou']
        text_lower = text.lower()
        if all(kw in text_lower for kw in ['accuracy', '%']) or \
           all(kw in text_lower for kw in ['method', '%']):
            return True
        
        return False
    
    def save_all(self) -> Dict:
        """执行所有提取并保存"""
        result = {
            "metadata": self.extract_metadata(),
            "images": self.extract_images(),
            "tables": self.extract_tables(),
            "formulas": self.extract_formulas(),
            "references": self.extract_references(),
            "citations": self.extract_citations()
        }
        
        # 文本内容
        result["text_by_page"] = self.extract_text_by_page()
        result["text_by_sections"] = self.extract_text_by_sections()
        
        # 保存为JSON
        output_file = self.output_dir / "extracted_content.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"提取完成!")
        print(f"- 页数: {result['metadata']['page_count']}")
        print(f"- 图片: {len(result['images'])}")
        print(f"- 表格: {len(result['tables'])}")
        print(f"- 公式候选: {len(result['formulas'])}")
        print(f"- 引用数量: {len(result['citations'])}")
        print(f"- 内容已保存至: {output_file}")
        
        return result
    
    def close(self):
        """关闭PDF"""
        self.doc.close()
        self.pdf.close()


def main():
    parser = argparse.ArgumentParser(
        description="从PDF学术论文中提取内容"
    )
    parser.add_argument(
        "input_pdf",
        help="输入的PDF文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="输出目录 (默认: output)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_pdf):
        print(f"错误: 文件不存在: {args.input_pdf}")
        sys.exit(1)
    
    extractor = PDFExtractor(args.input_pdf, args.output)
    extractor.save_all()
    extractor.close()


if __name__ == "__main__":
    main()
