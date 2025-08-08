# OCR屏幕文字识别工具

一个基于Python的屏幕文字识别工具，支持快捷键操作和自定义识别区域。

## 功能特性

- 🚀 **快速识别**: 1秒内完成屏幕区域文字识别
- ⌨️ **快捷键操作**: 支持全局快捷键，无需切换窗口
- 🎯 **自定义区域**: 可视化设置多个识别区域
- 💾 **设置保存**: 自动保存识别区域配置
- 🌐 **多语言支持**: 支持中文和英文识别

## 快捷键说明

- **空格键**: 识别当前设置的区域
- **F12**: 打开设置界面
- **Ctrl+Q**: 退出应用

## 安装要求

### 系统要求
- Python 3.11+
- macOS/Linux/Windows

### 依赖安装

1. 激活虚拟环境：
```bash
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
```

2. 安装Python依赖：
```bash
pip install -r requirements.txt
```

3. 安装Tesseract OCR引擎：

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # 安装语言包
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim  # 中文简体
```

**Windows:**
- 下载并安装 [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- 确保将Tesseract添加到系统PATH

## 使用方法

1. 启动应用：
```bash
python app.py
```

2. 设置识别区域：
   - 按 `F12` 打开设置界面
   - 点击"添加区域"按钮
   - 在屏幕上拖动鼠标选择要识别的区域
   - 可以设置多个区域

3. 使用识别功能：
   - 按 `空格键` 识别所有设置的区域
   - 识别结果会在控制台输出

**区域选择说明**：
- 点击"添加区域"后会显示提示窗口
- 切换到目标应用（包括全屏应用）
- 按住鼠标左键拖动选择区域
- 释放鼠标完成选择
- 按ESC键取消选择

## 项目结构

```
ArknightsAutoDubbing/
├── app.py              # 主应用文件
├── lib/
│   └── ocr.py         # OCR识别模块
├── requirements.txt    # Python依赖
├── README.md          # 项目说明
├── regions.json       # 区域配置文件（自动生成）
└── TEMP/              # 截屏和调试图像文件夹
```

## 技术栈

- **OCR引擎**: Tesseract
- **图像处理**: OpenCV
- **GUI框架**: Tkinter
- **键盘监听**: pynput
- **屏幕截图**: Pillow

## 注意事项

1. 首次使用需要安装Tesseract OCR引擎
2. 确保系统有足够权限进行屏幕截图
3. 识别准确率取决于文字清晰度和背景对比度
4. 建议在文字区域背景简单的情况下使用
5. 每次识别都会在TEMP文件夹中保存原始截屏和处理后的图像，方便调试

## 故障排除

### 常见问题

1. **Tesseract未找到**
   - 确保已正确安装Tesseract
   - 检查系统PATH设置

2. **权限问题**
   - macOS: 需要在系统偏好设置中允许应用访问屏幕
   - Windows: 以管理员身份运行

3. **识别效果不佳**
   - 调整识别区域，避免复杂背景
   - 确保文字清晰可见
   - 尝试不同的图像预处理参数

## 开发说明

- 项目使用Python 3.11开发
- 遵循PEP 8代码规范
- 支持模块化扩展 