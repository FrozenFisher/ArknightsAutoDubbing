#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的loader功能
"""

import sys
import os
sys.path.append(os.path.join('lib', 'ref'))

from loader import find_operator_by_name, find_rows_by_char, find_audio_by_char_name

def test_operator_lookup():
    """测试干员查找功能"""
    print("=== 测试干员查找功能 ===")
    
    test_names = [
        "斩业星熊",
        "Hoshiguma the Breacher", 
        "遥",
        "Haruka",
        "阿米娅",
        "Amiya",
        "银灰",
        "SilverAsh",
        "不存在的干员"
    ]
    
    for name in test_names:
        result = find_operator_by_name(name)
        if result:
            print(f"✓ '{name}' -> {result['chinese_name']} - {result['english_name']}")
        else:
            print(f"✗ '{name}' -> 未找到")

def test_char_search():
    """测试干员语音搜索功能"""
    print("\n=== 测试干员语音搜索功能 ===")
    
    test_names = [
        "斩业星熊",
        "Hoshiguma",
        "遥", 
        "Haruka",
        "阿米娅",
        "Amiya"
    ]
    
    for name in test_names:
        rows = find_rows_by_char(name)
        print(f"'{name}' -> 找到 {len(rows)} 条语音记录")
        if len(rows) > 0:
            print(f"  示例: {rows.iloc[0]['voice_text'][:50]}...")

def test_audio_search():
    """测试音频文件查找功能"""
    print("\n=== 测试音频文件查找功能 ===")
    
    test_names = [
        "斩业星熊",
        "Hoshiguma",
        "遥",
        "Haruka"
    ]
    
    for name in test_names:
        audio_files = find_audio_by_char_name(name, limit=3)
        print(f"'{name}' -> 找到 {len(audio_files)} 个音频文件")
        for i, file_path in enumerate(audio_files[:2]):
            print(f"  {i+1}. {os.path.basename(file_path)}")

if __name__ == "__main__":
    test_operator_lookup()
    test_char_search()
    test_audio_search() 