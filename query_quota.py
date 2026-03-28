import time
import jwt
import requests
import json
import tkinter as tk
from tkinter import messagebox
import sys
import io
import os
import warnings

# Ignore PyJWT InsecureKeyLengthWarning
warnings.filterwarnings('ignore', message='The HMAC key is.*')

def get_api_key():
    # exe로 빌드되었을 때와 파이썬 실행시의 경로가 다를 수 있으므로 두 경로 모두 확인
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    # exe로 빌드된 경우 _MEIPASS가 임시 폴더이므로 메인 실행파일 위치 기준으로 찾음
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)

    key_path = os.path.join(base_dir, "key", "zai.key")
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def generate_token(apikey: str, exp_seconds: int = 300):
    try:
        id, secret = apikey.split('.')
    except Exception:
        return None
    payload = {
        'api_key': id,
        'exp': int(round(time.time() * 1000)) + exp_seconds * 1000,
        'timestamp': int(round(time.time() * 1000)),
    }
    return jwt.encode(
        payload,
        secret,
        algorithm='HS256',
        headers={'alg': 'HS256', 'sign_type': 'SIGN'},
    )

def get_zhipu_usage(api_key):
    token = generate_token(api_key)
    if not token:
        return {'error': 'Invalid API Key format'}
    
    url = 'https://api.z.ai/api/monitor/usage/quota/limit'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return {'error': f'Status: {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}

def draw_pie_chart(canvas, x, y, radius, percentage, title):
    # background circle (gray)
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#e0e0e0", outline="")
    
    # slice for used percentage (orange/red)
    if percentage > 0:
        extent = -(percentage / 100.0) * 360 # Negative for clockwise
        canvas.create_arc(x - radius, y - radius, x + radius, y + radius, 
                          start=90, extent=extent, fill="#ff5722", outline="")
    
    # Text in the middle
    canvas.create_text(x, y, text=f"{percentage}%", font=("Arial", 16, "bold"))
    # Title below the pie chart
    canvas.create_text(x, y + radius + 15, text=title, font=("Arial", 10, "bold"))

class QuotaApp:
    def __init__(self, root, api_key):
        self.root = root
        self.api_key = api_key
        self.next_reset_time_sec = 0
        
        self.root.title("Z.ai Quota Monitor")
        self.root.geometry("450x450")
        self.root.attributes("-topmost", True) # Keep window on top
        
        self.canvas = tk.Canvas(root, width=450, height=200)
        self.canvas.pack(pady=10)
        
        self.info_label = tk.Label(root, text="Fetching data...", font=("Arial", 10), justify=tk.CENTER)
        self.info_label.pack(pady=10)
        
        self.reset_label = tk.Label(root, text="", font=("Arial", 12, "bold"), fg="red", justify=tk.CENTER)
        self.reset_label.pack(pady=5)
        
        # Start the update loops
        self.update_data()
        self.update_countdown()
        
    def update_countdown(self):
        if self.next_reset_time_sec > 0:
            diff = int(self.next_reset_time_sec - time.time())
            reset_time_str = time.strftime('%m-%d %H:%M:%S', time.localtime(self.next_reset_time_sec))
            
            if diff > 0:
                hours = diff // 3600
                minutes = (diff % 3600) // 60
                seconds = diff % 60
                self.reset_label.config(text=f"Token Reset In: {hours}h {minutes}m {seconds}s\n(At: {reset_time_str})")
            else:
                self.reset_label.config(text="Token Limit was reset or is resetting now!")
        
        # Schedule the next tick in 1 second
        self.root.after(1000, self.update_countdown)
        
    def update_data(self):
        result = get_zhipu_usage(self.api_key)
        
        if 'error' in result:
            self.info_label.config(text=f"Error: {result['error']}")
        elif 'data' in result and 'limits' in result['data']:
            q_data = result['data']
            level = q_data.get("level", "Unknown").upper()
            
            time_limit = next((l for l in q_data['limits'] if l.get('type') == 'TIME_LIMIT'), None)
            tokens_limit = next((l for l in q_data['limits'] if l.get('type') == 'TOKENS_LIMIT'), None)
            
            self.canvas.delete("all")
            
            info_lines = [f"Plan: {level}"]
            
            # 1. Total Monthly Web Search / Reader / Zread Quota (TIME_LIMIT)
            if time_limit:
                usage = time_limit.get('usage', 0)
                current = time_limit.get('currentValue', 0)
                remaining = time_limit.get('remaining', 0)
                time_pct = time_limit.get('percentage', 0)
                
                draw_pie_chart(self.canvas, 110, 80, 70, time_pct, "Web/Reader/Zread Quota")
                
                info_lines.append(f"\n[Web/Reader/Zread]")
                info_lines.append(f"Used: {current} / Allowed: {usage} (Remaining: {remaining})")
            
            # 2. 5 Hours token Quota (TOKENS_LIMIT)
            if tokens_limit:
                tokens_pct = tokens_limit.get('percentage', 0)
                draw_pie_chart(self.canvas, 330, 80, 70, tokens_pct, "5 Hours token Quota")
                
                info_lines.append(f"\n[5 Hours token Quota]")
                info_lines.append(f"Percentage used: {tokens_pct}%")
                
                reset_ms = tokens_limit.get('nextResetTime', 0)
                if reset_ms:
                    self.next_reset_time_sec = reset_ms / 1000.0
            
            self.info_label.config(text="\n".join(info_lines))
        
        # Schedule the next refresh (every 30 seconds)
        self.root.after(30000, self.update_data)

if __name__ == '__main__':
    api_key = get_api_key()
    if not api_key:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('Error', 'API Key가 필요합니다. key/zai.key 파일에 API 키를 입력해주세요!')
        root.destroy()
    else:
        root = tk.Tk()
        app = QuotaApp(root, api_key)
        root.mainloop()