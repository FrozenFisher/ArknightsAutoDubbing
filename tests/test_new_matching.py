#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的匹配逻辑
"""

import sys
import os
sys.path.append(os.path.join('lib', 'ref'))

from loader import find_operator_by_name, find_rows_by_char, find_audio_by_char_name
import pandas as pd

def test_matching_logic():
    """测试新的匹配逻辑"""
    print("=== 测试新的匹配逻辑 ===")
    
    # 测试用例
    test_cases = [
        "阿米娅",      # 应该匹配 char_002_amiya
        "银灰",        # 应该匹配 char_201_silverash
        "能天使",      # 应该匹配 char_103_angel
        "德克萨斯",    # 应该匹配 char_101_txsi
        "拉普兰德",    # 应该匹配 char_102_lappland
        "斩业星熊",    # 新干员，可能没有语音
        "遥",          # 新干员，可能没有语音
    ]
    
    for test_name in test_cases:
        print(f"\n--- 测试: {test_name} ---")
        
        # 1. 查找干员信息
        operator_info = find_operator_by_name(test_name)
        if operator_info:
            print(f"✓ 找到干员: {operator_info['chinese_name']} - {operator_info['english_name']}")
            
            # 2. 查找语音记录
            rows = find_rows_by_char(test_name)
            print(f"✓ 找到 {len(rows)} 条语音记录")
            
            if len(rows) > 0:
                # 显示匹配的char_id
                unique_char_ids = rows['char_id'].unique()
                print(f"  匹配的char_id: {list(unique_char_ids)}")
                
                # 显示示例语音文本
                sample_row = rows.iloc[0]
                print(f"  示例语音: {sample_row['voice_text'][:100]}...")
                
                # 3. 查找音频文件
                audio_files = find_audio_by_char_name(test_name, limit=3)
                print(f"✓ 找到 {len(audio_files)} 个音频文件")
                for i, file_path in enumerate(audio_files[:2]):
                    print(f"  {i+1}. {os.path.basename(file_path)}")
            else:
                print("✗ 未找到语音记录")
        else:
            print(f"✗ 未找到干员信息: {test_name}")

def test_char_id_matching():
    """测试char_id匹配逻辑"""
    print("\n=== 测试char_id匹配逻辑 ===")
    
    # 从parquet文件读取数据
    import pandas as pd
    parquet_path = os.path.join('lib', 'ref', 'table.parquet')
    df = pd.read_parquet(parquet_path)
    
    # 获取所有char_id
    unique_char_ids = df['char_id'].unique()
    print(f"总共有 {len(unique_char_ids)} 个唯一的char_id")
    
    # 测试一些已知的映射
    test_mappings = [
        ("阿米娅", "amiya"),
        ("银灰", "silverash"),
        ("能天使", "angel"),
        ("德克萨斯", "txsi"),
        ("拉普兰德", "lappland"),
    ]
    
    for chinese_name, expected_suffix in test_mappings:
        print(f"\n--- 测试映射: {chinese_name} -> {expected_suffix} ---")
        
        # 查找干员信息
        operator_info = find_operator_by_name(chinese_name)
        if operator_info:
            english_name = operator_info['english_name']
            english_name_clean = english_name.lower().replace(' ', '').replace('-', '').replace('_', '')
            print(f"英文名: {english_name}")
            print(f"清理后: {english_name_clean}")
            
            # 查找匹配的char_id
            matching_char_ids = []
            for char_id in unique_char_ids:
                if '_' in char_id:
                    char_suffix = char_id.split('_', 2)[-1]
                    char_suffix_clean = char_suffix.lower()
                    
                    if (english_name_clean in char_suffix_clean or 
                        char_suffix_clean in english_name_clean or
                        any(word in char_suffix_clean for word in english_name_clean.split())):
                        matching_char_ids.append(char_id)
            
            print(f"匹配的char_id: {matching_char_ids}")

if __name__ == "__main__":
    test_matching_logic()
    test_char_id_matching() 