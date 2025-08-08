import os
import json
import pandas as pd
from typing import Optional, Dict, Any, List

ROOT = os.path.dirname(__file__)
PARQUET_PATH = os.path.join(ROOT, 'table.parquet')
VOICES_JSON_PATH = os.path.join(ROOT, 'voices.json')
VOICES_DIR = os.path.join(ROOT, 'voices')

_df_cache: Optional[pd.DataFrame] = None
_voices_index: Optional[Dict[str, Any]] = None


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


def find_rows_by_char(char_keyword: str) -> pd.DataFrame:
    """支持通过干员中文或英文名的子串查找。
    匹配字段：char_id, voice_text 中包含关键词的行。
    """
    df = load_table()
    kw = str(char_keyword).strip().lower()
    if not kw:
        return df.iloc[0:0]
    def _s(x):
        return str(x).lower() if pd.notna(x) else ''
    mask = (
        df['char_id'].map(_s).str.contains(kw) |
        df['voice_text'].map(_s).str.contains(kw)
    )
    return df[mask]


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


def pick_audio_filepaths(rows: pd.DataFrame, limit: int = 5, fallback_url: bool = False) -> List[str]:
    """从行中抽取本地音频文件的绝对路径。
    优先从 filename 字段获取；若缺失则从 file_url 的basename推断。
    - fallback_url=True 时，当本地不存在时保留原URL返回。
    """
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
    """按干员名查找音频，返回本地 voices 目录下的绝对路径列表。
    当 fallback_url=True 且本地缺失时，返回对应URL。
    """
    rows = find_rows_by_char(char_name)
    return pick_audio_filepaths(rows, limit=limit, fallback_url=fallback_url) 