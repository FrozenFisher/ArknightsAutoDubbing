import os
import re
import base64
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


def _load_env_from_dotenv_if_needed() -> None:
    """从项目根目录 .env 加载并映射到程序期望的环境变量名。
    兼容如下映射：
    - SiliconFlowTTS-key -> TTS_SERVICE_API_KEY
    - SiliconFlowTTS-endpoint -> TTS_SERVICE_URL_SiliconFlow（去掉末尾的%等异常字符）
    仅在目标环境变量未设置时才写入 os.environ。
    """
    try:
        # 计算项目根目录：lib/tts_service.py -> lib -> 项目根
        project_root = Path(__file__).resolve().parent.parent
        dotenv_path = project_root / '.env'
        if not dotenv_path.exists():
            return
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                key = k.strip()
                val = v.strip().strip('"').strip("'")
                # 特殊清理：endpoint 可能带有意外的尾部字符
                if key.lower() == 'siliconflowtts-endpoint':
                    val = val.rstrip('%').strip()
                # 映射
                if key == 'SiliconFlowTTS-key' and not os.getenv('TTS_SERVICE_API_KEY'):
                    os.environ['TTS_SERVICE_API_KEY'] = val
                elif key == 'SiliconFlowTTS-endpoint' and not os.getenv('TTS_SERVICE_URL_SiliconFlow'):
                    os.environ['TTS_SERVICE_URL_SiliconFlow'] = val
    except Exception as e:
        logger.debug(f"加载 .env 失败（忽略，不影响主流程）: {e}")


class SiliconFlowTTS:
    """硅基流动 TTS 客户端（最小可用封装）。
    - 通过 customName(使用 md5(key)) 去重上传参考音频
    - 通过 uri 进行 TTS 合成
    - 若无 API Key 或请求失败，方法返回 None
    """

    def __init__(self) -> None:
        # 优先从 .env 映射加载
        _load_env_from_dotenv_if_needed()

        self.base_url: str = os.getenv("TTS_SERVICE_URL_SiliconFlow", "https://api.siliconflow.cn/v1").strip()
        self.api_key: str = os.getenv("TTS_SERVICE_API_KEY", "").strip()
        self.model: str = os.getenv("TTS_MODEL", "FunAudioLLM/CosyVoice2-0.5B").strip()

        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        self.role_name: Dict[str, str] = {}  # hashed_name -> uri

        if self.api_key:
            self._fetch_custom_voices()
        else:
            logger.warning("未检测到 TTS_SERVICE_API_KEY，将无法调用硅基流动 TTS。")

    def _filter_symbols(self, text: str) -> str:
        if not text:
            return text
        text = re.sub(r'[^\w\s\u4e00-\u9fff]{3,}', '', text)
        patterns = [
            r'o\([^)]*\)[^\w\s]*',
            r'\([^)]*\)[^\w\s]*',
            r'[^\w\s]*\([^)]*\)',
            r'[★☆♪♫♬♭♮♯]+',
            r'[（）()【】\[\]{}｛｝]+',
            r'[！!？?。.，,；;：:]+',
            r'[~～＠@#＃$＄%％^＾&＆*＊]+'
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text or text

    def _fetch_custom_voices(self) -> None:
        try:
            url = f"{self.base_url}/audio/voice/list"
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                result = resp.json()
                for voice in result.get("results", []):
                    name = voice.get("customName")
                    uri = voice.get("uri")
                    if name and uri:
                        self.role_name[name] = uri
                logger.info(f"已载入自定义音色：{len(self.role_name)} 条")
            else:
                logger.warning(f"获取音色列表失败: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.warning(f"获取音色列表异常: {e}")

    @staticmethod
    def _hash_key(key: str) -> str:
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def ensure_voice(self, name_key: str, wav_path: str, ref_text: Optional[str] = None) -> Optional[str]:
        """确保以 name_key 对应的音色已存在；若不存在则上传。
        返回 voice uri，失败返回 None。
        """
        if not self.api_key:
            return None
        hashed = self._hash_key(name_key)
        if hashed in self.role_name:
            return self.role_name[hashed]

        try:
            wav_file = Path(wav_path)
            if not wav_file.exists():
                logger.warning(f"参考音频不存在: {wav_file}")
                return None

            # 读取参考文本
            ref_text = (ref_text or "在一无所知中, 梦里的一天结束了，一个新的轮回便会开始").strip()

            with open(wav_file, 'rb') as f:
                audio_data = f.read()
            base64_str = base64.b64encode(audio_data).decode('utf-8')
            audio_base64 = f"data:audio/wav;base64,{base64_str}"

            files = {
                "model": (None, self.model),
                "customName": (None, hashed),
                "text": (None, ref_text),
                "audio": (None, audio_base64),
            }

            resp = requests.post(f"{self.base_url}/uploads/audio/voice", files=files, headers=self.headers, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                uri = result.get("uri")
                if uri:
                    self.role_name[hashed] = uri
                    return uri
                logger.warning(f"上传成功但未返回 URI: {result}")
                return None
            else:
                logger.warning(f"上传音色失败: {resp.status_code}, {resp.text}")
                return None
        except Exception as e:
            logger.warning(f"上传音色异常: {e}")
            return None

    def synthesize(self, text: str, voice_uri: Optional[str] = None, response_format: str = 'wav', sample_rate: int = 44100) -> Optional[bytes]:
        if not self.api_key:
            return None
        clean_text = self._filter_symbols(text) or text
        payload = {
            "model": self.model,
            "voice": voice_uri or f"{self.model}:default",
            "input": clean_text,
            "response_format": response_format,
            "speed": 1.0,
            "gain": 0.0,
        }
        if response_format in ["wav", "pcm"]:
            payload["sample_rate"] = sample_rate
        elif response_format == "mp3":
            payload["sample_rate"] = sample_rate if sample_rate in [32000, 44100] else 44100
        elif response_format == "opus":
            payload["sample_rate"] = 48000

        try:
            resp = requests.post(f"{self.base_url}/audio/speech", json=payload, headers=self.headers, timeout=60)
            if resp.status_code == 200:
                return resp.content
            logger.warning(f"TTS 请求失败: {resp.status_code}, {resp.text}")
            return None
        except Exception as e:
            logger.warning(f"TTS 调用异常: {e}")
            return None 