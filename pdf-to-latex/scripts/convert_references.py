#!/usr/bin/env python3
"""
参考文献转换脚本
将PDF提取的参考文献转换为BibTeX格式，并转换正文中的数字引用
"""

import re
import json
import argparse
import os
from typing import Dict, List, Tuple, Optional  # noqa: F401 Optional used in type hint
from pathlib import Path


class ReferenceConverter:
    """参考文献转换器"""

    # 会议名称到缩写的映射
    CONFERENCE_ABBREVS = {
        'conference on computer vision and pattern recognition': 'CVPR',
        'international conference on computer vision': 'ICCV',
        'european conference on computer vision': 'ECCV',
        'conference on neural information processing systems': 'NeurIPS',
        'international conference on learning representations': 'ICLR',
        'international conference on machine learning': 'ICML',
        'conference on computer vision and pattern recognition': 'CVPR',
        'international conference on 3d vision': '3DV',
        ' asian conference on computer vision': 'ACCV',
    }

    # 期刊名称映射
    JOURNAL_ABBREVS = {
        'ieee transactions on pattern analysis and machine intelligence': 'IEEE TPAMI',
        'international journal of computer vision': 'IJCV',
        'computer vision and image understanding': 'CVIU',
        'pattern recognition': 'PR',
    }

    def __init__(self):
        self.references = []
        self.citation_map = {}  # 数字 -> BibTeX key

    def extract_references_from_text(self, text: str) -> List[str]:
        """从文本中提取参考文献列表"""
        references = []

        # 查找References部分
        ref_section_match = re.search(
            r'(?:References|Bibliography|Literature\s+Cited)\s*[:\.]?\s*\n',
            text,
            re.IGNORECASE
        )

        if not ref_section_match:
            return []

        ref_text = text[ref_section_match.end():]

        # 分割参考文献 - 支持多种格式
        # 格式1: [1] Author...
        # 格式2: 1. Author...
        # 格式3: (1) Author...

        # 按编号分割
        ref_pattern = re.compile(
            r'(?:^|\n)\s*'
            r'(?:\[\s*(\d+)\s*\]|(\d+)\.|\((\d+)\))\s+'
            r'([A-Z].*)',
            re.MULTILINE
        )

        matches = ref_pattern.findall(ref_text)

        for match in matches:
            # match[0]是编号(可能在[1]中), match[1]是纯数字, match[2]是(数字), match[3]是内容
            ref_num = match[0] or match[1] or match[2]
            ref_content = match[3].strip()

            # 清理内容
            ref_content = re.sub(r'\s+', ' ', ref_content)
            if ref_content:
                references.append({
                    'number': ref_num,
                    'text': ref_content
                })

        return references

    def _normalize_author_bibtex(self, author_block: str) -> str:
        """将 'Last, F.; Last2, F.; and Last3, F.' 转为 BibTeX 的 'Last, F. and Last2, F. and Last3, F.'"""
        s = author_block.strip()
        s = re.sub(r';\s*and\s+', ' and ', s, flags=re.IGNORECASE)
        s = re.sub(r';\s*', ' and ', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    def _parse_aaai_style(self, ref_text: str) -> Optional[Dict]:
        """AAAI/学术格式: Authors. Year. Title. In Proceedings / arXiv / ...
        作者块到第一个 ' 19XX. ' 或 ' 20XX. ' 为止，其后为 Year. Title. Venue"""
        # 第一个 “ 年份. ”（空格+四位数年份+点+空格）分隔作者与 (年份+标题+出处)
        year_match = re.search(r'\s+(19\d{2}|20\d{2})\.\s+', ref_text)
        if not year_match:
            return None
        year = year_match.group(1)
        author_block = ref_text[:year_match.start()].strip()
        after_year = ref_text[year_match.end():].strip()
        # 作者块：去掉双栏混入的 “年份.标题” 片段（如 2017.High-Resolution...），保留 “F. S.” 等缩写
        author_block = re.sub(r'\s+', ' ', author_block)
        author_block = re.sub(r'(19|20)\d{2}\.[A-Z][a-zA-Z\-]*(?:\s+[A-Za-z\-]+)*', '', author_block)
        author_block = re.sub(r'\s+', ' ', author_block).strip()
        # 去掉末尾残留的 “and ” 或 “; ”（无后续作者时）
        author_block = re.sub(r'[;\s]+$', '', author_block)
        if not re.match(r'^[A-Z]', author_block):
            return None
        # 标题结束于 Venue 开头，或下一个 “ 年份. ”（双栏时下一条文献）
        venue_start = re.search(
            r'\s+In\s+(?:Proc\.|Proceed(?:ings?)?|the\s+)|\.?\s*arXiv\s+|Conference\s+on\s+|International\s+Conference\s+|Springer\s*\.',
            after_year,
            re.IGNORECASE
        )
        next_ref_year = re.search(r'\s+(19\d{2}|20\d{2})\.\s+', after_year[10:])  # 跳过开头，避免误伤
        end_pos = len(after_year)
        if venue_start:
            end_pos = min(end_pos, venue_start.start())
        if next_ref_year:
            end_pos = min(end_pos, 10 + next_ref_year.start())
        title = after_year[:end_pos].strip()
        if not title:
            dot_venue = re.search(r'\.\s+(?:In\s+|Proc\.|Proceedings|arXiv)', after_year, re.IGNORECASE)
            title = (after_year[:dot_venue.start()].strip() if dot_venue else after_year[:200].strip())
        title = re.sub(r'\s+', ' ', title).strip()
        if len(title) < 2:
            return None
        return {
            'type': 'misc',
            'author': self._normalize_author_bibtex(author_block),
            'title': title,
            'year': year,
            'journal': '',
            'booktitle': '',
            'volume': '',
            'number': '',
            'pages': '',
            'doi': '',
            'url': '',
            'publisher': ''
        }

    def parse_reference(self, ref_text: str) -> Dict:
        """解析单条参考文献，提取各个字段。优先使用 AAAI 风格 (Authors. Year. Title. Venue)。"""
        result = {
            'type': 'misc',
            'author': '',
            'title': '',
            'journal': '',
            'booktitle': '',
            'year': '',
            'volume': '',
            'number': '',
            'pages': '',
            'doi': '',
            'url': '',
            'publisher': ''
        }

        # 优先尝试 AAAI 风格：Authors. Year. Title. Venue
        ref_one_line = re.sub(r'\s+', ' ', ref_text).strip()
        aaai = self._parse_aaai_style(ref_one_line)
        if aaai and len(aaai.get('author', '')) > 2 and len(aaai.get('title', '')) > 5:
            result.update(aaai)
        else:
            # 回退到原有逻辑（仅作备用）
            aaai = self._parse_aaai_style(ref_text)  # 未合并空白再试一次
            if aaai and len(aaai.get('author', '')) > 2 and len(aaai.get('title', '')) > 5:
                result.update(aaai)
            else:
                result['year'] = ''
                year_match = re.search(r'\b(19|20)\d{2}\b', ref_text)
                if year_match:
                    result['year'] = year_match.group()
                author_match = re.match(r'^([A-Z][a-zA-Z\s,\-\.]+?)(?:\.|,|\()', ref_text)
                if author_match:
                    result['author'] = author_match.group(1).strip()
                    result['author'] = re.sub(r',\s*$', '', result['author'])
                if result['author']:
                    after_author = ref_text[len(result['author']):]
                    after_author = re.sub(r'^[\s,\.]+', '', after_author)
                    title_end_match = re.search(
                        r'\.\s+(?:pp?|pages?|vol(?:ume)?|no\.|number|doi|http)',
                        after_author,
                        re.IGNORECASE
                    )
                    if title_end_match:
                        result['title'] = after_author[:title_end_match.start()].strip()
                    else:
                        period_match = re.search(r'\.\s+[A-Z]', after_author)
                        result['title'] = after_author[:period_match.start()].strip() if period_match else after_author[:100].strip()

        if not result['year']:
            year_match = re.search(r'\b(19|20)\d{2}\b', ref_text)
            if year_match:
                result['year'] = year_match.group()

        # 检测文献类型
        ref_lower = ref_text.lower()

        # arXiv
        if 'arxiv' in ref_lower or 'arXiv' in ref_text:
            result['type'] = 'misc'
            arxiv_match = re.search(r'arXiv:([\d\.]+)', ref_text, re.IGNORECASE)
            if arxiv_match:
                result['eprint'] = arxiv_match.group(1).replace('.', '').rstrip()

        # 会议论文
        for conf_keyword, conf_name in self.CONFERENCE_ABBREVS.items():
            if conf_keyword in ref_lower:
                result['type'] = 'inproceedings'
                result['booktitle'] = conf_name
                break

        # 期刊论文
        for journal_keyword, journal_name in self.JOURNAL_ABBREVS.items():
            if journal_keyword in ref_lower:
                result['type'] = 'article'
                result['journal'] = journal_name
                break

        # 如果没有检测到类型，尝试根据内容判断
        if result['type'] == 'misc':
            if 'proceedings' in ref_lower or 'conference' in ref_lower:
                result['type'] = 'inproceedings'
            elif 'journal' in ref_lower or 'vol' in ref_lower or 'no.' in ref_lower:
                result['type'] = 'article'

        # 提取页码
        pages_match = re.search(r'pp?\.\s*(\d+[-–]\d+)', ref_text, re.IGNORECASE)
        if pages_match:
            result['pages'] = pages_match.group(1)

        # 提取卷号
        volume_match = re.search(r'vol(?:ume)?\.?\s*(\d+)', ref_text, re.IGNORECASE)
        if volume_match:
            result['volume'] = volume_match.group(1)

        # 提取期号
        number_match = re.search(r'no\.?\s*(\d+)', ref_text, re.IGNORECASE)
        if number_match:
            result['number'] = number_match.group(1)

        # 提取DOI
        doi_match = re.search(r'doi[:\s]*10\.\S+', ref_text, re.IGNORECASE)
        if doi_match:
            result['doi'] = doi_match.group().replace('doi:', '').strip()

        # 提取URL
        url_match = re.search(r'https?://\S+', ref_text)
        if url_match:
            result['url'] = url_match.group()

        return result

    def generate_bibtex_key(self, parsed_ref: Dict) -> str:
        """生成BibTeX引用键"""
        # 格式: FirstAuthorYear
        if parsed_ref['author']:
            # 提取第一个作者的姓
            first_author = parsed_ref['author'].split(',')[0].split(' and ')[0]
            first_author = re.sub(r'[^a-zA-Z]', '', first_author).lower()
            year = parsed_ref.get('year', '')
            return f"{first_author}{year}" if year else first_author
        else:
            # 如果没有作者，使用随机键
            return f"ref{hash(parsed_ref['title']) % 10000}"

    def to_bibtex(self, parsed_ref: Dict, bib_key: str) -> str:
        """将解析的参考文献转换为BibTeX格式"""
        ref_type = parsed_ref.get('type', 'misc')

        lines = [f"@{ref_type}{{{bib_key},"]

        # 添加作者
        if parsed_ref.get('author'):
            # 转换为BibTeX格式: Author, A. and Author, B.
            author = parsed_ref['author']
            lines.append(f"  author = {{{author}}},")

        # 添加标题
        if parsed_ref.get('title'):
            lines.append(f"  title = {{{parsed_ref['title']}}},")

        # 添加年份
        if parsed_ref.get('year'):
            lines.append(f"  year = {{{parsed_ref['year']}}},")

        # 根据类型添加不同字段
        if ref_type == 'article':
            if parsed_ref.get('journal'):
                lines.append(f"  journal = {{{parsed_ref['journal']}}},")
        elif ref_type == 'inproceedings':
            if parsed_ref.get('booktitle'):
                lines.append(f"  booktitle = {{{parsed_ref['booktitle']}}},")

        if parsed_ref.get('volume'):
            lines.append(f"  volume = {{{parsed_ref['volume']}}},")
        if parsed_ref.get('number'):
            lines.append(f"  number = {{{parsed_ref['number']}}},")
        if parsed_ref.get('pages'):
            lines.append(f"  pages = {{{parsed_ref['pages']}}},")
        if parsed_ref.get('doi'):
            lines.append(f"  doi = {{{parsed_ref['doi']}}},")
        if parsed_ref.get('url'):
            lines.append(f"  url = {{{parsed_ref['url']}}},")
        if parsed_ref.get('eprint'):
            lines.append(f"  eprint = {{{parsed_ref['eprint']}}},")
            lines.append("  archiveprefix = {arXiv},")

        lines.append("}")
        return '\n'.join(lines)

    def convert(self, references_data: List[Dict]) -> Tuple[List[str], Dict]:
        """转换参考文献列表"""
        bibtex_entries = []
        citation_map = {}
        used_keys = set()

        for ref_data in references_data:
            # 处理字典格式 {"number": "1", "text": "..."}
            if isinstance(ref_data, dict):
                ref_text = ref_data.get('text', '')
                ref_number = ref_data.get('number', '')
            else:
                ref_text = str(ref_data)
                ref_number = ''
            
            parsed = self.parse_reference(ref_text)
            
            # 使用提取的number如果存在
            if ref_number:
                parsed['number'] = ref_number
            
            bib_key = self.generate_bibtex_key(parsed)

            # 处理重复key
            original_key = bib_key
            counter = 1
            while bib_key in used_keys:
                bib_key = f"{original_key}{chr(96 + counter)}"  # a, b, c...
                counter += 1
            used_keys.add(bib_key)

            bibtex = self.to_bibtex(parsed, bib_key)
            bibtex_entries.append(bibtex)

            # 建立映射
            citation_map[str(parsed.get('number', ''))] = bib_key

        return bibtex_entries, citation_map

    def convert_citations(self, latex_text: str, citation_map: Dict) -> str:
        """将LaTeX中的数字引用转换为BibTeX引用"""
        # 匹配 [1], [1,2], [1-3], [1, 2, 3] 等格式
        def replace_citation(match):
            nums = match.group(1)
            # 解析数字列表
            result_keys = []

            # 处理各种格式: 1,2-5,6
            parts = nums.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-')
                    result_keys.extend([str(i) for i in range(int(start), int(end) + 1)])
                else:
                    result_keys.append(part)

            # 转换为bib keys
            bib_keys = []
            for num in result_keys:
                if num in citation_map:
                    bib_keys.append(citation_map[num])
                else:
                    # 尝试不同的格式
                    for key in citation_map:
                        if str(key).strip() == num:
                            bib_keys.append(citation_map[key])
                            break

            if bib_keys:
                return f"\\cite{{{','.join(bib_keys)}}}"
            else:
                return match.group(0)

        # 替换 [数字] 格式
        result = re.sub(r'\[(\s*\d+(?:[\s,\-]\d+)*\s*)\]', replace_citation, latex_text)

        return result

    def parse_bibtex_file(self, bibtex_path: str) -> Dict[int, str]:
        """从BibTeX文件解析，建立数字->bibkey的映射"""
        citation_map = {}
        
        with open(bibtex_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配所有BibTeX条目
        # 格式: @article{key, 或 @inproceedings{geiger2012,
        entry_pattern = re.compile(
            r'@(\w+)\s*\{\s*([^,\s]+)\s*,',
            re.MULTILINE
        )
        
        matches = entry_pattern.findall(content)
        bib_keys = [key for _, key in matches]
        
        # 假设BibTeX中的顺序对应PDF中的引用顺序
        # 按出现顺序分配数字
        for i, key in enumerate(bib_keys, 1):
            citation_map[str(i)] = key
        
        return citation_map

    def create_citation_map_from_extracted(self, extracted_data: Dict, bibtex_path: str = None) -> Dict[int, str]:
        """从提取的数据和可选的BibTeX文件创建引用映射"""
        citation_map = {}
        
        # 1. 如果提供了BibTeX文件，直接从文件解析
        if bibtex_path and os.path.exists(bibtex_path):
            return self.parse_bibtex_file(bibtex_path)
        
        # 2. 从提取的参考文献生成
        references = extracted_data.get('references', [])
        
        for i, ref in enumerate(references, 1):
            # 使用第一作者的姓 + 年份作为key
            ref_text = ref.get('text', '')
            
            # 提取作者和年份
            year_match = re.search(r'\b(19|20)\d{2}\b', ref_text)
            year = year_match.group() if year_match else ''
            
            author_match = re.match(r'^([A-Z][a-zA-Z]+)', ref_text)
            author = author_match.group(1) if author_match else ''
            
            key = f"{author.lower()}{year}" if author and year else f"ref{i}"
            citation_map[str(i)] = key
        
        return citation_map


def main():
    parser = argparse.ArgumentParser(
        description="将参考文献转换为BibTeX格式"
    )
    parser.add_argument(
        "input_file",
        help="输入的JSON文件或文本文件"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出BibTeX文件路径"
    )
    parser.add_argument(
        "-t", "--tex-file",
        help="需要转换引用的LaTeX文件"
    )
    parser.add_argument(
        "--output-tex",
        help="转换引用后的LaTeX文件输出路径"
    )
    parser.add_argument(
        "-b", "--bibtex",
        help="已有的BibTeX文件，用于建立数字->bibkey映射"
    )

    args = parser.parse_args()

    converter = ReferenceConverter()
    citation_map = {}

    # 读取输入
    if args.input_file.endswith('.json'):
        with open(args.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'references' in data:
                references = data['references']
            elif isinstance(data, list):
                references = data
            else:
                print("错误: JSON格式不正确")
                return
            
            # 尝试从JSON获取引用映射（如果有的话）
            if isinstance(data, dict) and 'citations' in data:
                # 使用提取的引用信息
                citations = data['citations']
                for num, cit_info in citations.items():
                    # 尝试匹配文献
                    pass
    else:
        # 文本文件
        with open(args.input_file, 'r', encoding='utf-8') as f:
            text = f.read()
            refs = converter.extract_references_from_text(text)
            references = [r['text'] for r in refs]

    # 转换
    bibtex_entries, generated_map = converter.convert(references)
    
    # 优先使用BibTeX文件建立的映射
    if args.bibtex and os.path.exists(args.bibtex):
        citation_map = converter.parse_bibtex_file(args.bibtex)
    else:
        citation_map = generated_map

    # 保存BibTeX
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(bibtex_entries))
        print(f"BibTeX已保存至: {args.output}")

    # 转换LaTeX文件中的引用
    if args.tex_file and args.output_tex:
        with open(args.tex_file, 'r', encoding='utf-8') as f:
            latex_content = f.read()

        converted_latex = converter.convert_citations(latex_content, citation_map)

        with open(args.output_tex, 'w', encoding='utf-8') as f:
            f.write(converted_latex)

        print(f"转换后的LaTeX已保存至: {args.output_tex}")

    # 打印引用映射
    print("\n引用映射:")
    for num, key in citation_map.items():
        print(f"  [{num}] -> \\cite{{{key}}}")


if __name__ == "__main__":
    main()
