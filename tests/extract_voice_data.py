import re
import os
import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
import hashlib

def load_operators_csv(csv_file='lib/operators.csv'):
    """加载干员CSV文件"""
    try:
        df = pd.read_csv(csv_file)
        return df
    except FileNotFoundError:
        print(f"警告：找不到 {csv_file} 文件")
        return None

def find_operator_name_by_voice_key(voice_key, operators_df):
    """根据voice_key查找干员中文名"""
    if operators_df is None:
        return voice_key.replace('char_', '').replace('_', '') if voice_key.startswith('char_') else voice_key
    
    # 从voice_key中提取干员标识符
    # 例如：char_009_12fce -> 12F
    if voice_key.startswith('char_'):
        # 移除char_前缀
        operator_id = voice_key.replace('char_', '')
        
        # 对于12F这种情况，需要特殊处理
        # char_009_12fce -> 12F
        if '12fce' in operator_id.lower():
            match = operators_df[operators_df['chinese_name'] == '12F']
            if not match.empty:
                return match.iloc[0]['chinese_name']
        
        # 尝试不同的匹配方式
        possible_names = [
            operator_id,  # 直接匹配
            operator_id.replace('_', ''),  # 移除下划线
            operator_id.upper(),  # 大写
            operator_id.replace('_', '').upper()  # 移除下划线并大写
        ]
        
        for name in possible_names:
            match = operators_df[operators_df['chinese_name'] == name]
            if not match.empty:
                return match.iloc[0]['chinese_name']
    
    # 如果没找到，返回原始voice_key处理后的名称
    return voice_key.replace('char_', '').replace('_', '') if voice_key.startswith('char_') else voice_key

def extract_voice_data_from_html(html_file, operators_df=None):
    """从HTML文件中提取语音数据"""
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 {html_file}")
        return []
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # 查找voice-data-root元素
    voice_root = soup.find('div', id='voice-data-root')
    if not voice_root:
        print("未找到voice-data-root元素")
        return []
    
    # 获取干员信息
    voice_key = voice_root.get('data-voice-key', '')
    voice_base = voice_root.get('data-voice-base', '')
    
    # 从HTML文件名中提取干员中文名
    # 例如：12F_page.html -> 12F
    html_filename = os.path.basename(html_file)
    operator_name = html_filename.replace('_page.html', '')
    
    voice_data = []
    
    # 查找所有voice-data-item元素
    voice_items = voice_root.find_all('div', class_='voice-data-item')
    
    for item in voice_items:
        title = item.get('data-title', '')
        voice_index = item.get('data-voice-index', '')
        voice_filename = item.get('data-voice-filename', '')
        cond = item.get('data-cond', '')
        
        # 只查找中文简体语音文本
        chinese_detail = item.find('div', {'data-kind-name': '中文'})
        chinese_text = chinese_detail.get_text(strip=True) if chinese_detail else ''
        
        # 构建语音文件URL - 使用正确的路径和文件名格式
        # 将CN_001.wav转换为cn_001.wav，路径使用voice而不是voice_cn
        corrected_filename = voice_filename.lower()
        voice_url = f"https://torappu.prts.wiki/assets/audio/voice/{voice_key}/{corrected_filename}?filename={quote(title)}.wav"
        
        # 构建本地文件名（使用中文文本作为data_detail）
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)  # 移除文件名中的非法字符
        safe_text = re.sub(r'[<>:"/\\|?*]', '_', chinese_text[:50])  # 限制文本长度并移除非法字符
        local_filename = f"{operator_name}_{safe_title}_{safe_text}.wav"
        
        voice_data.append({
            'operator_name': operator_name,
            'voice_key': voice_key,
            'title': title,
            'voice_index': voice_index,
            'voice_filename': voice_filename,
            'condition': cond,
            'chinese_text': chinese_text,
            'voice_url': voice_url,
            'local_filename': local_filename
        })
    
    return voice_data

def download_voice_file(url, local_filename):
    """下载语音文件"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"正在下载: {local_filename}")
        
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # 创建voc目录
        os.makedirs("voc", exist_ok=True)
        
        # 保存文件
        filepath = os.path.join("voc", local_filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 已下载: {filepath}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败 {local_filename}: {e}")
        return False

def save_voice_data_to_csv(voice_data, output_file):
    """保存语音数据到CSV文件"""
    
    if not voice_data:
        print("没有找到任何语音数据")
        return None
    
    df = pd.DataFrame(voice_data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"已保存 {len(voice_data)} 条语音数据到 {output_file}")
    
    return df

def print_voice_data_summary(voice_data):
    """打印语音数据摘要"""
    
    if not voice_data:
        print("没有找到任何语音数据")
        return
    
    print(f"总共提取到 {len(voice_data)} 条语音记录")
    print(f"干员名: {voice_data[0]['operator_name']}")
    print(f"Voice Key: {voice_data[0]['voice_key']}")
    
    print("\n语音记录列表:")
    print("-" * 80)
    
    for i, item in enumerate(voice_data, 1):
        print(f"{i:2d}. {item['title']} (索引: {item['voice_index']})")
        print(f"    中文: {item['chinese_text'][:50]}{'...' if len(item['chinese_text']) > 50 else ''}")
        print(f"    文件名: {item['local_filename']}")
        print(f"    URL: {item['voice_url']}")
        if item['condition']:
            print(f"    条件: {item['condition']}")
        print()

def main():
    """主函数"""
    
    # 测试文件
    html_file = "html/12F_page.html"
    
    print("开始从HTML文件中提取语音数据...")
    print("=" * 60)
    
    # 加载干员CSV文件
    operators_df = load_operators_csv()
    if operators_df is not None:
        print(f"已加载 {len(operators_df)} 个干员信息")
    
    # 提取语音数据
    voice_data = extract_voice_data_from_html(html_file, operators_df)
    
    if not voice_data:
        print("提取失败，没有找到任何语音数据")
        return
    
    # 打印摘要
    print_voice_data_summary(voice_data)
    
    # 保存到CSV
    csv_file = f"voice_data_{voice_data[0]['operator_name']}.csv"
    df = save_voice_data_to_csv(voice_data, csv_file)
    
    # 下载前3个语音文件作为测试
    print("\n开始下载前3个语音文件作为测试...")
    print("-" * 40)
    
    import time
    success_count = 0
    for i, item in enumerate(voice_data[:3], 1):
        print(f"\n下载第 {i} 个文件:")
        if download_voice_file(item['voice_url'], item['local_filename']):
            success_count += 1
        time.sleep(1)  # 避免请求过于频繁
    
    print(f"\n下载完成: {success_count}/{min(3, len(voice_data))} 个文件成功")
    
    print("\n提取完成！")

if __name__ == "__main__":
    main() 