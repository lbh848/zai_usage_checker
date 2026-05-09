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

def draw_pie_chart(canvas, x, y, radius, percentage, title, font_pct=16, font_title=10):
    # background circle (gray)
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#e0e0e0", outline="")

    # slice for used percentage (orange/red)
    if percentage > 0:
        extent = -(percentage / 100.0) * 360 # Negative for clockwise
        canvas.create_arc(x - radius, y - radius, x + radius, y + radius,
                          start=90, extent=extent, fill="#ff5722", outline="")

    # Text in the middle
    canvas.create_text(x, y, text=f"{percentage}%", font=("Arial", font_pct, "bold"))
    # Title below the pie chart
    canvas.create_text(x, y + radius + 15, text=title, font=("Arial", font_title, "bold"))

class QuotaApp:
    # Base dimensions (scale=1.0)
    BASE_WIN_W = 460
    BASE_WIN_H = 560
    BASE_CANVAS_W = 460
    BASE_CANVAS_H = 150
    SCALE_MIN = 0.6
    SCALE_MAX = 1.5
    SCALE_STEP = 0.1

    def __init__(self, root, api_key):
        self.root = root
        self.api_key = api_key
        self.next_reset_times = {}  # label -> reset_time_sec
        self.next_api_request_time = 0
        self.scale = 1.0
        self.last_result = None

        self.root.title("Z.ai Quota Monitor")
        self.root.attributes("-topmost", True) # Keep window on top
        self.root.resizable(False, False)

        # +/- button frame at the top
        btn_frame = tk.Frame(root)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))
        self.btn_minus = tk.Button(btn_frame, text=" ➖ ", font=("Arial", 10, "bold"), command=self.scale_down)
        self.btn_minus.pack(side=tk.LEFT, padx=2)
        self.scale_label = tk.Label(btn_frame, text="100%", font=("Arial", 10, "bold"), width=6)
        self.scale_label.pack(side=tk.LEFT, padx=2)
        self.btn_plus = tk.Button(btn_frame, text=" ➕ ", font=("Arial", 10, "bold"), command=self.scale_up)
        self.btn_plus.pack(side=tk.LEFT, padx=2)

        self.canvas = tk.Canvas(root, width=self.BASE_CANVAS_W, height=self.BASE_CANVAS_H)
        self.canvas.pack(pady=10)

        self.info_label = tk.Label(root, text="Fetching data...", font=("Arial", 10), justify=tk.CENTER)
        self.info_label.pack(pady=10)

        self.reset_label = tk.Label(root, text="", font=("Arial", 12, "bold"), fg="red", justify=tk.CENTER)
        self.reset_label.pack(pady=5)

        self.api_countdown_label = tk.Label(root, text="", font=("Arial", 10), justify=tk.CENTER)
        self.api_countdown_label.pack(pady=5)

        self._apply_scale()

        # Start the update loops
        self.update_data()
        self.update_countdown()

    def _apply_scale(self):
        s = self.scale
        self.root.geometry(f"{int(self.BASE_WIN_W * s)}x{int(self.BASE_WIN_H * s)}")
        self.canvas.config(width=int(self.BASE_CANVAS_W * s), height=int(self.BASE_CANVAS_H * s))
        pct_font = max(8, int(16 * s))
        title_font = max(6, int(10 * s))
        info_font = max(6, int(10 * s))
        reset_font = max(7, int(12 * s))
        countdown_font = max(6, int(10 * s))
        self.info_label.config(font=("Arial", info_font))
        self.reset_label.config(font=("Arial", reset_font))
        self.api_countdown_label.config(font=("Arial", countdown_font))
        self.scale_label.config(text=f"{int(s * 100)}%")
        # Redraw pie charts if data exists
        if self.last_result:
            self._draw_charts(self.last_result)

    def scale_up(self):
        new = round(min(self.scale + self.SCALE_STEP, self.SCALE_MAX), 1)
        if new != self.scale:
            self.scale = new
            self._apply_scale()

    def scale_down(self):
        new = round(max(self.scale - self.SCALE_STEP, self.SCALE_MIN), 1)
        if new != self.scale:
            self.scale = new
            self._apply_scale()

    def _limit_label(self, limit):
        t = limit.get('type', '')
        if t == 'TIME_LIMIT':
            return 'Search Quota'
        unit = limit.get('unit', 0)
        number = limit.get('number', 0)
        if unit == 3:
            return f'{number}H Token'
        if unit == 6:
            return 'Weekly Token'
        return f'Token ({number}/{unit})'

    def _draw_charts(self, result):
        s = self.scale
        self.canvas.delete("all")

        if 'data' not in result or 'limits' not in result['data']:
            return

        limits = result['data']['limits']
        n = len(limits)
        if n == 0:
            return

        r = int(45 * s)
        canvas_w = int(self.BASE_CANVAS_W * s)
        spacing = canvas_w / n
        cy = int(65 * s)
        fp = max(8, int(16 * s))
        ft = max(6, int(10 * s))

        for i, limit in enumerate(limits):
            cx = int(spacing * (i + 0.5))
            label = self._limit_label(limit)
            draw_pie_chart(self.canvas, cx, cy, r, limit.get('percentage', 0), label, fp, ft)
            if i < n - 1:
                div_x = int(spacing * (i + 1))
                self.canvas.create_line(div_x, int(10 * s), div_x, int(130 * s), fill="#cccccc", width=1, dash=(4, 4))
        
    def update_countdown(self):
        # API request countdown
        api_diff = int(self.next_api_request_time - time.time())
        if api_diff > 0:
            self.api_countdown_label.config(text=f"다음 API 요청까지: {api_diff}초")
        else:
            self.api_countdown_label.config(text="API 요청 중...")

        if self.next_reset_times:
            lines = []
            for label, reset_sec in self.next_reset_times.items():
                diff = int(reset_sec - time.time())
                if diff > 0:
                    hours = diff // 3600
                    minutes = (diff % 3600) // 60
                    seconds = diff % 60
                    lines.append(f"{label} Reset: {hours}h {minutes}m {seconds}s")
                else:
                    lines.append(f"{label}: Resetting!")
            self.reset_label.config(text="\n".join(lines))

        # Schedule the next tick in 1 second
        self.root.after(1000, self.update_countdown)
        
    def update_data(self):
        self.next_api_request_time = time.time() + 30
        result = get_zhipu_usage(self.api_key)
        self.last_result = result

        if 'error' in result:
            self.info_label.config(text=f"Error: {result['error']}")
        elif 'data' in result and 'limits' in result['data']:
            q_data = result['data']
            level = q_data.get("level", "Unknown").upper()
            limits = q_data['limits']

            self._draw_charts(result)

            info_lines = [f"Plan: {level}"]
            self.next_reset_times = {}

            # TIME_LIMIT
            time_limit = next((l for l in limits if l.get('type') == 'TIME_LIMIT'), None)
            if time_limit:
                usage = time_limit.get('usage', 0)
                current = time_limit.get('currentValue', 0)
                remaining = time_limit.get('remaining', 0)
                info_lines.append(f"\n[Search / Reader / Zread]")
                info_lines.append(f"Used: {current} / Allowed: {usage} (Remaining: {remaining})")

            # All TOKENS_LIMIT entries
            tokens_limits = [l for l in limits if l.get('type') == 'TOKENS_LIMIT']
            for tl in tokens_limits:
                label = self._limit_label(tl)
                pct = tl.get('percentage', 0)
                info_lines.append(f"\n[{label}]")
                info_lines.append(f"Percentage used: {pct}%")
                reset_ms = tl.get('nextResetTime', 0)
                if reset_ms:
                    self.next_reset_times[label] = reset_ms / 1000.0

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