#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
干员资源完整性检查脚本
检查每个干员的语音数据文件和音频文件是否完整
"""

import os
import pandas as pd
from pathlib import Path
import argparse
from typing import Dict, List, Set
import json

class OperatorResourceChecker:
    def __init__(self, voc_data_dir: str = "lib/voc_data", voc_dir: str = "lib/voc"):
        self.voc_data_dir = Path(voc_data_dir)
        self.voc_dir = Path(voc_dir)
        self.operators_csv = Path("parsed_operators.csv")
        
        if not self.voc_data_dir.exists():
            raise FileNotFoundError(f"语音数据目录不存在: {self.voc_data_dir}")
        if not self.voc_dir.exists():
            raise FileNotFoundError(f"音频文件目录不存在: {self.voc_dir}")
        if not self.operators_csv.exists():
            raise FileNotFoundError(f"干员列表文件不存在: {self.operators_csv}")
    
    def get_all_operators(self) -> List[str]:
        """获取所有干员名称列表"""
        try:
            df = pd.read_csv(self.operators_csv)
            return df['display_name'].tolist()
        except Exception as e:
            print(f"读取干员列表失败: {e}")
            return []
    
    def get_operator_voice_data_files(self) -> Dict[str, str]:
        """获取所有干员语音数据文件"""
        voice_data_files = {}
        for file_path in self.voc_data_dir.glob("voice_data_*.csv"):
            operator_name = file_path.stem.replace("voice_data_", "")
            voice_data_files[operator_name] = str(file_path)
        return voice_data_files
    
    def get_operator_audio_files(self) -> Dict[str, Set[str]]:
        """获取所有干员音频文件"""
        audio_files = {}
        for file_path in self.voc_dir.glob("*.wav"):
            parts = file_path.stem.split("_")
            if len(parts) >= 2:
                operator_name = parts[0]
                if operator_name not in audio_files:
                    audio_files[operator_name] = set()
                audio_files[operator_name].add(file_path.name)
        return audio_files
    
    def check_operator_voice_data(self, operator_name: str, voice_data_file: str) -> Dict:
        """检查单个干员的语音数据完整性"""
        result = {
            "operator_name": operator_name,
            "voice_data_file": voice_data_file,
            "voice_data_exists": False,
            "voice_entries": 0,
            "missing_audio_files": [],
            "total_expected_audio": 0,
            "total_actual_audio": 0
        }
        
        try:
            if not os.path.exists(voice_data_file):
                result["error"] = "语音数据文件不存在"
                return result
            
            result["voice_data_exists"] = True
            df = pd.read_csv(voice_data_file)
            result["voice_entries"] = len(df)
            
            operator_audio_files = set()
            for file_path in self.voc_dir.glob(f"{operator_name}_*.wav"):
                operator_audio_files.add(file_path.name)
            
            result["total_actual_audio"] = len(operator_audio_files)
            result["total_expected_audio"] = len(df)
            
            missing_files = []
            for _, row in df.iterrows():
                expected_filename = row.get('local_filename', '')
                if expected_filename and expected_filename not in operator_audio_files:
                    missing_files.append({
                        "voice_key": row.get('voice_key', ''),
                        "title": row.get('title', ''),
                        "expected_filename": expected_filename
                    })
            
            result["missing_audio_files"] = missing_files
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def check_all_operators(self) -> Dict:
        """检查所有干员的资源完整性"""
        print("开始检查干员资源完整性...")
        
        all_operators = self.get_all_operators()
        voice_data_files = self.get_operator_voice_data_files()
        audio_files = self.get_operator_audio_files()
        
        print(f"总干员数量: {len(all_operators)}")
        print(f"语音数据文件数量: {len(voice_data_files)}")
        print(f"有音频文件的干员数量: {len(audio_files)}")
        
        results = {
            "summary": {
                "total_operators": len(all_operators),
                "operators_with_voice_data": len(voice_data_files),
                "operators_with_audio": len(audio_files),
                "operators_with_complete_resources": 0,
                "operators_with_incomplete_resources": 0,
                "operators_without_voice_data": 0,
                "operators_without_audio": 0
            },
            "complete_operators": [],
            "incomplete_operators": [],
            "missing_voice_data": [],
            "missing_audio": [],
            "detailed_results": {}
        }
        
        for operator_name in all_operators:
            voice_data_file = voice_data_files.get(operator_name)
            
            if not voice_data_file:
                results["missing_voice_data"].append(operator_name)
                results["summary"]["operators_without_voice_data"] += 1
                continue
            
            check_result = self.check_operator_voice_data(operator_name, voice_data_file)
            results["detailed_results"][operator_name] = check_result
            
            if check_result.get("error"):
                results["incomplete_operators"].append(operator_name)
                results["summary"]["operators_with_incomplete_resources"] += 1
            elif check_result["total_actual_audio"] == check_result["total_expected_audio"]:
                results["complete_operators"].append(operator_name)
                results["summary"]["operators_with_complete_resources"] += 1
            else:
                results["incomplete_operators"].append(operator_name)
                results["summary"]["operators_with_incomplete_resources"] += 1
            
            if operator_name not in audio_files:
                results["missing_audio"].append(operator_name)
                results["summary"]["operators_without_audio"] += 1
        
        return results
    
    def print_summary(self, results: Dict):
        """打印检查结果摘要"""
        summary = results["summary"]
        
        print("\n" + "="*60)
        print("干员资源完整性检查结果摘要")
        print("="*60)
        print(f"总干员数量: {summary['total_operators']}")
        print(f"有语音数据的干员: {summary['operators_with_voice_data']}")
        print(f"有音频文件的干员: {summary['operators_with_audio']}")
        print(f"资源完整的干员: {summary['operators_with_complete_resources']}")
        print(f"资源不完整的干员: {summary['operators_with_incomplete_resources']}")
        print(f"缺少语音数据的干员: {summary['operators_without_voice_data']}")
        print(f"缺少音频文件的干员: {summary['operators_without_audio']}")
        
        if results["incomplete_operators"]:
            print(f"\n资源不完整的干员 ({len(results['incomplete_operators'])}个):")
            for i, operator in enumerate(results["incomplete_operators"], 1):
                print(f"  {i:3d}. {operator}")
        
        if results["missing_voice_data"]:
            print(f"\n缺少语音数据的干员 ({len(results['missing_voice_data'])}个):")
            for i, operator in enumerate(results["missing_voice_data"], 1):
                print(f"  {i:3d}. {operator}")
        
        if results["missing_audio"]:
            print(f"\n缺少音频文件的干员 ({len(results['missing_audio'])}个):")
            for i, operator in enumerate(results["missing_audio"], 1):
                print(f"  {i:3d}. {operator}")
    
    def print_detailed_missing_files(self, results: Dict):
        """打印详细缺失文件信息"""
        print("\n" + "="*60)
        print("详细缺失文件信息")
        print("="*60)
        
        for operator_name in results["incomplete_operators"]:
            if operator_name in results["detailed_results"]:
                detail = results["detailed_results"][operator_name]
                if detail.get("missing_audio_files"):
                    print(f"\n干员: {operator_name}")
                    print(f"语音数据文件: {detail['voice_data_file']}")
                    print(f"期望音频文件数量: {detail['total_expected_audio']}")
                    print(f"实际音频文件数量: {detail['total_actual_audio']}")
                    print(f"缺失音频文件数量: {len(detail['missing_audio_files'])}")
                    print("缺失的音频文件:")
                    for i, missing in enumerate(detail['missing_audio_files'], 1):
                        print(f"  {i:2d}. {missing['title']} ({missing['expected_filename']})")
                    print("-" * 40)
    
    def save_results(self, results: Dict, output_file: str = "resource_check_results.json"):
        """保存检查结果到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n检查结果已保存到: {output_file}")
        except Exception as e:
            print(f"保存结果失败: {e}")
    
    def generate_report(self, results: Dict, report_file: str = "resource_check_report.txt"):
        """生成文本报告"""
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("干员资源完整性检查报告\n")
                f.write("="*50 + "\n\n")
                
                summary = results["summary"]
                f.write(f"总干员数量: {summary['total_operators']}\n")
                f.write(f"有语音数据的干员: {summary['operators_with_voice_data']}\n")
                f.write(f"有音频文件的干员: {summary['operators_with_audio']}\n")
                f.write(f"资源完整的干员: {summary['operators_with_complete_resources']}\n")
                f.write(f"资源不完整的干员: {summary['operators_with_incomplete_resources']}\n")
                f.write(f"缺少语音数据的干员: {summary['operators_without_voice_data']}\n")
                f.write(f"缺少音频文件的干员: {summary['operators_without_audio']}\n\n")
                
                if results["incomplete_operators"]:
                    f.write(f"资源不完整的干员 ({len(results['incomplete_operators'])}个):\n")
                    for operator in results["incomplete_operators"]:
                        f.write(f"  - {operator}\n")
                    f.write("\n")
                
                if results["missing_voice_data"]:
                    f.write(f"缺少语音数据的干员 ({len(results['missing_voice_data'])}个):\n")
                    for operator in results["missing_voice_data"]:
                        f.write(f"  - {operator}\n")
                    f.write("\n")
                
                if results["missing_audio"]:
                    f.write(f"缺少音频文件的干员 ({len(results['missing_audio'])}个):\n")
                    for operator in results["missing_audio"]:
                        f.write(f"  - {operator}\n")
                    f.write("\n")
            
            print(f"报告已生成: {report_file}")
        except Exception as e:
            print(f"生成报告失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="干员资源完整性检查工具")
    parser.add_argument("--voc-data-dir", default="lib/voc_data", help="语音数据目录路径")
    parser.add_argument("--voc-dir", default="lib/voc", help="音频文件目录路径")
    parser.add_argument("--output", default="resource_check_results.json", help="输出结果文件")
    parser.add_argument("--report", default="resource_check_report.txt", help="输出报告文件")
    parser.add_argument("--save", action="store_true", help="保存检查结果")
    parser.add_argument("--detail", action="store_true", help="显示详细缺失文件信息")
    
    args = parser.parse_args()
    
    try:
        checker = OperatorResourceChecker(args.voc_data_dir, args.voc_dir)
        results = checker.check_all_operators()
        checker.print_summary(results)
        
        if args.detail:
            checker.print_detailed_missing_files(results)
        
        if args.save:
            checker.save_results(results, args.output)
            checker.generate_report(results, args.report)
        
    except Exception as e:
        print(f"检查失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 