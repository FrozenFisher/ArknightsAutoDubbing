import pandas as pd
from lib.ref.loader import find_audio_with_text_by_char_name

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
    found, not_found = test_all_operators() 