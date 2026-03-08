#!/usr/bin/env python3
"""从 extracted_content.json 的 text_by_sections['references'] 解析参考文献并生成 references.bib 与 citation 映射。"""
import json
import re
import sys
import os

# 允许从项目根或 pdf-to-latex 目录运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert_references import ReferenceConverter


def split_acm_refs(text: str) -> list:
    """将 ACM 风格参考文献文本拆分为单条。无编号时按「作者. 年份.」或「作者,」后的换行分界。"""
    if not text or len(text) < 50:
        return []
    # 先尝试按 ".\nName" 分界（新一条常以大写名字开头）
    parts = re.split(r'\.\s*\n\s*([A-Z][a-zA-Z\u00c0-\u024f]+(?:et\s+al\.|,))', text)
    refs = []
    current = []
    for i, p in enumerate(parts):
        if re.match(r'^[A-Z][a-zA-Z\u00c0-\u024f]+(?:et\s+al\.|,)$', p.strip()):
            if current:
                refs.append((' '.join(current)).strip())
            current = [p]
        else:
            current.append(p)
    if current:
        refs.append((' '.join(current)).strip())
    # 过滤：至少包含 4 位年份
    refs = [r for r in refs if re.search(r'\b(19|20)\d{2}\b', r) and len(r) > 30]
    return refs


def main():
    extracted_dir = sys.argv[1] if len(sys.argv) > 1 else 'extracted_split_and_fit'
    json_path = os.path.join(extracted_dir, 'extracted_content.json')
    if not os.path.isfile(json_path):
        print(f'Not found: {json_path}')
        sys.exit(1)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    refs_data = data.get('references', [])
    if not refs_data and data.get('text_by_sections'):
        raw = data['text_by_sections'].get('references', '')
        refs_text = split_acm_refs(raw)
        refs_data = [{'number': str(i + 1), 'text': t} for i, t in enumerate(refs_text)]
    if not refs_data:
        print('No references to convert.')
        sys.exit(0)
    converter = ReferenceConverter()
    bibtex_entries, citation_map = converter.convert(refs_data)
    bib_path = os.path.join(extracted_dir, 'references.bib')
    with open(bib_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(bibtex_entries))
    print(f'BibTeX saved: {bib_path}')
    map_path = os.path.join(extracted_dir, 'citation_map.json')
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(citation_map, f, indent=2, ensure_ascii=False)
    print(f'Citation mapping saved: {map_path}')
    print('Mapping:')
    for num, key in sorted(citation_map.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        print(f'  [{num}] -> \\cite{{{key}}}')


if __name__ == '__main__':
    main()
