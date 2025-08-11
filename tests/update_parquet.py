#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新parquet表格，添加拉普兰德的参考音频信息
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

def update_parquet_with_lappland():
    """更新parquet表格，添加拉普兰德的音频信息"""
    
    # 读取现有的parquet文件
    parquet_path = os.path.join('lib', 'ref', 'table.parquet')
    df = pd.read_parquet(parquet_path)
    
    print(f"原始表格行数: {len(df)}")
    print(f"原始表格列数: {len(df.columns)}")
    
    # 检查是否已经存在拉普兰德的记录
    existing_lappland = df[df['char_id'] == 'char_001_lappland']
    if not existing_lappland.empty:
        print(f"已存在 {len(existing_lappland)} 条拉普兰德的记录")
        print("现有记录:")
        for _, row in existing_lappland.iterrows():
            print(f"  ID: {row['id']}, 语音文本: {row['voice_text'][:50]}...")
    
    # 查看现有记录的数据类型作为参考
    sample_row = df.iloc[0]
    print(f"\n参考数据类型:")
    for col in df.columns:
        print(f"  {col}: {type(sample_row[col])} = {sample_row[col]}")
    
    # 创建新的拉普兰德记录，使用与现有数据相同的数据类型
    new_record = {
        'id': 'char_001_lappland_CN_001',
        'char_id': 'char_001_lappland',
        'voice_actor_name': '拉普兰德',
        'char_word_id': 'lappland_001',
        'lock_description': '',  # 使用空字符串
        'place_type': 'HOME_PLACE',  # 使用与现有数据相同的值
        'unlock_type': 'DIRECT',  # 使用与现有数据相同的值
        'voice_asset': 'char_001_lappland/CN_001',  # 使用正确的格式
        'voice_id': 'CN_001',
        'voice_index': 1,
        'voice_text': '哟，博士。就算我把武器带进这里，你也会原谅我的对吧。那我就坐在这里了。',
        'voice_title': '任命助理',  # 使用与现有数据相同的值
        'voice_type': 'ONLY_TEXT',  # 使用与现有数据相同的值
        'word_key': 'char_001_lappland',  # 使用与现有数据相同的格式
        'file_url': 'https://torappu.prts.wiki/assets/audio/voice_cn/char_001_lappland.wav',
        'time': 3.5,  # 假设音频时长3.5秒
        'sample_rate': 44100,  # 使用与现有数据相同的采样率
        'frames': 154350,  # 44100 * 3.5
        'channels': 1,
        'filename': 'char_001_lappland.wav',  # 使用正确的文件名格式
        'mimetype': 'audio/x-wav',
        'file_size': 154000  # 假设文件大小
    }
    
    # 检查是否已存在相同ID的记录
    if new_record['id'] not in df['id'].values:
        # 创建新的DataFrame，确保数据类型一致
        new_df = pd.DataFrame([new_record])
        
        # 确保数据类型与现有数据一致
        for col in df.columns:
            if col in new_df.columns:
                new_df[col] = new_df[col].astype(df[col].dtype)
        
        # 添加新记录
        df_updated = pd.concat([df, new_df], ignore_index=True)
        
        # 保存更新后的parquet文件
        df_updated.to_parquet(parquet_path, index=False)
        
        print(f"✓ 成功添加拉普兰德记录")
        print(f"更新后表格行数: {len(df_updated)}")
        print(f"新记录ID: {new_record['id']}")
        print(f"音频文件: {new_record['filename']}")
        print(f"语音文本: {new_record['voice_text']}")
        
        # 验证更新
        df_verify = pd.read_parquet(parquet_path)
        lappland_records = df_verify[df_verify['char_id'] == 'char_001_lappland']
        print(f"验证: 现在有 {len(lappland_records)} 条拉普兰德记录")
        
    else:
        print("⚠️ 记录已存在，无需重复添加")
    
    return df_updated if 'df_updated' in locals() else df

def test_lappland_search():
    """测试拉普兰德的搜索功能"""
    print("\n=== 测试拉普兰德搜索功能 ===")
    
    # 导入loader模块
    import sys
    sys.path.append(os.path.join('lib', 'ref'))
    from loader import find_rows_by_char, find_audio_by_char_name
    
    # 测试搜索
    test_names = ["拉普兰德", "Lappland", "lappland"]
    
    for name in test_names:
        print(f"\n--- 搜索: {name} ---")
        
        # 查找语音记录
        rows = find_rows_by_char(name)
        print(f"找到 {len(rows)} 条语音记录")
        
        if len(rows) > 0:
            # 显示匹配的char_id
            unique_char_ids = rows['char_id'].unique()
            print(f"匹配的char_id: {list(unique_char_ids)}")
            
            # 显示语音文本
            for i, (_, row) in enumerate(rows.head(3).iterrows()):
                print(f"  {i+1}. {row['voice_text'][:100]}...")
            
            # 查找音频文件
            audio_files = find_audio_by_char_name(name, limit=5)
            print(f"找到 {len(audio_files)} 个音频文件")
            for i, file_path in enumerate(audio_files[:3]):
                print(f"  {i+1}. {os.path.basename(file_path)}")
        else:
            print("未找到语音记录")

if __name__ == "__main__":
    # 更新parquet文件
    update_parquet_with_lappland()
    
    # 测试搜索功能
    test_lappland_search() 