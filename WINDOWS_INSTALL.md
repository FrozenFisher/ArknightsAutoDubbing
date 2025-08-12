# Windows 用户安装指南

## 快速安装步骤

### 1. 环境准备
确保你的系统已安装 Python 3.11 或更高版本。

### 2. 下载项目
```cmd
git clone https://github.com/your-repo/ArknightsAutoDubbing.git
cd ArknightsAutoDubbing
```

### 3. 创建虚拟环境
```cmd
python -m venv venv
venv\Scripts\activate
```

### 4. 安装依赖（推荐使用GBK编码文件）
```cmd
pip install -r requirements_gbk.txt
```

### 5. 配置环境变量
复制环境变量模板文件：
```cmd
copy .env_example .env
```

编辑 `.env` 文件，填入你的硅基流动API密钥：
```
SiliconFlowTTS-key=your_actual_api_key_here
SiliconFlowTTS-endpoint=https://api.siliconflow.cn/v1
```

### 6. 下载音频数据
访问 [ModelScope 方舟语音数据集](https://www.modelscope.cn/datasets/FrozenFish114/Arknights_voice_zh)
下载 `voc` 和 `voc_data` 压缩包，解压到项目根目录。

### 7. 运行应用
```cmd
python app.py
```

## 常见问题解决

### 编码问题
如果遇到编码错误，请：
1. 使用 `requirements_gbk.txt` 而不是 `requirements.txt`
2. 设置环境变量：`set PYTHONIOENCODING=utf-8`
3. 确保控制台支持中文显示

### 权限问题
如果遇到权限错误，请：
1. 以管理员身份运行命令提示符
2. 确保防火墙允许应用访问网络

### 音频播放问题
如果TTS音频无法播放：
1. 确保系统音量已开启
2. 检查音频文件格式是否为WAV
3. 查看控制台输出的播放日志

## 快捷键说明
- **空格键**: 识别当前设置的区域并生成TTS配音
- **F12**: 打开设置界面
- **Shift+Ctrl+Q**: 退出应用

## 技术支持
如果遇到问题，请：
1. 查看控制台输出的错误信息
2. 检查README.md中的故障排除部分
3. 提交Issue时请包含详细的错误日志 