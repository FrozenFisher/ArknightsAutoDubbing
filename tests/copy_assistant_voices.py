#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复制所有干员的"任命助理"语音文件到发布目录
"""

import os
import shutil
import pandas as pd
import glob
from pathlib import Path

def copy_assistant_voices():
    """
    复制所有干员的"任命助理"语音文件到发布目录
    """
    # 定义路径
    voc_data_dir = Path("lib/voc_data")
    voc_dir = Path("lib/voc")
    voc_data_publish_dir = Path("lib/voc_data_publish")
    voc_publish_dir = Path("lib/voc_publish")
    
    # 创建发布目录
    voc_data_publish_dir.mkdir(exist_ok=True)
    voc_publish_dir.mkdir(exist_ok=True)
    
    # 获取所有干员语音数据文件
    voice_data_files = list(voc_data_dir.glob("voice_data_*.csv"))
    
    print(f"找到 {len(voice_data_files)} 个干员语音数据文件")
    
    copied_count = 0
    missing_count = 0
    missing_operators = []
    
    for voice_data_file in voice_data_files:
        try:
            # 读取CSV文件
            df = pd.read_csv(voice_data_file, encoding='utf-8')
            
            # 查找"任命助理"语音
            assistant_voice = df[df['title'] == '任命助理']
            
            if not assistant_voice.empty:
                # 获取干员名称和文件名
                operator_name = assistant_voice.iloc[0]['operator_name']
                local_filename = assistant_voice.iloc[0]['local_filename']
                
                # 源文件路径
                source_audio_file = voc_dir / local_filename
                source_csv_file = voice_data_file
                
                # 目标文件路径
                target_audio_file = voc_publish_dir / local_filename
                target_csv_file = voc_data_publish_dir / voice_data_file.name
                
                # 复制音频文件
                if source_audio_file.exists():
                    shutil.copy2(source_audio_file, target_audio_file)
                    print(f"✓ 已复制: {operator_name} - {local_filename}")
                    copied_count += 1
                else:
                    print(f"✗ 音频文件缺失: {operator_name} - {local_filename}")
                    missing_count += 1
                    missing_operators.append(operator_name)
                
                # 复制CSV文件
                shutil.copy2(source_csv_file, target_csv_file)
                
            else:
                print(f"⚠ 未找到任命助理语音: {voice_data_file.name}")
                
        except Exception as e:
            print(f"✗ 处理文件 {voice_data_file.name} 时出错: {e}")
            missing_count += 1
    
    # 创建汇总报告
    report_file = Path("assistant_voice_copy_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("任命助理语音复制报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"总处理文件数: {len(voice_data_files)}\n")
        f.write(f"成功复制: {copied_count}\n")
        f.write(f"缺失文件: {missing_count}\n\n")
        
        if missing_operators:
            f.write("缺失音频文件的干员:\n")
            for operator in missing_operators:
                f.write(f"  - {operator}\n")
    
    print(f"\n复制完成!")
    print(f"成功复制: {copied_count} 个音频文件")
    print(f"缺失文件: {missing_count} 个")
    print(f"详细报告已保存到: {report_file}")
    
    # 显示发布目录统计
    audio_files = list(voc_publish_dir.glob("*.wav"))
    csv_files = list(voc_data_publish_dir.glob("*.csv"))
    
    print(f"\n发布目录统计:")
    print(f"音频文件: {len(audio_files)} 个")
    print(f"CSV文件: {len(csv_files)} 个")

def verify_copy_results():
    """
    验证复制结果
    """
    voc_data_publish_dir = Path("lib/voc_data_publish")
    voc_publish_dir = Path("lib/voc_publish")
    
    if not voc_data_publish_dir.exists() or not voc_publish_dir.exists():
        print("发布目录不存在，请先运行复制脚本")
        return
    
    # 统计文件
    audio_files = list(voc_publish_dir.glob("*.wav"))
    csv_files = list(voc_data_publish_dir.glob("*.csv"))
    
    print("复制结果验证:")
    print(f"音频文件数量: {len(audio_files)}")
    print(f"CSV文件数量: {len(csv_files)}")
    
    # 检查音频文件大小
    total_size = sum(f.stat().st_size for f in audio_files)
    print(f"音频文件总大小: {total_size / 1024 / 1024:.2f} MB")
    
    # 显示前几个文件作为示例
    print("\n前5个音频文件:")
    for i, audio_file in enumerate(audio_files[:5]):
        size_mb = audio_file.stat().st_size / 1024 / 1024
        print(f"  {i+1}. {audio_file.name} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    print("开始复制干员任命助理语音文件...")
    copy_assistant_voices()
    
    print("\n" + "="*50)
    verify_copy_results() 