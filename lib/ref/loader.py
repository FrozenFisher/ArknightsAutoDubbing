import os
import json
import pandas as pd
from typing import Optional, Dict, Any, List

ROOT = os.path.dirname(__file__)
PARQUET_PATH = os.path.join(ROOT, 'table.parquet')
VOICES_JSON_PATH = os.path.join(ROOT, 'voices.json')
VOICES_DIR = os.path.join(ROOT, 'voices')
OPERATORS_CSV_PATH = os.path.join(ROOT, '..', 'operators.csv')

_df_cache: Optional[pd.DataFrame] = None
_voices_index: Optional[Dict[str, Any]] = None
_operators_cache: Optional[pd.DataFrame] = None


def load_table() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        _df_cache = pd.read_parquet(PARQUET_PATH)
    return _df_cache


def load_voices_index() -> Dict[str, Any]:
    global _voices_index
    if _voices_index is None:
        with open(VOICES_JSON_PATH, 'r', encoding='utf-8') as f:
            _voices_index = json.load(f)
    return _voices_index


def load_operators() -> pd.DataFrame:
    """加载干员中英文对照表"""
    global _operators_cache
    if _operators_cache is None:
        if os.path.exists(OPERATORS_CSV_PATH):
            _operators_cache = pd.read_csv(OPERATORS_CSV_PATH, encoding='utf-8-sig')
        else:
            # 如果CSV文件不存在，返回空的DataFrame
            _operators_cache = pd.DataFrame(columns=['chinese_name', 'english_name', 'url'])
    return _operators_cache


def find_operator_by_name(name: str) -> Optional[Dict[str, str]]:
    """通过干员名称查找对应的中英文信息"""
    operators_df = load_operators()
    if operators_df.empty:
        return None
    
    name_lower = name.strip().lower()
    
    # 查找中文名匹配
    chinese_match = operators_df[operators_df['chinese_name'].str.lower() == name_lower]
    if not chinese_match.empty:
        row = chinese_match.iloc[0]
        return {
            'chinese_name': row['chinese_name'],
            'english_name': row['english_name'],
            'url': row['url']
        }
    
    # 查找英文名匹配
    english_match = operators_df[operators_df['english_name'].str.lower() == name_lower]
    if not english_match.empty:
        row = english_match.iloc[0]
        return {
            'chinese_name': row['chinese_name'],
            'english_name': row['english_name'],
            'url': row['url']
        }
    
    # 模糊匹配
    chinese_contains = operators_df[operators_df['chinese_name'].str.lower().str.contains(name_lower, na=False)]
    english_contains = operators_df[operators_df['english_name'].str.lower().str.contains(name_lower, na=False)]
    
    if not chinese_contains.empty:
        row = chinese_contains.iloc[0]
        return {
            'chinese_name': row['chinese_name'],
            'english_name': row['english_name'],
            'url': row['url']
        }
    
    if not english_contains.empty:
        row = english_contains.iloc[0]
        return {
            'chinese_name': row['chinese_name'],
            'english_name': row['english_name'],
            'url': row['url']
        }
    
    return None


def find_rows_by_char(char_keyword: str) -> pd.DataFrame:
    """支持通过干员中文或英文名的子串查找。
    匹配逻辑：
    1. 用中文名在CSV中找到对应的英文名
    2. 将CSV中的英文名与parquet文件中char_xxx_后面的内容进行匹配
    3. 如果CSV中的英文名包含char_xxx_后面的内容，则输出对应的音频路径
    """
    df = load_table()
    kw = str(char_keyword).strip().lower()
    if not kw:
        return df.iloc[0:0]
    
    def _s(x):
        return str(x).lower() if pd.notna(x) else ''
    # 首先尝试通过CSV查找干员信息
    operator_info = find_operator_by_name(char_keyword)
    if operator_info:
        english_name = operator_info['english_name']
        if english_name:
            # 将英文名转换为小写并移除空格，用于匹配
            english_name_clean = english_name.lower().replace(' ', '').replace('-', '').replace('_', '')
            
            # 获取所有唯一的char_id
            unique_char_ids = df['char_id'].unique()
            # 查找匹配的char_id
            matching_char_ids = []
            for char_id in unique_char_ids:
                # 提取char_xxx_后面的部分
                if '_' in char_id:
                    char_suffix = char_id.split('_', 2)[-1]  # 取最后一部分
                    char_suffix_clean = char_suffix.lower()
                    
                    # 更智能的匹配逻辑
                    matched = False
                    
                    # 1. 完全匹配
                    if english_name_clean == char_suffix_clean:
                        matched = True
                    
                    # # 2. 包含匹配
                    # elif english_name_clean in char_suffix_clean or char_suffix_clean in english_name_clean:
                    #     matched = True
                    
                    # # 3. 单词匹配（处理复合词）
                    # else:
                    #     english_words = english_name_clean.split()
                    #     for word in english_words:
                    #         if len(word) > 2 and word in char_suffix_clean:
                    #             matched = True
                    #             break
                    
                    # 4. 特殊映射（处理一些特殊情况）
                    special_mappings = {
                        'silverash': 'svrash',  # 银灰
                        'exusiai': 'angel', # 能天使
                        'bagpipe': 'bpipe',   #风笛
                    }
                    for eng, char_suffix_map in special_mappings.items():
                        if eng in english_name_clean and char_suffix_map in char_suffix_clean:
                            matched = True
                            break
                    
                    if matched:
                        matching_char_ids.append(char_id)
                        
            
            # 如果找到匹配的char_id，返回对应的行
            if matching_char_ids:
                mask = df['char_id'].isin(matching_char_ids)
                return df[mask]
    
    # 原有的查找逻辑作为后备
    mask = (
        df['char_id'] == "failed",
        df['voice_text'] == "failed"
    )
    return None


def _extract_filename(url_or_fname: Optional[str]) -> Optional[str]:
    if not isinstance(url_or_fname, str) or not url_or_fname:
        return None
    # 如果是URL，取最后一段；否则直接返回
    base = os.path.basename(url_or_fname)
    return base if base else None


def _local_path_if_available(filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    # 先根据voices.json判断是否为合法文件名
    try:
        voices = load_voices_index()
        files_dict = voices.get('files', {}) if isinstance(voices, dict) else {}
        if filename not in files_dict:
            # voices.json中没有该文件记录，直接按存在性检查
            pass
    except Exception:
        # 读取失败则降级为存在性检查
        pass

    candidate = os.path.join(VOICES_DIR, filename)
    return os.path.abspath(candidate) if os.path.exists(candidate) else None


def pick_audio_filepaths(rows: pd.DataFrame, limit: int = 1, fallback_url: bool = False) -> List[str]:
    """从行中抽取本地音频文件的绝对路径。
    优先从 filename 字段获取；若缺失则从 file_url 的basename推断。
    - fallback_url=True 时，当本地不存在时保留原URL返回。
    """
    # 处理空DataFrame的情况
    if rows is None or rows.empty:
        return []
    
    results: List[str] = []
    for _, r in rows.head(limit).iterrows():
        fname = r.get('filename') if isinstance(r, pd.Series) else None
        url = r.get('file_url') if isinstance(r, pd.Series) else None

        filename = _extract_filename(fname) or _extract_filename(url)
        local_path = _local_path_if_available(filename)
        if local_path:
            results.append(local_path)
        elif fallback_url and isinstance(url, str) and url:
            results.append(url)
    return results


def find_audio_by_char_name(char_name: str, limit: int = 1, fallback_url: bool = False) -> List[str]:
    """按干员名查找音频，返回本地 voc 目录下的绝对路径列表。
    直接搜索新下载的音频文件，不再使用旧的搜索方式。
    """
    # 使用新的搜索逻辑
    results = find_audio_with_text_by_char_name(char_name, limit=limit, fallback_url=fallback_url)
    
    # 只返回文件路径
    return [result['file_path'] for result in results]


def find_audio_with_text_by_char_name(char_name: str, limit: int = 1, fallback_url: bool = False) -> List[Dict[str, str]]:
    """按干员名查找音频和对应的语音文本，返回包含文件路径和文本的字典列表。
    直接搜索新下载的音频文件（voc目录），不再回退到旧的搜索方式。
    
    Returns:
        List[Dict[str, str]]: 包含 'file_path' 和 'voice_text' 的字典列表
    """
    # 直接搜索新下载的音频文件
    results = find_new_audio_by_char_name(char_name, limit)
    
    if not results:
        print(f"警告：未找到干员 '{char_name}' 对应的新音频文件")
    
    return results


def find_new_audio_by_char_name(char_name: str, limit: int = 1) -> List[Dict[str, str]]:
    """根据干员中文名搜索新下载的音频文件（lib/voc目录）
    
    Args:
        char_name: 干员中文名
        limit: 返回结果数量限制
    
    Returns:
        List[Dict[str, str]]: 包含 'file_path' 和 'voice_text' 的字典列表
    """
    import os
    import glob
    
    # 检查lib/voc目录是否存在
    voc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'voc')
    if not os.path.exists(voc_dir):
        return []
    
    # 搜索以干员名开头的音频文件
    pattern = os.path.join(voc_dir, f"{char_name}_*.wav")
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        return []
    
    # 按文件名排序，确保结果一致
    matching_files.sort()
    
    results = []
    for file_path in matching_files[:limit]:
        # 从文件名中提取信息
        filename = os.path.basename(file_path)
        
        # 文件名格式：干员名_标题_MD5.wav
        # 例如：阿_干员报到_5274c881a4cf6ffc12a12222b6ddbecf.wav
        # 或者：12F_干员报到_e71cd60e6c57a241e7702a0e1864fa47.wav
        parts = filename.replace('.wav', '').split('_')
        if len(parts) >= 3:
            # MD5哈希值总是32位十六进制字符
            md5_hash = parts[-1]  # 最后一部分是MD5
            operator_name = parts[0]  # 第一部分是干员名
            title = '_'.join(parts[1:-1])  # 中间部分是标题（可能包含下划线）
            
            # 尝试从对应的CSV文件中获取中文文本
            chinese_text = get_chinese_text_from_csv(operator_name, md5_hash)
            
            results.append({
                'file_path': os.path.abspath(file_path),
                'voice_text': chinese_text or f"{operator_name}_{title}"
            })
        else:
            # 如果文件名格式不符合预期，使用文件名作为文本
            results.append({
                'file_path': os.path.abspath(file_path),
                'voice_text': filename.replace('.wav', '')
            })
    
    return results


def get_chinese_text_from_csv(operator_name: str, md5_hash: str) -> str:
    """从CSV文件中根据干员名和MD5哈希值获取文本（支持多语言）
    
    Args:
        operator_name: 干员名
        md5_hash: 文本的MD5哈希值
    
    Returns:
        str: 文本内容，如果没找到则返回空字符串
    """
    import os
    
    # 构建CSV文件路径 - 现在在 lib/voc_data 目录下
    csv_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'voc_data', 
        f'voice_data_{operator_name}.csv'
    )
    
    if not os.path.exists(csv_file):
        return ""
    
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file)
        
        # 查找匹配的行 - 同时支持新旧字段名
        # 优先使用新的 selected_text_md5，如果没有则回退到 chinese_text_md5
        matching_rows = None
        
        # 首先尝试新的字段名
        if 'selected_text_md5' in df.columns:
            matching_rows = df[df['selected_text_md5'] == md5_hash]
        
        # 如果没找到，尝试旧的字段名
        if (matching_rows is None or matching_rows.empty) and 'chinese_text_md5' in df.columns:
            matching_rows = df[df['chinese_text_md5'] == md5_hash]
        
        if matching_rows is not None and not matching_rows.empty:
            # 返回文本内容（可能是中文、英语、日语等）
            return matching_rows.iloc[0]['chinese_text']
        
        return ""
        
    except Exception as e:
        print(f"读取CSV文件出错: {e}")
        return "" 