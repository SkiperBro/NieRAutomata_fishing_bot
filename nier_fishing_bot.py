import pyautogui
import ctypes
import time
import soundcard
import argparse
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import sys
import numpy as np
import json
import os
from collections import deque

# https://stackoverflow.com/questions/14489013/simulate-python-keypresses-for-controlling-a-game
SendInput = ctypes.windll.user32.SendInput

ESC = 0x01
DOWN = 0xD0
ENTER = 0x1C

PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

def presskey(hexkeycode, holdlength=0.1):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexkeycode, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    time.sleep(holdlength)
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexkeycode, 0x0008 | 0x0002, 0,
                        ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

class FishingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NieR Automata Fishing Bot v2")
        self.root.geometry("800x600")
        
        # Language settings
        self.language = "EN"  # Default to English
        self.translations = {
            "EN": {
                "title": "NieR Automata Fishing Bot v2",
                "status_stopped": "Status: Stopped",
                "status_starting": "Status: Starting...",
                "status_running": "Status: Running",
                "status_calibrating": "Status: Calibrating...",
                "audio_level": "Audio Level: ",
                "fish_counter": "🐟 Caught: ",
                "start_button": "🎣 Start",
                "stop_button": "⏹️ Stop",
                "calibrate_button": "🎚️ Calibrate",
                "settings_label": "Settings",
                "threshold_label": "Threshold:",
                "sensitivity_label": "Sensitivity:",
                "auto_calibration": "Auto-calibration",
                "stats_label": "Statistics",
                "log_label": "Activity Log",
                "total_caught": "Total caught: ",
                "current_threshold": "Current threshold: ",
                "background_level": "Background level: ",
                "sensitivity_value": "Sensitivity: ",
                "instructions": """💡 INSTRUCTIONS:
1. Enable Stereo Mix in Windows sound settings
2. Disable music and voices in game settings
3. Stand near water and press 'Calibrate'
4. Start bot when threshold is properly set""",
                "calibration_start": "Calibration... Listening to background noise for 5 seconds",
                "calibration_complete": "Calibration complete!",
                "avg_background": "Average background: ",
                "max_background": "Max background: ",
                "threshold_set": "Threshold set: ",
                "fish_detected_at": "Fish will be detected at: >",
                "calibration_error": "Calibration error: ",
                "start_bot": "Starting fishing bot...",
                "detection_threshold": "Detection threshold: ",
                "audio_error": "Audio error: ",
                "using_device": "Using device: ",
                "bot_started": "Bot started!",
                "casting": "Casting...",
                "waiting_bite": "Waiting for bite...",
                "caught": "CAUGHT! Level: ",
                "threshold": " (threshold: ",
                "fish_caught": "Fish caught! Total: ",
                "no_bite": "No bite",
                "error": "Error: ",
                "critical_error": "Critical error: ",
                "bot_stopped": "Bot stopped",
                "config_error": "Error in settings! Check numeric values"
            },
            "RU": {
                "title": "NieR Automata Fishing Bot v2",
                "status_stopped": "Статус: Остановлен",
                "status_starting": "Статус: Запуск...",
                "status_running": "Статус: Работает",
                "status_calibrating": "Статус: Калибровка...",
                "audio_level": "Уровень звука: ",
                "fish_counter": "🐟 Поймано: ",
                "start_button": "🎣 Запустить",
                "stop_button": "⏹️ Остановить",
                "calibrate_button": "🎚️ Калибровать",
                "settings_label": "Настройки",
                "threshold_label": "Порог звука:",
                "sensitivity_label": "Чувствительность:",
                "auto_calibration": "Авто-калибровка",
                "stats_label": "Статистика",
                "log_label": "Лог работы",
                "total_caught": "Всего поймано: ",
                "current_threshold": "Текущий порог: ",
                "background_level": "Фоновый уровень: ",
                "sensitivity_value": "Чувствительность: ",
                "instructions": """💡 ИНСТРУКЦИЯ:
1. Включите Stereo Mix в настройках звука Windows
2. В игре отключите музыку и голоса
3. Встаньте у воды и нажмите 'Калибровать'
4. Запустите бота когда порог будет настроен""",
                "calibration_start": "Калибровка... Слушаем фоновый шум 5 секунд",
                "calibration_complete": "Калибровка завершена!",
                "avg_background": "Средний фон: ",
                "max_background": "Максимальный фон: ",
                "threshold_set": "Установлен порог: ",
                "fish_detected_at": "Рыба будет detected при: >",
                "calibration_error": "Ошибка калибровки: ",
                "start_bot": "Запуск рыболовного бота...",
                "detection_threshold": "Порог обнаружения: ",
                "audio_error": "Ошибка аудио: ",
                "using_device": "Используется: ",
                "bot_started": "Бот начал работу!",
                "casting": "Забрасываем удочку...",
                "waiting_bite": "Ожидаем поклёвку...",
                "caught": "ПОЙМАНО! Уровень: ",
                "threshold": " (порог: ",
                "fish_caught": "Улов! Всего поймано: ",
                "no_bite": "Рыба не клюнула",
                "error": "Ошибка: ",
                "critical_error": "Критическая ошибка: ",
                "bot_stopped": "Бот остановлен",
                "config_error": "Ошибка в настройках! Проверьте числовые значения"
            }
        }
        
        self.running = False
        self.calibrating = False
        self.bot_thread = None
        self.mic = None
        self.fish_count = 0
        self.audio_levels = deque(maxlen=100)
        self.config_file = "fishing_bot_config.json"
        self.background_level = 0.0
        
        self.load_config()
        self.setup_gui()
        self.update_audio_meter()
        
    def t(self, key):
        """Get translation for current language"""
        return self.translations[self.language].get(key, key)
        
    def load_config(self):
        self.config = {
            "threshold": 0.001,
            "sensitivity": 1.8,  # Changed from 2.0 to 1.8
            "auto_calibration": True,
            "fish_count": 0,
            "background_level": 0.0005,
            "language": "EN"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                    self.fish_count = self.config.get("fish_count", 0)
                    self.background_level = self.config.get("background_level", 0.0005)
                    self.language = self.config.get("language", "EN")
            except:
                pass
    
    def save_config(self):
        self.config["fish_count"] = self.fish_count
        self.config["background_level"] = self.background_level
        self.config["language"] = self.language
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and stats
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=5)
        
        title_label = tk.Label(header_frame, text=self.t("title"), font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Language selector
        lang_frame = tk.Frame(header_frame)
        lang_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(lang_frame, text="Language:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value=self.language)
        lang_dropdown = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=["EN", "RU"], width=5, state="readonly")
        lang_dropdown.pack(side=tk.LEFT, padx=5)
        lang_dropdown.bind("<<ComboboxSelected>>", self.change_language)
        
        self.fish_counter = tk.Label(header_frame, text=f"{self.t('fish_counter')}{self.fish_count}", 
                                   font=("Arial", 12), fg="blue")
        self.fish_counter.pack(side=tk.RIGHT, padx=10)
        
        # Status frame
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(status_frame, text=self.t("status_stopped"), font=("Arial", 12), fg="red")
        self.status_label.pack(side=tk.LEFT)
        
        # Audio meter
        self.audio_meter = ttk.Progressbar(main_frame, orient='horizontal', length=200, mode='determinate')
        self.audio_meter.pack(fill=tk.X, pady=5)
        
        self.audio_label = tk.Label(main_frame, text=f"{self.t('audio_level')}0.0000", font=("Arial", 10))
        self.audio_label.pack(pady=2)
        
        self.threshold_line = tk.Canvas(main_frame, height=2, bg='red')
        self.threshold_line.pack(fill=tk.X, pady=2)
        
        # Controls frame
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = tk.Button(controls_frame, text=self.t("start_button"), command=self.start_bot, 
                                    bg="green", fg="white", font=("Arial", 10))
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(controls_frame, text=self.t("stop_button"), command=self.stop_bot, 
                                   bg="red", fg="white", font=("Arial", 10), state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.calibrate_button = tk.Button(controls_frame, text=self.t("calibrate_button"), command=self.calibrate_audio,
                                        bg="orange", fg="white", font=("Arial", 10))
        self.calibrate_button.pack(side=tk.LEFT, padx=5)
        
        # Settings frame
        settings_frame = tk.LabelFrame(main_frame, text=self.t("settings_label"), font=("Arial", 10, "bold"))
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Threshold settings
        threshold_frame = tk.Frame(settings_frame)
        threshold_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(threshold_frame, text=self.t("threshold_label")).pack(side=tk.LEFT)
        self.threshold_var = tk.StringVar(value=str(self.config["threshold"]))
        threshold_entry = tk.Entry(threshold_frame, textvariable=self.threshold_var, width=8)
        threshold_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(threshold_frame, text=self.t("sensitivity_label")).pack(side=tk.LEFT, padx=(20, 5))
        self.sensitivity_var = tk.StringVar(value=str(self.config["sensitivity"]))
        sensitivity_entry = tk.Entry(threshold_frame, textvariable=self.sensitivity_var, width=8)
        sensitivity_entry.pack(side=tk.LEFT, padx=5)
        
        # Auto calibration
        auto_calib_frame = tk.Frame(settings_frame)
        auto_calib_frame.pack(fill=tk.X, pady=2)
        
        self.auto_calib_var = tk.BooleanVar(value=self.config["auto_calibration"])
        auto_calib_check = tk.Checkbutton(auto_calib_frame, text=self.t("auto_calibration"), 
                                        variable=self.auto_calib_var, font=("Arial", 9))
        auto_calib_check.pack(side=tk.LEFT)
        
        # Stats frame
        stats_frame = tk.LabelFrame(main_frame, text=self.t("stats_label"), font=("Arial", 10, "bold"))
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, font=("Arial", 9))
        self.stats_text.pack(fill=tk.X, pady=2)
        self.update_stats()
        
        # Log area
        log_frame = tk.LabelFrame(main_frame, text=self.t("log_label"), font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Instructions
        instructions = tk.Label(main_frame, text=self.t("instructions"), 
                               font=("Arial", 8), fg="gray", justify=tk.LEFT)
        instructions.pack(pady=5)
        
    def change_language(self, event=None):
        self.language = self.lang_var.get()
        self.save_config()
        
        # Update all UI elements
        self.root.title(self.t("title"))
        self.status_label.config(text=self.t("status_stopped"))
        self.audio_label.config(text=f"{self.t('audio_level')}0.0000")
        self.fish_counter.config(text=f"{self.t('fish_counter')}{self.fish_count}")
        self.start_button.config(text=self.t("start_button"))
        self.stop_button.config(text=self.t("stop_button"))
        self.calibrate_button.config(text=self.t("calibrate_button"))
        
        # Update stats
        self.update_stats()
        
        # Update log
        self.log_message("Language changed to " + self.language, "INFO")
        
    def update_stats(self):
        stats = f"{self.t('total_caught')}{self.fish_count}\n"
        stats += f"{self.t('current_threshold')}{self.config['threshold']:.6f}\n"
        stats += f"{self.t('background_level')}{self.background_level:.6f}\n"
        stats += f"{self.t('sensitivity_value')}{self.config['sensitivity']:.1f}x"
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)
        
    def update_audio_meter(self):
        if not self.running and not self.calibrating:
            try:
                if self.mic is None:
                    # Initialize microphone if not already initialized
                    mics = soundcard.all_microphones()
                    for mic in mics:
                        if 'stereo' in mic.name.lower() or 'mix' in mic.name.lower():
                            self.mic = mic
                            break
                    if self.mic is None:
                        self.mic = soundcard.default_microphone()
                
                with self.mic.recorder(samplerate=48000, channels=1) as recorder:
                    data = recorder.record(numframes=1024)
                    volume = np.mean(np.abs(data)) if len(data) > 0 else 0.0
                    
                    self.audio_levels.append(volume)
                    
                    # Update UI
                    self.audio_label.config(text=f"{self.t('audio_level')}{volume:.6f}")
                    meter_value = min(volume * 50000, 100)  # Scale for progressbar
                    self.audio_meter['value'] = meter_value
                    
                    # Update threshold line
                    self.threshold_line.delete("all")
                    threshold_pos = min(self.config["threshold"] * 50000, 100)
                    self.threshold_line.create_line(threshold_pos, 0, threshold_pos, 2, fill="red", width=2)
                    
                    # Indicator color
                    if volume > self.config["threshold"]:
                        self.audio_meter['style'] = 'red.Horizontal.TProgressbar'
                    elif volume > self.background_level * 1.5:
                        self.audio_meter['style'] = 'orange.Horizontal.TProgressbar'
                    else:
                        self.audio_meter['style'] = 'blue.Horizontal.TProgressbar'
                        
            except Exception as e:
                # If error, try to reinitialize next time
                self.mic = None
        
        # Continue updating every 100ms
        if not self.running:
            self.root.after(100, self.update_audio_meter)
        
    def log_message(self, message, level="INFO"):
        colors = {
            "INFO": "black",
            "ERROR": "red",
            "SUCCESS": "green",
            "WARNING": "orange",
            "DEBUG": "blue"
        }
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{level}] {message}\n", level)
        self.log_text.tag_config(level, foreground=colors.get(level, "black"))
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def update_status(self, status, color):
        status_text = f"Status: {status}"
        if status == "Stopped":
            status_text = self.t("status_stopped")
        elif status == "Starting...":
            status_text = self.t("status_starting")
        elif status == "Running":
            status_text = self.t("status_running")
        elif status == "Calibrating...":
            status_text = self.t("status_calibrating")
            
        self.status_label.config(text=status_text, fg=color)
        
    def calibrate_audio(self):
        if self.calibrating:
            return
            
        self.calibrating = True
        self.log_message(self.t("calibration_start"), "INFO")
        self.update_status("Calibrating...", "orange")
        
        def calibration_thread():
            try:
                if self.mic is None:
                    mics = soundcard.all_microphones()
                    for mic in mics:
                        if 'stereo' in mic.name.lower() or 'mix' in mic.name.lower():
                            self.mic = mic
                            break
                    if self.mic is None:
                        self.mic = soundcard.default_microphone()
                
                with self.mic.recorder(samplerate=48000, channels=1) as recorder:
                    background_levels = []
                    for i in range(50):  # 5 seconds
                        if not self.calibrating:
                            break
                        data = recorder.record(numframes=960)
                        volume = np.mean(np.abs(data)) if len(data) > 0 else 0.0
                        background_levels.append(volume)
                        
                        # Update progress in real time
                        if i % 5 == 0:
                            self.log_message(f"Calibration... {i/5:.1f}s, current level: {volume:.6f}", "DEBUG")
                        
                        time.sleep(0.1)
                    
                    if background_levels:
                        self.background_level = np.mean(background_levels)
                        max_background = np.max(background_levels)
                        
                        # Set threshold based on max background level
                        new_threshold = max_background * self.config["sensitivity"]
                        self.config["threshold"] = new_threshold
                        self.threshold_var.set(f"{new_threshold:.6f}")
                        
                        self.log_message(self.t("calibration_complete"), "SUCCESS")
                        self.log_message(f"{self.t('avg_background')}{self.background_level:.6f}", "INFO")
                        self.log_message(f"{self.t('max_background')}{max_background:.6f}", "INFO")
                        self.log_message(f"{self.t('threshold_set')}{new_threshold:.6f}", "SUCCESS")
                        self.log_message(f"{self.t('fish_detected_at')}{new_threshold:.6f}", "INFO")
                        
                        self.update_stats()
                        self.save_config()
                        
            except Exception as e:
                self.log_message(f"{self.t('calibration_error')}{str(e)}", "ERROR")
            finally:
                self.calibrating = False
                self.update_status("Stopped", "red")
                self.update_audio_meter()
                
        threading.Thread(target=calibration_thread, daemon=True).start()
        
    def start_bot(self):
        try:
            # Update settings from UI
            try:
                self.config["threshold"] = float(self.threshold_var.get())
                self.config["sensitivity"] = float(self.sensitivity_var.get())
                self.config["auto_calibration"] = self.auto_calib_var.get()
            except ValueError:
                self.log_message(self.t("config_error"), "ERROR")
                return
                
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.calibrate_button.config(state=tk.DISABLED)
            self.update_status("Starting...", "orange")
            self.log_message(self.t("start_bot"), "INFO")
            self.log_message(f"{self.t('detection_threshold')}{self.config['threshold']:.6f}", "INFO")
            
            # Start in separate thread
            self.bot_thread = threading.Thread(target=self.run_bot)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            
        except Exception as e:
            self.log_message(f"{self.t('error')}{str(e)}", "ERROR")
            self.stop_bot()
            
    def stop_bot(self):
        self.running = False
        self.calibrating = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.calibrate_button.config(state=tk.NORMAL)
        self.update_status("Stopped", "red")
        self.log_message(self.t("bot_stopped"), "INFO")
        self.save_config()
        self.update_audio_meter()
        
    def run_bot(self):
        try:
            # Audio initialization
            try:
                if self.mic is None:
                    mics = soundcard.all_microphones()
                    for mic in mics:
                        if 'stereo' in mic.name.lower() or 'mix' in mic.name.lower():
                            self.mic = mic
                            break
                    if self.mic is None:
                        self.mic = soundcard.default_microphone()
                
                self.log_message(f"{self.t('using_device')}{self.mic.name}", "SUCCESS")
                
            except Exception as e:
                self.log_message(f"{self.t('audio_error')}{str(e)}", "ERROR")
                return
                
            self.update_status("Running", "green")
            self.log_message(self.t("bot_started"), "SUCCESS")
            
            def wait_for_catch():
                try:
                    with self.mic.recorder(samplerate=48000, channels=1) as recorder:
                        for i in range(200):  # 20 seconds
                            if not self.running:
                                return False
                            
                            data = recorder.record(numframes=4800)  # 100ms
                            volume = np.mean(np.abs(data)) if len(data) > 0 else 0.0
                            
                            # ONLY static check against set threshold
                            if volume >= self.config["threshold"]:
                                self.log_message(f"{self.t('caught')}{volume:.6f}{self.t('threshold')}{self.config['threshold']:.6f})", "SUCCESS")
                                return True
                                
                            time.sleep(0.09)
                            
                except Exception as e:
                    self.log_message(f"{self.t('audio_error')}{str(e)}", "ERROR")
                    return False
                    
                return False
            
            # Main loop
            while self.running:
                try:
                    self.log_message(self.t("casting"), "INFO")
                    
                    presskey(DOWN, 2)
                    presskey(ENTER)
                    time.sleep(3)
                    
                    self.log_message(self.t("waiting_bite"), "INFO")
                    catch = wait_for_catch()
                    
                    presskey(ENTER)  # Hook the fish
                    if catch:
                        self.fish_count += 1
                        self.fish_counter.config(text=f"{self.t('fish_counter')}{self.fish_count}")
                        self.log_message(f"{self.t('fish_caught')}{self.fish_count}", "SUCCESS")
                        self.update_stats()
                        time.sleep(9)
                    else:
                        self.log_message(self.t("no_bite"), "WARNING")
                        time.sleep(3)
                        
                except Exception as e:
                    self.log_message(f"{self.t('error')}{str(e)}", "ERROR")
                    time.sleep(2)
                    
        except Exception as e:
            self.log_message(f"{self.t('critical_error')}{str(e)}", "ERROR")
        finally:
            self.stop_bot()

def main():
    try:
        root = tk.Tk()
        
        # Styles for progressbar
        style = ttk.Style()
        style.configure('blue.Horizontal.TProgressbar', background='blue')
        style.configure('orange.Horizontal.TProgressbar', background='orange')
        style.configure('red.Horizontal.TProgressbar', background='red')
        
        app = FishingBotGUI(root)
        
        def on_closing():
            app.running = False
            app.calibrating = False
            app.save_config()
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"Startup error: {e}")

if __name__ == "__main__":
    main()