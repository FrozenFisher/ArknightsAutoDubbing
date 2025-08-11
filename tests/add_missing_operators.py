import pandas as pd
import re

def get_missing_operators():
    """获取只在HTML中的干员信息"""
    
    # 读取解析后的HTML数据
    try:
        html_df = pd.read_csv('parsed_operators.csv')
    except FileNotFoundError:
        print("错误：找不到 parsed_operators.csv 文件")
        return []
    
    # 读取现有的operators.csv
    try:
        csv_df = pd.read_csv('lib/operators.csv')
    except FileNotFoundError:
        print("错误：找不到 lib/operators.csv 文件")
        return []
    
    # 找出只在HTML中的干员
    html_names = set(html_df['display_name'].tolist())
    csv_names = set(csv_df['chinese_name'].tolist())
    
    missing_names = html_names - csv_names
    
    # 获取这些干员的详细信息
    missing_operators = []
    for name in missing_names:
        row = html_df[html_df['display_name'] == name].iloc[0]
        missing_operators.append({
            'chinese_name': name,
            'english_name': name,  # 暂时使用中文名作为英文名
            'url': row['full_url']
        })
    
    return missing_operators

def add_operators_to_csv(new_operators, output_file='lib/operators_updated.csv'):
    """将新干员添加到CSV文件中"""
    
    # 读取现有的operators.csv
    try:
        existing_df = pd.read_csv('lib/operators.csv')
    except FileNotFoundError:
        print("错误：找不到 lib/operators.csv 文件")
        return False
    
    # 创建新干员的DataFrame
    new_df = pd.DataFrame(new_operators)
    
    # 合并数据
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # 按中文名排序
    combined_df = combined_df.sort_values('chinese_name').reset_index(drop=True)
    
    # 保存到新文件
    combined_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"已添加 {len(new_operators)} 个新干员到 {output_file}")
    print(f"总干员数：{len(combined_df)}")
    
    return True

def backup_original_csv():
    """备份原始CSV文件"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"lib/operators_backup_{timestamp}.csv"
    
    try:
        shutil.copy2('lib/operators.csv', backup_file)
        print(f"已备份原始文件到：{backup_file}")
        return True
    except Exception as e:
        print(f"备份失败：{e}")
        return False

def main():
    """主函数"""
    
    print("开始添加缺失的干员到CSV文件...")
    print("=" * 50)
    
    # 获取缺失的干员
    missing_operators = get_missing_operators()
    
    if not missing_operators:
        print("没有找到缺失的干员")
        return
    
    print(f"找到 {len(missing_operators)} 个缺失的干员：")
    print("-" * 30)
    
    for i, op in enumerate(missing_operators, 1):
        print(f"{i}. {op['chinese_name']}")
    
    print()
    
    # 备份原始文件
    if not backup_original_csv():
        print("警告：无法备份原始文件，但继续执行...")
    
    # 添加到CSV文件
    if add_operators_to_csv(missing_operators):
        print("\n✅ 成功添加所有缺失的干员！")
        
        # 显示更新后的统计
        try:
            updated_df = pd.read_csv('lib/operators_updated.csv')
            print(f"\n更新后的统计：")
            print(f"- 总干员数：{len(updated_df)}")
            print(f"- 新增干员数：{len(missing_operators)}")
            
            # 检查是否要替换原文件
            print(f"\n是否要替换原始的 lib/operators.csv 文件？")
            print("新文件已保存为：lib/operators_updated.csv")
            
        except Exception as e:
            print(f"读取更新后的文件时出错：{e}")
    else:
        print("❌ 添加干员失败")

if __name__ == "__main__":
    main() 