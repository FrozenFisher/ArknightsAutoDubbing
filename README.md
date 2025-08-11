# 方舟干员语音自动配音系统

一个基于Python的明日方舟干员语音自动配音工具，支持OCR识别游戏文本、TTS语音合成、音频文件管理等功能。

## 特别鸣谢

数据来源: prts.wiki
语音版权与解释权所有: 上海鹰角网络科技有限公司
云端tts: 硅基流动
OCR: PaddlePaddle

## 功能特性

- 🎮 **游戏文本识别**: OCR识别游戏中的角色名和对话文本
- 🎤 **智能TTS配音**: 基于硅基流动API的语音合成
- 🎵 **音频文件管理**: 自动下载和管理干员语音文件
- 🎯 **自定义区域**: 可视化设置多个识别区域
- ⌨️ **快捷键操作**: 支持全局快捷键，无需切换窗口
- 📊 **资源完整性检查**: 自动检查干员音频资源完整性
- 🔄 **多语言支持**: 支持中文、英语、日语干员语音
- 📱 **状态提示**: 实时显示处理状态（等待/识别/上传音色/TTS）
- 🔊 **自动播放**: TTS结果自动播放

## 快捷键说明

- **空格键**: 识别当前设置的区域并生成TTS配音
- **F12**: 打开设置界面
- **Ctrl+Q**: 退出应用

## 安装要求

### 系统要求
- Python 3.11
- macOS/Linux/Windows
- 硅基流动API密钥（用于TTS服务）

### 依赖安装

1. 创建并激活虚拟环境：
```bash
# 创建 Python 3.11 虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
```

2. 安装Python依赖：
```bash
pip3 install -r requirements.txt
```

3. 下载音频数据：
   - 访问 [ModelScope 方舟语音数据集](https://www.modelscope.cn/datasets/FrozenFish114/Arknights_voice_zh)
   - 下载 `voc` 和 `voc_data` 压缩包
   - 解压到项目根目录，确保文件结构如下：
     ```
     lib/
     ├── voc/           # 音频文件目录
     └── voc_data/      # 语音数据CSV文件
     ```

4. 配置TTS服务：
   - 复制环境变量模板文件：
     ```bash
     cp .env_example .env
     ```
   - 编辑 `.env` 文件，填入你的硅基流动API密钥：
     ```bash
     SiliconFlowTTS-key=your_actual_api_key_here
     SiliconFlowTTS-endpoint=https://api.siliconflow.cn/v1
     ```
   - 或设置环境变量 `SILICONFLOW_API_KEY`

## 使用方法

### 1. 启动应用
```bash
python app.py
```

### 2. 设置识别区域
- 按 `F12` 打开设置界面
- 点击"添加区域"按钮
- 在屏幕上拖动鼠标选择要识别的区域
- 建议设置两个区域：角色名区域和对话文本区域

### 3. 使用配音功能
- 在游戏中切换到对话界面
- 按 `空格键` 识别文本并生成TTS配音
- 系统会自动播放生成的语音

### 4. 音频文件管理

#### 下载干员音频
```bash
python crawl_all_operators_audio_flexible.py
```

#### 检查资源完整性
```bash
python check_operator_resources.py
```

## 项目结构

```
ArknightsAutoDubbing/
├── app.py                          # 主应用（OCR+TTS）
├── crawl_all_operators_audio_flexible.py  # 音频下载脚本
├── check_operator_resources.py     # 资源完整性检查
├── in.html                         # 干员列表HTML
├── parsed_operators.csv            # 解析的干员列表
├── regions.json                    # OCR区域配置
├── lib/                            # 核心库文件
│   ├── voc/                        # 音频文件目录（需从ModelScope下载）
│   ├── voc_data/                   # 语音数据CSV文件（需从ModelScope下载）
│   ├── voc_tmp/                    # TTS临时文件
│   ├── ref/                        # 参考音频加载器
│   │   ├── loader.py               # 音频查找和匹配
│   │   └── table.parquet           # 音频索引数据
│   ├── ocr.py                      # OCR识别模块
│   └── tts_service.py              # TTS服务模块
├── tests/                          # 测试和工具脚本
├── requirements.txt                # Python依赖
├── setup.py                        # 安装配置
└── README.md                       # 项目说明
```

**注意**: `lib/voc/` 和 `lib/voc_data/` 目录包含大量音频文件，需要从 [ModelScope 方舟语音数据集](https://www.modelscope.cn/datasets/FrozenFish114/Arknights_voice_zh) 单独下载。

## 核心功能说明

### OCR文本识别
- 基于PaddleOCR的高精度文字识别
- 支持中文、英文、日文识别
- 自定义区域识别，适应不同游戏界面

### TTS语音合成
- 基于硅基流动API的语音合成
- 自动上传干员音色并复用
- 支持多语言干员（中文/英语/日语）
- 异步播放，不阻塞主程序

### 音频文件管理
- 自动下载干员语音文件
- 资源完整性检查和报告
- 支持联动干员多语言语音
- 智能音频文件匹配

### 状态提示系统
- 左上角置顶状态窗口
- 实时显示处理进度：
  - 等待
  - OCR识别
  - 正在上传音色
  - 正在TTS
- 自动播放TTS结果

## 技术栈

- **OCR引擎**: PaddleOCR
- **TTS服务**: 硅基流动API
- **图像处理**: OpenCV
- **GUI框架**: Tkinter
- **键盘监听**: pynput
- **屏幕截图**: pyautogui
- **数据处理**: pandas, pyarrow
- **网络请求**: requests
- **音频播放**: afplay (macOS)

## 配置说明

### TTS API配置
有两种方式配置硅基流动API密钥：

#### 方式一：环境变量配置（推荐）
1. 复制环境变量模板文件：
```bash
cp .env_example .env
```

2. 编辑 `.env` 文件，填入你的API密钥：
```bash
SiliconFlowTTS-key=your_actual_api_key_here
SiliconFlowTTS-endpoint=https://api.siliconflow.cn/v1
```

#### 方式二：代码中配置
在 `lib/tts_service.py` 中直接配置硅基流动API密钥：
```python
SILICONFLOW_API_KEY = "your_api_key_here"
```

### 区域配置
- `regions.json`: 自动保存的OCR识别区域
- 支持多个区域，建议配置角色名和对话文本区域

### 音频文件配置
- `lib/voc/`: 干员音频文件目录
- `lib/voc_data/`: 语音数据CSV文件
- `lib/voc_tmp/`: TTS生成的临时音频文件

## 注意事项

1. **API密钥**: 需要有效的硅基流动API密钥才能使用TTS功能
2. **权限设置**: 
   - macOS: 需要在系统偏好设置中允许应用访问屏幕
   - Windows: 以管理员身份运行
3. **网络连接**: 音频下载和TTS需要稳定的网络连接
4. **存储空间**: 音频文件较多，确保有足够存储空间
5. **识别精度**: OCR识别效果取决于游戏界面清晰度

## 故障排除

### 常见问题

1. **TTS服务不可用**
   - 检查API密钥配置：
     - 确认 `.env` 文件存在且格式正确
     - 验证 `SiliconFlowTTS-key` 值不为空
     - 检查API密钥是否有效
   - 确认网络连接正常
   - 查看API配额使用情况

2. **音频文件缺失**
   - 确认已从 [ModelScope 方舟语音数据集](https://www.modelscope.cn/datasets/FrozenFish114/Arknights_voice_zh) 下载音频数据
   - 检查 `lib/voc/` 和 `lib/voc_data/` 目录是否存在
   - 运行资源完整性检查：`python check_operator_resources.py`
   - 如需重新下载，可运行：`python crawl_all_operators_audio_flexible.py`

3. **OCR识别不准确**
   - 调整识别区域
   - 确保游戏界面清晰
   - 避免复杂背景干扰

4. **状态提示不显示**
   - 检查窗口权限设置
   - 确认Tkinter正常工作
   - 重启应用

5. **环境变量配置问题**
   - 确认 `.env` 文件在项目根目录
   - 检查文件编码为UTF-8
   - 验证变量名格式正确（区分大小写）
   - 重启应用以重新加载环境变量

6. **Python版本问题**
   - 确保使用 Python 3.11 或更高版本
   - 检查虚拟环境是否正确创建：`python --version`
   - 如果版本不匹配，重新创建虚拟环境：
     ```bash
     rm -rf venv
     python3.11 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```

## 开发说明

- 项目使用Python 3.11开发
- 遵循PEP 8代码规范
- 支持模块化扩展
- 完整的错误处理和日志记录

## 更新日志

### v2.0.0
- 新增TTS语音合成功能
- 新增音频文件管理系统
- 新增状态提示系统
- 新增资源完整性检查
- 重构项目结构，优化代码组织

### v1.0.0
- 基础OCR识别功能
- 自定义区域设置
- 快捷键操作支持 