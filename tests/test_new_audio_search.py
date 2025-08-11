#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的音频搜索功能
"""

import sys
import os
sys.path.append(os.path.join('lib', 'ref'))

from loader import find_audio_with_text_by_char_name, find_new_audio_by_char_name, get_chinese_text_from_csv

def test_new_audio_search():
    """测试新的音频搜索功能"""
    print("=== 测试新的音频搜索功能 ===")
    
    # 测试用例
    test_names = [
        "阿",
        "12F",
        "银灰",  # 可能没有新音频
        "能天使",  # 可能没有新音频
    ]
    
    for name in test_names:
        print(f"\n--- 测试: {name} ---")
        
        # 使用新函数查找音频和文本
        results = find_audio_with_text_by_char_name(name, limit=34)
        print(f"找到 {len(results)} 个音频文件")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. 文件: {os.path.basename(result['file_path'])}")
            print(f"     文本: {result['voice_text'][:100]}...")
            print(f"     路径: {result['file_path']}")

def test_csv_lookup():
    """测试CSV文件查找功能"""
    print("\n=== 测试CSV文件查找功能 ===")
    
    # 测试从CSV文件中查找中文文本
    test_cases = [
        ("阿", "5274c881a4cf6ffc12a12222b6ddbecf"),  # 干员报到
        ("阿", "9440b2c32ed37f5a2b3793ca1fcea1a3"),  # 闲置
        ("12F", "e71cd60e6c57a241e7702a0e1864fa47"),  # 干员报到
    ]
    
    for operator_name, md5_hash in test_cases:
        chinese_text = get_chinese_text_from_csv(operator_name, md5_hash)
        print(f"{operator_name} - {md5_hash}: {chinese_text[:50]}...")

def test_filename_parsing():
    """测试文件名解析功能"""
    print("\n=== 测试文件名解析功能 ===")
    
    test_filenames = [
        "阿_干员报到_5274c881a4cf6ffc12a12222b6ddbecf.wav",
        "12F_干员报到_e71cd60e6c57a241e7702a0e1864fa47.wav",
        "阿_信赖提升后交谈3_fbf2a16ad6c621919a1d5f9e6e60ea56.wav",
    ]
    
    for filename in test_filenames:
        parts = filename.replace('.wav', '').split('_')
        if len(parts) >= 3:
            md5_hash = parts[-1]
            operator_name = parts[0]
            title = '_'.join(parts[1:-1])
            print(f"文件名: {filename}")
            print(f"  干员名: {operator_name}")
            print(f"  标题: {title}")
            print(f"  MD5: {md5_hash}")
            print()

if __name__ == "__main__":
    test_filename_parsing()
    test_csv_lookup()
    test_new_audio_search() 