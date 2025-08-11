#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HTML解析功能
"""

from bs4 import BeautifulSoup
import re
import os
import csv
from typing import Dict, List

def parse_operators_from_html(html_content: str) -> List[Dict]:
    """从HTML内容解析干员信息"""
    soup = BeautifulSoup(html_content, 'html.parser')
    operators = []
    
    # 查找所有short-container类的元素
    short_containers = soup.find_all(class_='short-container')
    print(f"找到 {len(short_containers)} 个short-container")
    
    for i, container in enumerate(short_containers):
        print(f"\n=== 分析第 {i+1} 个容器 ===")
        
        # 在每个short-container中查找name类的元素
        name_elements = container.find_all(class_='name')
        print(f"  找到 {len(name_elements)} 个name元素")
        
        for j, name_element in enumerate(name_elements):
            # 获取name元素下的所有div子元素
            div_elements = name_element.find_all('div')
            print(f"    name[{j}] 包含 {len(div_elements)} 个div子元素")
            
            # 根据固定顺序：第一个是中文名，第二个是英文名
            chinese_name = ""
            english_name = ""
            
            for k, div in enumerate(div_elements):
                text = div.get_text().strip()
                if text:
                    print(f"      div[{k}]: '{text}'")
                    
                    if k == 1:  # 第一个div是中文名
                        chinese_name = text
                    elif k == 2:  # 第二个div是英文名
                        english_name = text
                    # 忽略其他div（如代号等）
            
            print(f"  解析结果: 中文名='{chinese_name}', 英文名='{english_name}'")
            
            # 添加到结果中
            if chinese_name:
                operators.append({
                    'chinese_name': chinese_name,
                    'english_name': english_name,
                    'url': f"https://prts.wiki/w/{chinese_name}"
                })
                print(f"  ✓ 添加: {chinese_name} - {english_name}")
    
    return operators

def save_to_csv(operators: List[Dict], filename: str = "operators.csv"):
    """保存干员信息到CSV文件"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['chinese_name', 'english_name', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 写入表头
            writer.writeheader()
            
            # 写入数据
            for operator in operators:
                writer.writerow(operator)
        
        print(f"\n✓ CSV文件已保存: {filename}")
        print(f"  包含 {len(operators)} 个干员信息")
        
    except Exception as e:
        print(f"✗ 保存CSV文件失败: {e}")

# 测试HTML片段
test_html = os.path.join(os.path.dirname(__file__), 'input.html')
with open(test_html, 'r', encoding='utf-8') as f:
    test_html = f.read()

if __name__ == "__main__":
    print("开始测试HTML解析...")
    operators = parse_operators_from_html(test_html)
    
    print(f"\n=== 最终结果 ===")
    print(f"总共解析出 {len(operators)} 个干员:")
    for op in operators:
        print(f"  {op['chinese_name']} - {op['english_name']}")
    
    # 保存到CSV文件
    save_to_csv(operators, "operators.csv") 