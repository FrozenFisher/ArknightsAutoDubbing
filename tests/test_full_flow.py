#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的TTS流程
"""

import sys
import os
sys.path.append(os.path.join('lib', 'ref'))
sys.path.append('lib')

import pandas as pd
from lib.ref.loader import find_audio_with_text_by_char_name
from tts_service import SiliconFlowTTS

def test_full_tts_flow():
    """测试完整的TTS流程"""
    print("=== 测试完整TTS流程 ===")
    
    # 测试用例
    test_cases = [
        ("阿米娅", "博士，您工作辛苦了。"),
        ("银灰", "消磨时间尚有更好的方法。"),
        ("能天使", "老板，安排点差事给我们吧~"),
        ("德克萨斯", "我仍会保护你的安全，博士。"),
    ]
    
    # 初始化TTS服务
    tts = SiliconFlowTTS()
    if not tts.api_key:
        print("⚠️ 未检测到TTS API Key，跳过TTS测试")
        return
    
    for name_text, content_text in test_cases:
        print(f"\n--- 测试: {name_text} ---")
        print(f"内容: {content_text}")
        
        # 1. 查找参考音频和文本
        ref_results = find_audio_with_text_by_char_name(name_text, limit=1, fallback_url=False)
        
        if ref_results:
            ref_data = ref_results[0]
            ref_path = ref_data['file_path']
            ref_text = ref_data['voice_text']
            
            print(f"✓ 找到参考音频: {os.path.basename(ref_path)}")
            print(f"✓ 参考文本: {ref_text[:50]}...")
            
            # 2. 确保音色存在
            voice_uri = tts.ensure_voice(name_key=name_text, wav_path=ref_path, ref_text=ref_text)
            
            if voice_uri:
                print(f"✓ 音色URI: {voice_uri}")
                
                # 3. 合成语音
                audio_bytes = tts.synthesize(content_text, voice_uri=voice_uri)
                
                if audio_bytes:
                    print(f"✓ TTS合成成功，音频大小: {len(audio_bytes)} 字节")
                    
                    # 保存音频文件
                    os.makedirs('TEMP', exist_ok=True)
                    import datetime
                    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    out_path = os.path.abspath(os.path.join('TEMP', f'tts_{name_text}_{ts}.wav'))
                    
                    with open(out_path, 'wb') as f:
                        f.write(audio_bytes)
                    
                    print(f"✓ 音频已保存: {out_path}")
                else:
                    print("✗ TTS合成失败")
            else:
                print("✗ 音色上传失败")
        else:
            print("✗ 未找到参考音频")

def test_all_operators():
    """测试所有干员的音频文件查找功能，找出无法找到的干员"""
    
    # 读取干员CSV文件
    try:
        df = pd.read_csv('lib/operators.csv')
    except FileNotFoundError:
        print("错误：找不到 lib/operators.csv 文件")
        return
    
    # 存储结果
    found_operators = []
    not_found_operators = []
    
    print("开始轮询所有干员...")
    print("=" * 50)
    
    # 轮询每个干员
    for index, row in df.iterrows():
        chinese_name = row['chinese_name']
        english_name = row['english_name']
        
        # 跳过空行
        if pd.isna(chinese_name) or chinese_name.strip() == '':
            continue
            
        print(f"正在查询: {chinese_name} ({english_name})")
        
        # 查找音频文件
        try:
            result = find_audio_with_text_by_char_name(chinese_name, limit=1)
            
            if result and len(result) > 0:
                found_operators.append({
                    'chinese_name': chinese_name,
                    'english_name': english_name,
                    'file_count': len(result),
                    'first_file': result[0]['file_path'] if result else None
                })
                print(f"  ✓ 找到 {len(result)} 个音频文件")
            else:
                not_found_operators.append({
                    'chinese_name': chinese_name,
                    'english_name': english_name
                })
                print(f"  ✗ 未找到音频文件")
                
        except Exception as e:
            not_found_operators.append({
                'chinese_name': chinese_name,
                'english_name': english_name,
                'error': str(e)
            })
            print(f"  ✗ 查询出错: {e}")
    
    # 输出统计结果
    print("\n" + "=" * 50)
    print("统计结果:")
    print(f"总干员数: {len(df)}")
    print(f"找到音频文件的干员数: {len(found_operators)}")
    print(f"未找到音频文件的干员数: {len(not_found_operators)}")
    
    # 详细列出未找到的干员
    if not_found_operators:
        print("\n未找到音频文件的干员列表:")
        print("-" * 30)
        for i, op in enumerate(not_found_operators, 1):
            error_info = f" (错误: {op['error']})" if 'error' in op else ""
            print(f"{i:3d}. {op['chinese_name']} ({op['english_name']}){error_info}")
    
    # 保存结果到文件
    try:
        # 保存未找到的干员到CSV
        if not_found_operators:
            not_found_df = pd.DataFrame(not_found_operators)
            not_found_df.to_csv('not_found_operators.csv', index=False, encoding='utf-8')
            print(f"\n未找到的干员列表已保存到: not_found_operators.csv")
        
        # 保存找到的干员到CSV
        if found_operators:
            found_df = pd.DataFrame(found_operators)
            found_df.to_csv('found_operators.csv', index=False, encoding='utf-8')
            print(f"找到的干员列表已保存到: found_operators.csv")
            
    except Exception as e:
        print(f"保存结果文件时出错: {e}")
    
    return found_operators, not_found_operators

if __name__ == "__main__":
    test_full_tts_flow() 
    found, not_found = test_all_operators() 