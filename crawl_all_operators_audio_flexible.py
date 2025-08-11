import re
import os
import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import quote, unquote
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
# 新增：导入资源检查器
from check_operator_resources import OperatorResourceChecker

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

# 新增：报告解析与语言映射工具
LANG_MAP_DISPLAY_TO_KIND = {
    '中文': '中文',
    '日语': '日文',
    '日文': '日文',
    '英语': '英文',
    '英文': '英文',
}


def parse_missing_audio_language_report(report_file: str = 'resource_check_report.txt') -> Dict[str, str]:
    """解析报告中"缺少音频文件的干员"段落，返回 {干员: 语言}，未标注语言或标注"无"的不返回。
    语言值为中文显示名（中文/日语/英语）。"""
    if not os.path.exists(report_file):
        return {}
    mappings: Dict[str, str] = {}
    in_section = False
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not in_section:
                    if line.startswith('缺少音频文件的干员'):
                        in_section = True
                    continue
                # 已进入段落，遇到文件结尾则跳出
                if not line:
                    continue  # 跳过空行，继续处理
                if line.startswith('干员资源完整性检查报告'):
                    break
                if line.startswith('-'):
                    # 兼容格式: "- 名称-语言" 或 "- 名称"
                    item = line.lstrip('-').strip()
                    if not item:
                        continue
                    if '-' in item:
                        parts = item.split('-')
                        lang = parts[-1].strip()
                        name = '-'.join(parts[:-1]).strip()
                        if lang and lang != '无':
                            mappings[name] = lang
                    # 若没有语言标注，跳过，等待标注
        return mappings
    except Exception:
        return mappings


def map_display_lang_to_kind_name(display_lang: str) -> Tuple[str, str]:
    """将显示语言映射为 (数据块语言标签, 下载路径基准)。
    返回 (kind_name, base_path)，其中 base_path 为 voice_cn 或 voice。"""
    kind = LANG_MAP_DISPLAY_TO_KIND.get(display_lang, '中文')
    base_path = 'voice_cn' if kind == '中文' else 'voice'
    return kind, base_path

def crawl_operator_page(url, operator_name):
    """爬取干员语音记录页面的HTML内容"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"正在爬取 {operator_name} 的语音记录页面...")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 保存完整的HTML内容
        html_filename = f"html/{operator_name}_page.html"
        os.makedirs("html", exist_ok=True)
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✅ 已保存完整HTML到: {html_filename}")
        print(f"HTML大小: {len(response.text)} 字符")
        
        return response.text
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 爬取失败: {e}")
        return None

# 修改：支持按语言提取文本与下载路径

def extract_voice_data_from_html(html_content, operator_name, preferred_language: str = '中文'):
    """从HTML内容中按语言提取语音数据，并构建对应语言的下载地址"""
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找voice-data-root元素
    voice_root = soup.find('div', id='voice-data-root')
    if not voice_root:
        print(f"未找到 {operator_name} 的voice-data-root元素")
        return []
    
    # 获取干员信息
    voice_key = voice_root.get('data-voice-key', '')
    voice_base = voice_root.get('data-voice-base', '')
    
    voice_data = []
    
    # 语言映射
    kind_name, base_path = map_display_lang_to_kind_name(preferred_language)
    
    # 查找所有voice-data-item元素
    voice_items = voice_root.find_all('div', class_='voice-data-item')
    
    for item in voice_items:
        title = item.get('data-title', '')
        voice_index = item.get('data-voice-index', '')
        voice_filename = item.get('data-voice-filename', '')
        cond = item.get('data-cond', '')
        
        # 选取目标语言文本，若没有则回退中文，再回退为空
        detail = item.find('div', {'data-kind-name': kind_name})
        text_value = detail.get_text(strip=True) if detail else ''
        if not text_value and kind_name != '中文':
            cn_detail = item.find('div', {'data-kind-name': '中文'})
            text_value = cn_detail.get_text(strip=True) if cn_detail else ''
        
        # 构建语音文件URL - 根据语言选择 voice_cn 或 voice，文件名统一小写
        corrected_filename = voice_filename.lower()
        voice_url = f"https://torappu.prts.wiki/assets/audio/{base_path}/{voice_key}/{corrected_filename}?filename={quote(title)}.wav"
        
        # 构建本地文件名（使用文本的MD5哈希值）
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        selected_text_md5 = hashlib.md5(text_value.encode('utf-8')).hexdigest()
        base_filename = f"{operator_name}_{safe_title}_{selected_text_md5}"
        local_filename = f"{base_filename}.wav"
        
        voice_data.append({
            'operator_name': operator_name,
            'voice_key': voice_key,
            'title': title,
            'voice_index': voice_index,
            'voice_filename': voice_filename,
            'condition': cond,
            'chinese_text': text_value,  # 按需求将字段“中文文本”复用为所选语言文本
            'selected_language': preferred_language,
            'selected_text_md5': selected_text_md5,
            'voice_url': voice_url,
            'local_filename': local_filename
        })
    
    return voice_data

def download_voice_file(url, local_filename, voice_key=None, title=None):
    """下载语音文件，如果中文失败则尝试日文"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"正在下载: {local_filename}")
        
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # 创建lib/voc目录
        os.makedirs("lib/voc", exist_ok=True)
        
        # 保存文件
        filepath = os.path.join("lib/voc", local_filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 已下载: {filepath}")
        return True, "chinese"
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 中文语音下载失败: {e}")
        
        # 如果中文失败且提供了voice_key和title，尝试日文语音
        if voice_key and title:
            try:
                # 构建日文语音URL
                corrected_filename = local_filename.split('_', 1)[1] if '_' in local_filename else local_filename
                if corrected_filename.endswith('.wav'):
                    corrected_filename = corrected_filename[:-4]  # 移除.wav后缀
                
                # 从文件名中提取原始文件名
                original_filename = None
                for part in corrected_filename.split('_'):
                    if part.upper().startswith('CN_'):
                        original_filename = part.lower()
                        break
                
                if original_filename:
                    japanese_url = f"https://torappu.prts.wiki/assets/audio/voice/{voice_key}/{original_filename}?filename={quote(title)}.wav"
                    print(f"尝试下载其他语种语音: {japanese_url}")
                    
                    response = requests.get(japanese_url, headers=headers, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    # 修改文件名，添加其他语种标识
                    japanese_filename = local_filename.replace('.wav', '_其他语种.wav')
                    filepath = os.path.join("lib/voc", japanese_filename)
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"✅ 已下载其他语种语音: {filepath}")
                    return True, "japanese"
                    
            except requests.exceptions.RequestException as e2:
                print(f"❌ 其他语种语音也下载失败: {e2}")
        
        return False, "failed"

def save_voice_data_to_csv(voice_data, output_file):
    """保存语音数据到CSV文件"""
    
    if not voice_data:
        print("没有找到任何语音数据")
        return None
    
    # 创建lib/voc_data目录
    os.makedirs("lib/voc_data", exist_ok=True)
    
    # 如果output_file不包含路径，则添加到lib/voc_data目录
    if not os.path.dirname(output_file):
        output_file = os.path.join("lib/voc_data", output_file)
    
    df = pd.DataFrame(voice_data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"已保存 {len(voice_data)} 条语音数据到 {output_file}")
    
    return df

# 修改：加入 preferred_language 支持

def process_operator(operator, download_audio=True, max_audio_files=None, preferred_language: str = '中文'):
    """处理单个干员的语音数据（支持按语言）"""
    
    operator_name = operator['display_name']
    url = operator['full_url']
    
    print(f"\n{'='*60}")
    print(f"开始处理干员: {operator_name} [{preferred_language}]")
    print(f"{'='*60}")
    
    # 爬取HTML页面
    html_content = crawl_operator_page(url, operator_name)
    
    if html_content is None:
        print(f"❌ {operator_name} HTML爬取失败，跳过")
        return None
    
    # 提取语音数据（按语言）
    voice_data = extract_voice_data_from_html(html_content, operator_name, preferred_language=preferred_language)
    
    if not voice_data:
        print(f"❌ {operator_name} 没有找到语音数据，跳过")
        return None
    
    print(f"✅ {operator_name} 找到 {len(voice_data)} 条语音记录")
    
    # 保存语音数据到CSV
    csv_file = f"voice_data_{operator_name}.csv"
    save_voice_data_to_csv(voice_data, csv_file)
    
    # 下载音频文件
    if download_audio:
        print(f"\n开始下载 {operator_name} 的音频文件...")
        success_count = 0
        chinese_count = 0
        japanese_count = 0
        failed_count = 0
        
        if max_audio_files is None:
            # 下载所有音频文件
            download_count = len(voice_data)
            voice_items = voice_data
        else:
            # 下载指定数量的音频文件
            download_count = min(max_audio_files, len(voice_data))
            voice_items = voice_data[:download_count]
        
        for i, item in enumerate(voice_items, 1):
            print(f"\n下载第 {i}/{download_count} 个文件:")
            success, voice_type = download_voice_file(
                item['voice_url'], 
                item['local_filename'],
                voice_key=item['voice_key'],
                title=item['title']
            )
            if success:
                success_count += 1
                if voice_type == "chinese":
                    chinese_count += 1
                elif voice_type == "japanese":
                    japanese_count += 1
            else:
                failed_count += 1
            time.sleep(1)  # 避免请求过于频繁
        
        print(f"\n{operator_name} 下载完成: {success_count}/{download_count} 个文件成功")
        print(f"  中文语音: {chinese_count} 个")
        print(f"  其他语种语音: {japanese_count} 个")
        print(f"  下载失败: {failed_count} 个")
        
        # 返回结果信息
        result_info = {
            'operator_name': operator_name,
            'total_voice_data': len(voice_data),
            'download_count': download_count,
            'success_count': success_count,
            'chinese_count': chinese_count,
            'japanese_count': japanese_count,
            'failed_count': failed_count,
            'has_japanese': japanese_count > 0,
            'selected_language': preferred_language,
        }
        
        return voice_data, result_info
    
    return voice_data, None

def main():
    """主函数"""
    
    print("开始爬取所有干员的音频数据...")
    print("=" * 80)
    
    # 第0步：下载前进行资源完整性检查
    print("0. 资源完整性预检查...")
    try:
        checker = OperatorResourceChecker("lib/voc_data", "lib/voc")
        results = checker.check_all_operators()
        # 保存检查结果
        checker.save_results(results, "resource_check_results.json")
        
        # 报告文件策略：如果用户版报告已存在则不覆盖；总是输出一份自动报告
        user_report_path = "resource_check_report.txt"
        auto_report_path = "resource_check_report_auto.txt"
        try:
            checker.generate_report(results, auto_report_path)
            print(f"自动报告已生成: {auto_report_path}")
        except Exception as e_auto:
            print(f"自动报告生成失败: {e_auto}")
        if not os.path.exists(user_report_path):
            try:
                checker.generate_report(results, user_report_path)
                print(f"用户可标注的报告已生成: {user_report_path}")
            except Exception as e_user:
                print(f"用户报告生成失败: {e_user}")
        else:
            print(f"检测到已存在的用户报告 {user_report_path}，不会覆盖。")
        
        incomplete_set = set(results.get('incomplete_operators', []))
        missing_audio_set = set(results.get('missing_audio', []))
        # 需要继续用中文下载的：不完整但已存在部分音频
        need_cn_download = incomplete_set - missing_audio_set
        # 从用户报告读取对缺少音频的语言标注
        lang_map = parse_missing_audio_language_report(user_report_path)
        # 需要按标注语言下载的：缺少音频且已标注语言为英语/日语
        need_special_download = {
            name: lang for name, lang in lang_map.items()
            if name in missing_audio_set and LANG_MAP_DISPLAY_TO_KIND.get(lang) in ('日文', '英文')
        }
        # 缺少音频但未标注或标注为"无"的，暂不下载
        pending_names = [name for name in missing_audio_set if name not in need_special_download]
        if pending_names:
            print(f"⚠️ 以下干员缺少音频且未标注或标注为'无'，此次跳过: {', '.join(pending_names)}")
    except Exception as e:
        print(f"资源预检查失败（可能是首次执行或目录为空），将继续全部流程：{e}")
        results = None
        need_cn_download = set()
        need_special_download = {}
    
    # 解析in.html文件中的所有干员链接
    print("1. 解析in.html文件中的干员链接...")
    operators = parse_html_links('in.html')
    
    if not operators:
        print("❌ 没有找到任何干员链接")
        return
    
    print(f"✅ 找到 {len(operators)} 个干员")
    
    # 显示前几个干员
    print("\n前10个干员:")
    for i, op in enumerate(operators[:10], 1):
        print(f"{i:2d}. {op['display_name']}")
    
    if len(operators) > 10:
        print(f"... 还有 {len(operators) - 10} 个干员")
    
    # 根据预检查结果过滤待处理干员
    allowed_names = set(op['display_name'] for op in operators)
    selected_name_to_lang: Dict[str, str] = {}
    if results is not None:
        # 1) 继续下载 voice_cn 的不完整干员
        for name in need_cn_download:
            if name in allowed_names:
                selected_name_to_lang[name] = '中文'
        # 2) 对缺少音频但已标注语言的干员，按该语言处理（路径使用 voice）
        for name, display_lang in need_special_download.items():
            if name in allowed_names:
                selected_name_to_lang[name] = display_lang
        if not selected_name_to_lang:
            print("当前无需要下载的干员（要么资源已完整，要么缺少音频但尚未标注语言）。")
    else:
        # 无检查结果时，默认全部中文
        for op in operators:
            selected_name_to_lang[op['display_name']] = '中文'
    
    # 将 operators 过滤到需要处理的集合
    operators_to_process = [
        {**op, 'preferred_language': selected_name_to_lang[op['display_name']]}
        for op in operators if op['display_name'] in selected_name_to_lang
    ]
    
    if not operators_to_process:
        print("无待处理干员，程序结束。")
        return
    
    print(f"\n本次将处理 {len(operators_to_process)} 名干员：")
    preview = operators_to_process[:10]
    for i, op in enumerate(preview, 1):
        print(f"{i:2d}. {op['display_name']} [{op.get('preferred_language','中文')}]")
    if len(operators_to_process) > 10:
        print(f"... 还有 {len(operators_to_process) - 10} 名")
    
    # 询问每个干员下载多少个音频文件
    print(f"\n请选择每个干员下载的音频文件数量：")
    print("1. 下载所有音频文件")
    print("2. 下载前5个音频文件")
    print("3. 自定义数量")
    
    audio_choice = input("请输入选择 (1/2/3): ").strip()
    
    if audio_choice == "1":
        max_audio_files = None  # 下载所有
        print("将下载每个干员的所有音频文件")
    elif audio_choice == "2":
        max_audio_files = 5
        print("将下载每个干员的前5个音频文件")
    elif audio_choice == "3":
        try:
            max_audio_files = int(input("请输入每个干员要下载的音频文件数量: "))
            print(f"将下载每个干员的前{max_audio_files}个音频文件")
        except ValueError:
            print("输入无效，使用默认值5")
            max_audio_files = 5
    else:
        print("输入无效，使用默认值5")
        max_audio_files = 5
    
    all_voice_data = []
    success_count = 0
    failed_operators = []
    japanese_operators = []  # 使用其他语种语音的干员
    operator_results = []  # 所有干员的处理结果
    
    for i, operator in enumerate(operators_to_process, 1):
        print(f"\n处理进度: {i}/{len(operators_to_process)} ({i/len(operators_to_process)*100:.1f}%)")
        try:
            preferred_language = operator.get('preferred_language', '中文')
            result = process_operator(operator, download_audio=True, max_audio_files=max_audio_files, preferred_language=preferred_language)
            if result:
                voice_data, result_info = result
                if voice_data:
                    all_voice_data.extend(voice_data)
                    success_count += 1
                    
                    # 记录处理结果
                    if result_info:
                        operator_results.append(result_info)
                        # 如果使用了其他语种语音，添加到特殊列表
                        if result_info['has_japanese'] or result_info.get('selected_language') in ('日语','日文','英语','英文'):
                            japanese_operators.append({
                                'name': result_info['operator_name'],
                                'other_voice_count': result_info['japanese_count'],
                                'chinese_count': result_info['chinese_count'],
                                'total_download': result_info['download_count']
                            })
                else:
                    failed_operators.append(operator['display_name'])
            else:
                failed_operators.append(operator['display_name'])
        except Exception as e:
            print(f"❌ 处理 {operator['display_name']} 时出错: {e}")
            failed_operators.append(operator['display_name'])
        
        # 每处理10个干员保存一次进度
        if i % 10 == 0:
            progress_csv_file = f"voice_data_progress_{i}.csv"
            save_voice_data_to_csv(all_voice_data, progress_csv_file)
            print(f"✅ 已保存进度到 lib/voc_data/{progress_csv_file}")
        
        time.sleep(1)  # 干员之间稍作休息
    
    # 保存所有语音数据到总CSV文件
    if all_voice_data:
        total_csv_file = "all_voice_data_complete.csv"
        save_voice_data_to_csv(all_voice_data, total_csv_file)
        print(f"\n✅ 总共处理了 {len(all_voice_data)} 条语音记录")
        print(f"✅ 总数据已保存到 lib/voc_data/{total_csv_file}")
    
    # 保存失败列表
    if failed_operators:
        with open("failed_operators.txt", "w", encoding="utf-8") as f:
            for op in failed_operators:
                f.write(f"{op}\n")
        print(f"❌ 有 {len(failed_operators)} 个干员处理失败，详情见 failed_operators.txt")
    
    # 显示使用其他语种语音的干员总结
    if japanese_operators:
        print(f"\n{'='*60}")
        print("📢 特殊干员总结：使用其他语种语音的干员（可能是联动干员）")
        print(f"{'='*60}")
        print(f"共有 {len(japanese_operators)} 个干员使用了其他语种语音：")
        print()
        
        for i, op in enumerate(japanese_operators, 1):
            print(f"{i:2d}. {op['name']}")
            print(f"    其他语种语音: {op['other_voice_count']} 个")
            print(f"    中文语音: {op['chinese_count']} 个")
            print(f"    总下载: {op['total_download']} 个")
            print()
        
        # 保存其他语种语音干员列表到文件
        with open("other_voice_operators.txt", "w", encoding="utf-8") as f:
            f.write("使用其他语种语音的干员列表（可能是联动干员）：\n")
            f.write("="*60 + "\n")
            for op in japanese_operators:
                f.write(f"{op['name']}: 其他语种{op['other_voice_count']}个, 中文{op['chinese_count']}个\n")
        
        print(f"✅ 其他语种语音干员列表已保存到 other_voice_operators.txt")
    else:
        print(f"\n✅ 所有待处理干员均已完成下载！")
    
    # 显示总体统计
    print(f"\n{'='*60}")
    print("📊 总体统计")
    print(f"{'='*60}")
    print(f"成功处理干员: {success_count}/{len(operators_to_process)}")
    print(f"使用其他语种语音的干员: {len(japanese_operators)} 个")
    print(f"处理失败的干员: {len(failed_operators)} 个")
    
    if operator_results:
        total_chinese = sum(r['chinese_count'] for r in operator_results)
        total_japanese = sum(r['japanese_count'] for r in operator_results)
        total_failed = sum(r['failed_count'] for r in operator_results)
        print(f"总下载文件: {total_chinese + total_japanese + total_failed} 个")
        print(f"  中文语音: {total_chinese} 个")
        print(f"  其他语种语音: {total_japanese} 个")
        print(f"  下载失败: {total_failed} 个")
    
    print("\n所有干员处理完成！")

if __name__ == "__main__":
    main() 