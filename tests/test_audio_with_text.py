#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音频和文本查找功能
"""

import sys
import os
sys.path.append(os.path.join('lib', 'ref'))

from loader import find_audio_with_text_by_char_name, find_audio_by_char_name

def test_audio_with_text():
    """测试音频和文本查找功能"""
    print("=== 测试音频和文本查找功能 ===")
    
    # 测试用例
    test_names = [
        "阿米娅",
        "银灰", 
        "能天使",
        "德克萨斯",
        "拉普兰德",
        "斩业星熊",  # 新干员，可能没有语音
    ]
    
    for name in test_names:
        print(f"\n--- 测试: {name} ---")
        
        # 使用新函数查找音频和文本
        results = find_audio_with_text_by_char_name(name, limit=3)
        print(f"找到 {len(results)} 个音频文件")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. 文件: {os.path.basename(result['file_path'])}")
            print(f"     文本: {result['voice_text'][:100]}...")
        
        # 对比旧函数
        old_results = find_audio_by_char_name(name, limit=3)
        print(f"旧函数找到 {len(old_results)} 个音频文件")
        for i, file_path in enumerate(old_results[:2]):
            print(f"     {i+1}. {os.path.basename(file_path)}")

if __name__ == "__main__":
    test_audio_with_text() 