#!/usr/bin/env python3
"""
数学公式转换脚本
将PDF中的公式转换为LaTeX格式
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional

# 常用数学符号映射表
SYMBOL_MAP = {
    # 希腊字母
    'α': r'\alpha',
    'β': r'\beta', 
    'γ': r'\gamma',
    'δ': r'\delta',
    'ε': r'\epsilon',
    'ζ': r'\zeta',
    'η': r'\eta',
    'θ': r'\theta',
    'ι': r'\iota',
    'κ': r'\kappa',
    'λ': r'\lambda',
    'μ': r'\mu',
    'ν': r'\nu',
    'ξ': r'\xi',
    'π': r'\pi',
    'ρ': r'\rho',
    'σ': r'\sigma',
    'τ': r'\tau',
    'υ': r'\upsilon',
    'φ': r'\phi',
    'χ': r'\chi',
    'ψ': r'\psi',
    'ω': r'\omega',
    # 大写希腊字母
    'Γ': r'\Gamma',
    'Δ': r'\Delta',
    'Θ': r'\Theta',
    'Λ': r'\Lambda',
    'Ξ': r'\Xi',
    'Π': r'\Pi',
    'Σ': r'\Sigma',
    'Φ': r'\Phi',
    'Ψ': r'\Psi',
    'Ω': r'\Omega',
    # 运算符
    '×': r'\times',
    '÷': r'\div',
    '±': r'\pm',
    '∓': r'\mp',
    '√': r'\sqrt',
    '∛': r'\sqrt[3]',
    '∞': r'\infty',
    '≈': r'\approx',
    '≠': r'\neq',
    '≤': r'\leq',
    '≥': r'\geq',
    '≪': r'\ll',
    '≫': r'\gg',
    '≡': r'\equiv',
    '∝': r'\propto',
    # 集合
    '∈': r'\in',
    '∉': r'\notin',
    '⊂': r'\subset',
    '⊃': r'\supset',
    '⊆': r'\subseteq',
    '⊇': r'\supseteq',
    '∪': r'\cup',
    '∩': r'\cap',
    '∅': r'\emptyset',
    '∀': r'\forall',
    '∃': r'\exists',
    # 逻辑
    '∧': r'\land',
    '∨': r'\lor',
    '¬': r'\neg',
    '→': r'\rightarrow',
    '←': r'\leftarrow',
    '↔': r'\leftrightarrow',
    '⇒': r'\Rightarrow',
    '⇐': r'\Leftarrow',
    '⇔': r'\Leftrightarrow',
    # 其他
    '∂': r'\partial',
    '∇': r'\nabla',
    '∑': r'\sum',
    '∏': r'\prod',
    '∫': r'\int',
    '∬': r'\iint',
    '∮': r'\oint',
    '°': r'^\circ',
    '′': "'",
    '″': "''",
}


class FormulaConverter:
    """数学公式转换器"""
    
    def __init__(self):
        self.symbol_map = SYMBOL_MAP
    
    def unicode_to_latex(self, formula: str) -> str:
        """将Unicode数学符号转换为LaTeX"""
        result = formula
        
        # 按长度降序排序，避免部分替换
        sorted_symbols = sorted(self.symbol_map.keys(), key=len, reverse=True)
        
        for symbol in sorted_symbols:
            if symbol in result:
                result = result.replace(symbol, self.symbol_map[symbol])
        
        return result
    
    def detect_inline_or_display(self, formula: str, context: str = "") -> str:
        """检测公式是行内还是显示公式"""
        # 如果公式很长或包含某些模式，可能是显示公式
        display_indicators = [
            r'\sum',
            r'\int',
            r'\frac',
            r'\begin',
            r'&=',
            r'\\',
        ]
        
        is_display = any(indicator in formula for indicator in display_indicators)
        
        if is_display:
            # 确保被 $$ 或 \[ \] 包裹
            if not (formula.strip().startswith(r'\[') or 
                    formula.strip().startswith(r'$$')):
                formula = f"\\begin{{align*}}\n{formula}\n\\end{{align*}}"
        
        return formula
    
    def clean_formula(self, formula: str) -> str:
        """清理公式文本"""
        # 移除多余空白
        formula = re.sub(r'\s+', ' ', formula)
        
        # 修复常见问题
        # x^2 -> x^{2}
        formula = re.sub(r'(\w)\^(\d)(?!\})', r'\1^{\2}', formula)
        formula = re.sub(r'(\w)\^(\w)(?!\})', r'\1^{\2}', formula)
        
        # a_1 -> a_{1}
        formula = re.sub(r'(\w)_(\d)(?!\})', r'\1_{\2}', formula)
        formula = re.sub(r'(\w)_(\w)(?!\})', r'\1_{\2}', formula)
        
        return formula
    
    def convert(self, formula: str, context: str = "") -> str:
        """转换公式"""
        # 先转换为LaTeX符号
        result = self.unicode_to_latex(formula)
        
        # 清理公式
        result = self.clean_formula(result)
        
        # 检测类型
        result = self.detect_inline_or_display(result, context)
        
        return result
    
    def batch_convert(self, formulas: List[Dict]) -> List[Dict]:
        """批量转换公式"""
        results = []
        
        for item in formulas:
            formula = item.get("text", "")
            context = item.get("context", "")
            
            converted = self.convert(formula, context)
            
            results.append({
                **item,
                "latex": converted
            })
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="将数学公式转换为LaTeX格式"
    )
    parser.add_argument(
        "input_file",
        help="输入的JSON文件（包含公式列表）"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径"
    )
    
    args = parser.parse_args()
    
    # 读取输入
    with open(args.input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    converter = FormulaConverter()
    
    # 转换公式
    if isinstance(data, list):
        results = converter.batch_convert(data)
    elif isinstance(data, dict) and "formulas" in data:
        results = converter.batch_convert(data["formulas"])
    else:
        print("错误: 输入文件格式不正确")
        sys.exit(1)
    
    # 保存结果
    output_file = args.output or args.input_file.replace(".json", "_latex.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"转换完成! 结果已保存至: {output_file}")


if __name__ == "__main__":
    main()
