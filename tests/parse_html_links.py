import re
from urllib.parse import unquote
import pandas as pd

def parse_html_links(html_file='in.html'):
    """解析HTML文件中的干员语音记录链接"""
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 {html_file}")
        return []
    
    # 使用正则表达式提取所有链接
    # 匹配 <a href="/w/干员名/语音记录" title="干员名/语音记录">干员名/语音记录</a>
    pattern = r'<a href="/w/([^"]+)/%E8%AF%AD%E9%9F%B3%E8%AE%B0%E5%BD%95" title="([^"]+)/语音记录">([^<]+)/语音记录</a>'
    
    matches = re.findall(pattern, content)
    
    operators = []
    
    for match in matches:
        # match[0] 是URL编码的干员名
        # match[1] 是title中的干员名
        # match[2] 是显示的干员名
        
        url_encoded_name = match[0]
        title_name = match[1]
        display_name = match[2]
        
        # URL解码
        decoded_name = unquote(url_encoded_name)
        
        # 构建完整链接
        full_url = f"https://prts.wiki/w/{url_encoded_name}/语音记录"
        
        operators.append({
            'url_encoded_name': url_encoded_name,
            'decoded_name': decoded_name,
            'title_name': title_name,
            'display_name': display_name,
            'full_url': full_url
        })
    
    return operators

def save_to_csv(operators, output_file='parsed_operators.csv'):
    """保存解析结果到CSV文件"""
    
    if not operators:
        print("没有找到任何干员链接")
        return
    
    df = pd.DataFrame(operators)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"已保存 {len(operators)} 个干员链接到 {output_file}")
    
    return df

def print_summary(operators):
    """打印解析结果摘要"""
    
    if not operators:
        print("没有找到任何干员链接")
        return
    
    print(f"总共解析到 {len(operators)} 个干员语音记录链接")
    print("\n前10个干员示例：")
    print("-" * 60)
    
    for i, op in enumerate(operators[:10], 1):
        print(f"{i:2d}. {op['display_name']}")
        print(f"    URL编码: {op['url_encoded_name']}")
        print(f"    解码后: {op['decoded_name']}")
        print(f"    完整链接: {op['full_url']}")
        print()
    
    if len(operators) > 10:
        print(f"... 还有 {len(operators) - 10} 个干员")
    
    # 按字母分组统计
    print("\n按首字母分组统计：")
    print("-" * 30)
    
    letter_counts = {}
    for op in operators:
        first_letter = op['display_name'][0].upper()
        if first_letter.isalpha():
            letter_counts[first_letter] = letter_counts.get(first_letter, 0) + 1
        else:
            # 处理数字开头的干员（如12F）
            letter_counts['数字'] = letter_counts.get('数字', 0) + 1
    
    for letter in sorted(letter_counts.keys()):
        print(f"{letter}: {letter_counts[letter]} 个")

def compare_with_csv(operators, csv_file='lib/operators.csv'):
    """与现有的operators.csv文件比较"""
    
    try:
        df_csv = pd.read_csv(csv_file)
        csv_names = set(df_csv['chinese_name'].tolist())
    except FileNotFoundError:
        print(f"警告：找不到 {csv_file} 文件，跳过比较")
        return
    
    html_names = set(op['display_name'] for op in operators)
    
    # 找出只在HTML中存在的干员
    only_in_html = html_names - csv_names
    # 找出只在CSV中存在的干员
    only_in_csv = csv_names - html_names
    # 共同存在的干员
    common = html_names & csv_names
    
    print(f"\n与 {csv_file} 的比较结果：")
    print("-" * 40)
    print(f"HTML中的干员数: {len(html_names)}")
    print(f"CSV中的干员数: {len(csv_names)}")
    print(f"共同存在的干员数: {len(common)}")
    print(f"只在HTML中的干员数: {len(only_in_html)}")
    print(f"只在CSV中的干员数: {len(only_in_csv)}")
    
    if only_in_html:
        print(f"\n只在HTML中的干员（前10个）:")
        for name in sorted(list(only_in_html))[:10]:
            print(f"  - {name}")
        if len(only_in_html) > 10:
            print(f"  ... 还有 {len(only_in_html) - 10} 个")
    
    if only_in_csv:
        print(f"\n只在CSV中的干员（前10个）:")
        for name in sorted(list(only_in_csv))[:10]:
            print(f"  - {name}")
        if len(only_in_csv) > 10:
            print(f"  ... 还有 {len(only_in_csv) - 10} 个")

def main():
    """主函数"""
    
    print("开始解析 in.html 文件中的干员语音记录链接...")
    print("=" * 60)
    
    # 解析HTML文件
    operators = parse_html_links()
    
    if not operators:
        print("解析失败，没有找到任何干员链接")
        return
    
    # 打印摘要
    print_summary(operators)
    
    # 保存到CSV
    df = save_to_csv(operators)
    
    # 与现有CSV比较
    compare_with_csv(operators)
    
    print("\n解析完成！")

if __name__ == "__main__":
    main() 