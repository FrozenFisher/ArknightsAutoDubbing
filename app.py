import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from pynput import keyboard
from pynput.mouse import Listener as MouseListener
from pynput.mouse import Button
import pyautogui
import os
from datetime import datetime
import subprocess

# 导入OCR模块（这会触发模型预加载）
print("正在启动OCR应用...")
from lib.ocr import ocr
from lib.tts_service import SiliconFlowTTS

class OCRApp:
    def __init__(self, root: tk.Tk):
        # 绑定主 root（外部创建并隐藏）
        self.root = root
        self.settings_window = None
        self.regions = []
        self.current_region = None
        self.is_selecting = False
        self.start_pos = None
        self.end_pos = None
        self.overlay_window = None
        self.overlay_canvas = None
        self.last_ocr_time = 0  # 添加防抖时间记录
        # 状态提示窗口
        self.status_window = None
        self.status_label = None
        
        # TTS 客户端（若无API Key则内部降级为不可用）
        self.tts = SiliconFlowTTS()
        
        # 最近一次有效的角色名，用于当本轮未识别到角色名时回退使用
        self.last_char_name = None
        
        # 加载保存的区域设置
        self.load_regions()
        
        # 启动键盘监听
        self.start_keyboard_listener()
        
        print("OCR应用已启动")
        print("快捷键说明:")
        print("- 空格键: 识别当前设置的区域")
        print("- F12: 打开设置界面")
        print("- Ctrl+Q: 退出应用")

        # 显示初始等待状态
        self.show_status("等待")

    def _ensure_status_window(self):
        if self.status_window and tk.Toplevel.winfo_exists(self.status_window):
            return
        # 创建小型置顶无边框状态窗
        self.status_window = tk.Toplevel(self.root)
        self.status_window.overrideredirect(True)
        self.status_window.attributes('-topmost', True)
        try:
            self.status_window.attributes('-alpha', 0.92)
        except Exception:
            pass
        frame = tk.Frame(self.status_window, bg='#111111', bd=0, highlightthickness=0)
        frame.pack(fill='both', expand=True)
        self.status_label = tk.Label(
            frame,
            text="",
            fg='#FFFFFF',
            bg='#111111',
            font=('Arial', 14, 'bold'),
            padx=12,
            pady=8
        )
        self.status_label.pack()

    def show_status(self, text: str, duration_ms: int | None = None):
        """在屏幕左上角显示状态提示。duration_ms 提供时，超时后自动隐藏。"""
        try:
            self._ensure_status_window()
            # 固定左上角（稍作内边距）
            pos_x, pos_y = 20, 20
            self.status_window.geometry(f"+{pos_x}+{pos_y}")
            self.status_label.config(text=text)
            self.status_window.deiconify()
            self.status_window.lift()
            # 保持最前并强制刷新，避免长任务期间无法立即渲染
            try:
                self.status_window.attributes('-topmost', True)
            except Exception:
                pass
            self.status_window.update_idletasks()
            self.status_window.update()
            if duration_ms is not None:
                self.status_window.after(duration_ms, self.hide_status)
        except Exception:
            pass

    def hide_status(self):
        try:
            if self.status_window and tk.Toplevel.winfo_exists(self.status_window):
                self.status_window.withdraw()
        except Exception:
            pass

    def play_audio(self, wav_path: str):
        """异步播放音频（macOS 使用 afplay；失败则忽略）。"""
        def _run():
            try:
                if os.path.exists(wav_path):
                    # macOS 使用 afplay
                    subprocess.run(["afplay", wav_path], check=False)
            except Exception:
                pass
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        
    def load_regions(self):
        """加载保存的区域设置"""
        try:
            with open('regions.json', 'r', encoding='utf-8') as f:
                self.regions = json.load(f)
        except FileNotFoundError:
            self.regions = []
        
    def save_regions(self):
        """保存区域设置"""
        with open('regions.json', 'w', encoding='utf-8') as f:
            json.dump(self.regions, f, ensure_ascii=False, indent=2)
    
    def start_keyboard_listener(self):
        """启动键盘监听"""
        def on_press(key):
            try:
                # 空格键 - 识别文字
                if key == keyboard.Key.space:
                    self.show_status("ocr识别")
                    self.recognize_text()
                
                # F12 - 打开设置
                elif key == keyboard.Key.f12:
                    self.open_settings()
                
                # Ctrl+Q - 退出应用
                elif (hasattr(key, 'char') and key.char == 'q' and 
                      any(mod == keyboard.Key.ctrl for mod in self.current_modifiers)):
                    self.quit_app()
             
            except AttributeError:
                pass
         
        def on_release(key):
            pass
         
        self.current_modifiers = set()
         
        def on_press_with_modifiers(key):
            if key in [keyboard.Key.shift, keyboard.Key.ctrl, keyboard.Key.alt]:
                self.current_modifiers.add(key)
            on_press(key)
         
        def on_release_with_modifiers(key):
            if key in [keyboard.Key.shift, keyboard.Key.ctrl, keyboard.Key.alt]:
                self.current_modifiers.discard(key)
            on_release(key)
         
         # 启动监听器
        self.listener = keyboard.Listener(
            on_press=on_press_with_modifiers,
            on_release=on_release_with_modifiers
        )
        self.listener.start()
    
    def recognize_text(self):
        """识别文字并驱动TTS（当可用）"""
        # 检查是否在冷却期内
        current_time = time.time()
        if current_time - self.last_ocr_time < 1.0:  # 1秒防抖
            print(f"OCR冷却中，还需等待 {1.0 - (current_time - self.last_ocr_time):.1f} 秒")
            return
        
        # 更新最后OCR时间
        self.last_ocr_time = current_time
        
        if not self.regions:
            print("没有设置识别区域，请先按F12打开设置")
            self.show_status("等待", duration_ms=800)
            return
        
        print(f"开始识别 {len(self.regions)} 个区域...")
        
        name_text = None
        content_text = None
        all_results = []  # 存储所有区域的识别结果（拼接用）
        
        for i, region in enumerate(self.regions):
            try:
                result = ocr(region['start'], region['end'])
                name = region.get('name', f'区域{i+1}')
                if result:
                    print(f"[{name}] {result}")
                    all_results.append(result)
                    # 简单的命名约定：包含“名”/"name" 的区域当作角色名；包含“文案”/"text" 的区域当作文案
                    lname = name.lower()
                    if ('名' in name) or ('name' in lname):
                        name_text = result.strip()
                    if ('文案' in name) or ('text' in lname) or ('台词' in name) or ('对白' in name):
                        content_text = result.strip()
                else:
                    print(f"[{name}] 未识别到文字")
            except Exception as e:
                print(f"[{name}] 识别失败: {e}")
        
        # 将所有结果拼接成一个字符串
        final_text = ''
        if all_results:
            final_text = ' '.join(all_results)
            print(f"\n完整识别结果: {final_text}")
        else:
            print("\n未识别到任何文字")
        
        # 角色名回退逻辑：若本轮未识别到角色名，则沿用上一次有效角色名
        if name_text:
            self.last_char_name = name_text
        elif self.last_char_name:
            name_text = self.last_char_name
            print(f"角色名未识别，沿用上一次角色：{name_text}")
        
        # 若具备角色名与文案，尝试用硅基流动TTS
        try:
            if name_text and content_text and hasattr(self, 'tts') and self.tts.api_key:
                # 查找参考音频和文本（limit=1）
                from lib.ref.loader import find_audio_with_text_by_char_name
                ref_results = find_audio_with_text_by_char_name(name_text, limit=1)
                print(ref_results)
                voice_uri = None
                if ref_results:
                    self.show_status("正在上传音色")
                    ref_data = ref_results[0]
                    ref_path = ref_data['file_path']
                    ref_text = ref_data['voice_text']
                    # 以角色名为key，上传或复用音色，使用参考文本
                    voice_uri = self.tts.ensure_voice(name_key=name_text, wav_path=ref_path, ref_text=ref_text)
                
                # 合成
                self.show_status("正在tts")
                audio_bytes = self.tts.synthesize(content_text, voice_uri=voice_uri)
                if audio_bytes:
                    os.makedirs('lib/voc_tmp', exist_ok=True)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    out_path = os.path.abspath(os.path.join('lib/voc_tmp', f'tts_{ts}.wav'))
                    with open(out_path, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"TTS已生成: {out_path}")
                    # 自动播放并恢复等待状态
                    self.play_audio(out_path)
                    self.show_status("等待", duration_ms=1000)
                else:
                    print("TTS生成失败或未返回音频。")
                    self.show_status("等待", duration_ms=1000)
        except Exception as e:
            print(f"TTS流程异常: {e}")
            self.show_status("等待", duration_ms=1000)
        
        return final_text
    
    def open_settings(self):
        """打开设置界面"""
        if self.settings_window:
            self.settings_window.lift()
            return
    
        self.settings_window = tk.Toplevel()
        self.settings_window.title("OCR设置")
        self.settings_window.geometry("600x500")
        self.settings_window.resizable(True, True)
    
        # 创建主框架
        main_frame = ttk.Frame(self.settings_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
        # 标题
        title_label = ttk.Label(main_frame, text="OCR识别区域设置", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
    
        # 说明文字
        info_label = ttk.Label(main_frame, text="点击'添加区域'按钮，然后在屏幕上拖动鼠标选择识别区域")
        info_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))
    
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))
    
        # 添加区域按钮
        add_btn = ttk.Button(button_frame, text="添加区域", command=self.add_region)
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
    
        # 清除所有区域按钮
        clear_btn = ttk.Button(button_frame, text="清除所有区域", command=self.clear_regions)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
    
        # 测试识别按钮
        test_btn = ttk.Button(button_frame, text="测试识别", command=self.test_recognition)
        test_btn.pack(side=tk.LEFT)
    
        # 区域列表框架
        list_frame = ttk.LabelFrame(main_frame, text="当前区域列表", padding="10")
        list_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
    
        # 创建Treeview显示区域列表
        columns = ('序号', '名称', '起始坐标', '结束坐标', '操作')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
    
        for col in columns:
            self.tree.heading(col, text=col)
            if col == '名称':
                self.tree.column(col, width=100)
            elif col == '操作':
                self.tree.column(col, width=80)
            else:
                self.tree.column(col, width=120)
    
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
    
        # 配置网格权重
        self.settings_window.columnconfigure(0, weight=1)
        self.settings_window.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
    
        # 更新区域列表
        self.update_region_list()
    
        # 绑定窗口关闭事件
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)
    
    def add_region(self):
        """添加识别区域"""
        self.settings_window.withdraw()  # 隐藏设置窗口
        
        # 使用pynput监听全局鼠标事件来选择区域
        print("开始区域选择模式...")
        print("请切换到目标应用，然后按住鼠标左键拖动选择区域")
        print("选择完成后会自动保存区域")
        
        # 创建透明全屏覆盖窗口用于显示选择框
        self.create_overlay_window()
        
        # 创建选择区域窗口 - 最小化且置顶
        self.selection_window = tk.Toplevel()
        self.selection_window.geometry("1x1+0+0")  # 最小化窗口
        self.selection_window.attributes('-topmost', True)
        self.selection_window.attributes('-alpha', 0.01)  # 几乎完全透明
        self.selection_window.configure(bg='black')
        
        # 绑定ESC键取消选择
        self.selection_window.bind("<Escape>", self.cancel_selection)
        
        # 使用pynput监听全局鼠标事件
        self.is_selecting = False
        self.start_pos = None
        self.end_pos = None
        
        # 启动全局鼠标监听
        self.mouse_listener = MouseListener(
            on_click=self.on_global_mouse_click,
            on_move=self.on_global_mouse_move
        )
        self.mouse_listener.start()
        
        # 显示提示窗口
        self.show_selection_hint()
    
    def show_selection_hint(self):
        """显示选择提示窗口"""
        self.hint_window = tk.Toplevel()
        self.hint_window.title("区域选择提示")
        self.hint_window.geometry("400x200")
        self.hint_window.attributes('-topmost', True)
        
        # 居中显示
        self.hint_window.update_idletasks()
        x = (self.hint_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.hint_window.winfo_screenheight() // 2) - (200 // 2)
        self.hint_window.geometry(f"400x200+{x}+{y}")
        
        # 提示内容
        ttk.Label(self.hint_window, text="区域选择模式", font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Label(self.hint_window, text="1. 切换到目标应用窗口").pack(pady=5)
        ttk.Label(self.hint_window, text="2. 按住鼠标左键拖动选择区域").pack(pady=5)
        ttk.Label(self.hint_window, text="3. 释放鼠标完成选择").pack(pady=5)
        ttk.Label(self.hint_window, text="4. 按ESC键取消选择").pack(pady=5)
        
        # 关闭提示窗口时取消选择
        self.hint_window.protocol("WM_DELETE_WINDOW", self.cancel_selection)
    
    def create_overlay_window(self):
        """创建透明覆盖窗口用于显示选择框"""
        self.overlay_window = tk.Toplevel()
        
        # 获取屏幕尺寸
        screen_width = self.overlay_window.winfo_screenwidth()
        screen_height = self.overlay_window.winfo_screenheight()
        
        # 设置为全屏透明窗口
        self.overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', 0.3)  # 设置透明度
        self.overlay_window.overrideredirect(True)  # 移除窗口边框
        self.overlay_window.configure(bg='black')
        
        # 创建画布
        self.overlay_canvas = tk.Canvas(
            self.overlay_window,
            width=screen_width,
            height=screen_height,
            bg='gray10',  # 使用深灰色背景
            highlightthickness=0
        )
        self.overlay_canvas.pack()
        
        # 绑定点击事件让窗口可以穿透（虽然在macOS上有限制）
        self.overlay_canvas.bind("<Button-1>", self.pass_through_click)
    
    def on_global_mouse_click(self, x, y, button, pressed):
        """全局鼠标点击事件"""
        if button == Button.left:
            if pressed:
                # 鼠标按下
                self.is_selecting = True
                self.start_pos = (x, y)
                print(f"开始选择区域: ({x}, {y})")
            else:
                # 鼠标释放
                if self.is_selecting:
                    self.is_selecting = False
                    self.end_pos = (x, y)
                    print(f"完成选择区域: ({x}, {y})")
                    self.finish_global_selection()
    
    def on_global_mouse_move(self, x, y):
        """全局鼠标移动事件"""
        if self.is_selecting and self.overlay_canvas:
            # 清除之前的选择框
            self.overlay_canvas.delete("selection_rect")
            
            # 绘制新的选择框
            if self.start_pos:
                start_x, start_y = self.start_pos
                
                # 确保坐标顺序正确
                left = min(start_x, x)
                top = min(start_y, y)
                right = max(start_x, x)
                bottom = max(start_y, y)
                
                # 绘制红色选择框
                self.overlay_canvas.create_rectangle(
                    left, top, right, bottom,
                    outline='red',
                    width=3,
                    tags="selection_rect"
                )
                
                # 绘制半透明填充
                self.overlay_canvas.create_rectangle(
                    left, top, right, bottom,
                    fill='red',
                    stipple='gray25',
                    tags="selection_rect"
                )
            
            # 实时显示选择区域坐标（可选，用于调试）
            print(f"选择中: ({self.start_pos[0]}, {self.start_pos[1]}) -> ({x}, {y})")
    
    def finish_global_selection(self):
        """完成全局区域选择"""
        if self.start_pos and self.end_pos:
            # 确保坐标顺序正确
            x1, y1 = self.start_pos
            x2, y2 = self.end_pos
            
            start_x = min(x1, x2)
            start_y = min(y1, y2)
            end_x = max(x1, x2)
            end_y = max(y1, y2)
            
            # 显示最终选择的区域并保持一段时间
            self.show_final_selection(start_x, start_y, end_x, end_y)
        
            # 延迟一下让用户看到选择的区域
            self.overlay_window.after(1000, lambda: self.show_name_dialog(start_x, start_y, end_x, end_y))
        else:
            # 如果没有选择区域，直接清理资源
            self.cleanup_selection()
    
    def show_final_selection(self, start_x, start_y, end_x, end_y):
        """显示最终选择的区域"""
        if self.overlay_canvas:
            # 清除之前的选择框
            self.overlay_canvas.delete("selection_rect")
            
            # 绘制最终的红色选择框（更加突出）
            self.overlay_canvas.create_rectangle(
                start_x, start_y, end_x, end_y,
                outline='red',
                width=5,  # 更粗的边框
                tags="selection_rect"
            )
            
            # 绘制半透明填充
            self.overlay_canvas.create_rectangle(
                start_x, start_y, end_x, end_y,
                fill='red',
                stipple='gray25',
                tags="selection_rect"
            )
            
            # 在选择框中间显示坐标信息
            center_x = (start_x + end_x) // 2
            center_y = (start_y + end_y) // 2
            coord_text = f"({start_x},{start_y}) - ({end_x},{end_y})"
            
            # 创建白色背景的文本标签
            self.overlay_canvas.create_rectangle(
                center_x - 80, center_y - 15, center_x + 80, center_y + 15,
                fill='white',
                outline='black',
                tags="selection_rect"
            )
            
            self.overlay_canvas.create_text(
                center_x, center_y,
                text=coord_text,
                fill='black',
                font=('Arial', 10, 'bold'),
                tags="selection_rect"
            )
            
            print(f"选择区域确认: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
    
    def show_name_dialog(self, start_x, start_y, end_x, end_y):
        """显示区域命名对话框"""
        # 清理覆盖窗口，让命名对话框能正常显示
        if hasattr(self, 'overlay_window') and self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
            self.overlay_canvas = None
        
        self.name_dialog = tk.Toplevel()
        self.name_dialog.title("区域命名")
        self.name_dialog.geometry("300x150")
        self.name_dialog.attributes('-topmost', True)
        
        # 居中显示
        self.name_dialog.update_idletasks()
        x = (self.name_dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.name_dialog.winfo_screenheight() // 2) - (150 // 2)
        self.name_dialog.geometry(f"300x150+{x}+{y}")
        
        # 提示文字
        ttk.Label(self.name_dialog, text="请为这个区域命名:").pack(pady=10)
        
        # 输入框
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(self.name_dialog, textvariable=self.name_var, width=30)
        name_entry.pack(pady=10)
        name_entry.focus()
        
        # 按钮框架
        button_frame = ttk.Frame(self.name_dialog)
        button_frame.pack(pady=10)
        
        # 确定按钮
        ttk.Button(button_frame, text="确定", command=lambda: self.save_named_region(start_x, start_y, end_x, end_y)).pack(side=tk.LEFT, padx=5)
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self.cancel_naming).pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        name_entry.bind("<Return>", lambda e: self.save_named_region(start_x, start_y, end_x, end_y))
        
        # 关闭对话框时取消
        self.name_dialog.protocol("WM_DELETE_WINDOW", self.cancel_naming)
    
    def save_named_region(self, start_x, start_y, end_x, end_y):
        """保存命名区域"""
        name = self.name_var.get().strip()
        if not name:
            name = f"区域{len(self.regions) + 1}"
        
        # 添加新区域
        new_region = {
            'name': name,
            'start': [start_x, start_y],
            'end': [end_x, end_y]
        }
        self.regions.append(new_region)
        
        # 保存设置
        self.save_regions()
        
        # 更新显示
        self.update_region_list()
        
        print(f"添加新区域 '{name}': 起始({start_x}, {start_y}) 结束({end_x}, {end_y})")
        
        # 关闭对话框
        self.name_dialog.destroy()
    
    def cancel_naming(self):
        """取消命名"""
        if hasattr(self, 'name_dialog'):
            self.name_dialog.destroy()
    
    def cleanup_selection(self):
        """清理选择资源"""
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        
        if hasattr(self, 'hint_window'):
            self.hint_window.destroy()
        
        if hasattr(self, 'selection_window'):
            self.selection_window.destroy()
            
        if hasattr(self, 'overlay_window') and self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
            self.overlay_canvas = None
        
        self.settings_window.deiconify()
    
    def cancel_selection(self, event=None):
        """取消选择"""
        print("取消区域选择")
        self.cleanup_selection()
    
    def pass_through_click(self, event):
        """让点击事件穿透透明窗口"""
        # 在macOS上，Tkinter透明窗口的点击穿透有限制
        # 这里我们简单地忽略点击事件，让pynput处理全局鼠标事件
        pass
    
    def update_region_list(self):
        """更新区域列表显示"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加区域到列表
        for i, region in enumerate(self.regions):
            start_x, start_y = region['start']
            end_x, end_y = region['end']
            name = region.get('name', f'区域{i+1}')
            
            self.tree.insert('', 'end', values=(
                f"{i+1}",
                name,
                f"({start_x}, {start_y})",
                f"({end_x}, {end_y})",
                "删除"
            ))
        
        # 绑定删除事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
    
    def on_tree_double_click(self, event):
        """双击树形列表事件"""
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)
        
        if column == '#5':  # 操作列
            index = int(self.tree.item(item)['values'][0]) - 1
            self.delete_region(index)
    
    def delete_region(self, index):
        """删除指定区域"""
        if 0 <= index < len(self.regions):
            deleted_region = self.regions.pop(index)
            self.save_regions()
            self.update_region_list()
            print(f"删除区域 {index+1}: {deleted_region}")
    
    def clear_regions(self):
        """清除所有区域"""
        if messagebox.askyesno("确认", "确定要清除所有区域吗？"):
            self.regions.clear()
            self.save_regions()
            self.update_region_list()
            print("已清除所有区域")
    
    def test_recognition(self):
        """测试识别功能"""
        if not self.regions:
            messagebox.showwarning("警告", "没有设置识别区域")
            return
        
        self.recognize_text()
    
    def close_settings(self):
        """关闭设置窗口"""
        self.settings_window.destroy()
        self.settings_window = None
    
    def quit_app(self):
        """退出应用"""
        print("正在退出OCR应用...")
        # 关闭状态窗
        try:
            self.hide_status()
            if self.status_window:
                self.status_window.destroy()
        except Exception:
            pass
        if self.listener:
            self.listener.stop()
        if self.settings_window:
            self.settings_window.destroy()
        exit(0)

def main():
    """主函数"""
    # 创建主窗口（隐藏），先创建 root 再实例化 App，避免多 root 导致 Toplevel 不刷新
    root = tk.Tk()
    root.withdraw()
    app = OCRApp(root)
    
    # 运行主循环
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.quit_app()

if __name__ == "__main__":
    main() 