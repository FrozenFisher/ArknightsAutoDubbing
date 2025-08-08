import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import ImageGrab
import time
import os
from datetime import datetime

# 全局OCR引擎实例，启动时预加载
print("正在初始化OCR引擎...")
ocr_engine = PaddleOCR(
    lang="ch",  # 使用中文模型
    use_doc_orientation_classify=False,  # 不使用文档方向分类模型
    use_doc_unwarping=False,  # 不使用文本图像矫正模型
    use_textline_orientation=False,  # 不使用文本行方向分类模型
)
print("OCR引擎初始化完成！")

def ocr(start_xy, end_xy):
    """
    对指定区域进行OCR识别
    
    Args:
        start_xy (tuple): 开始坐标 (x, y)
        end_xy (tuple): 结束坐标 (x, y)
    
    Returns:
        str: 识别出的文字
    """
    try:
        # 计算截图区域
        x1, y1 = start_xy
        x2, y2 = end_xy
        
        # 确保坐标顺序正确
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # 截取屏幕区域
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        
        # 保存截图用于OCR识别
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        ocr_image_path = f"TEMP/ocr_input_{timestamp}.png"
        os.makedirs("TEMP", exist_ok=True)
        screenshot.save(ocr_image_path)
        
        # 进行OCR识别
        result = ocr_engine.predict(ocr_image_path)
        
        # 提取文字结果
        texts = []
        if result and len(result) > 0:
            for res in result:
                try:
                    # OCR结果在嵌套的res字典中
                    if 'res' in res.json:
                        ocr_res = res.json['res']
                        
                        # 从嵌套的res中提取rec_texts
                        if 'rec_texts' in ocr_res:
                            rec_texts = ocr_res['rec_texts']
                            rec_scores = ocr_res.get('rec_scores', [])
                            
                            # 过滤置信度较高的文本
                            for i, text in enumerate(rec_texts):
                                if i < len(rec_scores) and rec_scores[i] > 0.5:  # 置信度大于0.5
                                    texts.append(str(text))
                                elif i >= len(rec_scores):  # 如果没有对应的置信度，也添加
                                    texts.append(str(text))
                    
                except Exception as e:
                    print(f"处理OCR结果时出错: {e}")
        
        result_text = ''.join(texts) if texts else ""
        
        # 删除临时图片文件
        try:
            if os.path.exists(ocr_image_path):
                os.remove(ocr_image_path)
        except Exception as e:
            print(f"删除临时文件失败: {e}")
        
        return result_text
        
    except Exception as e:
        print(f"OCR识别出错: {e}")
        import traceback
        traceback.print_exc()
        return f"OCR识别失败: {str(e)}"

def test_ocr():
    """测试OCR功能"""
    print("测试OCR功能...")
    # 测试一个小的屏幕区域
    result = ocr((100, 100), (300, 150))
    print(f"识别结果: {result}") 