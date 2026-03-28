import time
import jwt
import requests
import json
import tkinter as tk
from tkinter import messagebox
import sys
import io
import warnings
from config import ZHIPU_API_KEY

# Ignore PyJWT InsecureKeyLengthWarning
warnings.filterwarnings('ignore', message='The HMAC key is.*')

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

def display_quota(data):
    if not data: return
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    print('=' * 50)
    print('      Z.ai Quota Info (Balance)')
    print('=' * 50)
    
    if 'data' in data and 'limits' in data['data']:
        q_data = data['data']
        print(f'Current Plan Level: {q_data.get("level", "Unknown").upper()}')
        print('-' * 50)
        
        for limit in q_data['limits']:
            l_type = limit.get('type')
            
            if l_type == 'TIME_LIMIT':
                unit = limit.get('unit', 5)
                usage = limit.get('usage', 0)
                current = limit.get('currentValue', 0)
                remaining = limit.get('remaining', 0)
                pct = limit.get('percentage', 0)
                print(f"[{unit}-Hour Usage Limit]")
                print(f"Total allowed: {usage} | Used: {current} | Remaining: {remaining}")
                print(f"Usage: {pct}%")
                
                if 'usageDetails' in limit:
                    for d in limit['usageDetails']:
                        mcode = d.get('modelCode', 'Unknown')
                        muse = d.get('usage', 0)
                        print(f"   - {mcode}: {muse} times")
            
            elif l_type == 'TOKENS_LIMIT':
                unit = limit.get('unit', 0)
                hrs = limit.get('number', 5)
                pct = limit.get('percentage', 0)
                print(f"\n[{hrs}-Hour Token Usage]")
                print(f"Percentage used: {pct}%")
            
            if 'nextResetTime' in limit:
                reset_ms = limit['nextResetTime']
                reset_sec = reset_ms / 1000.0
                reset_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_sec))
                print(f"Next Reset: {reset_time_str}")
            print('-' * 50)

    elif 'error' in data:
        print(f"Error fetching data: {data['error']}")
    else:
        print(json.dumps(data, indent=4, ensure_ascii=False))
        
    print('=' * 50)
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo('Z.ai Quota', output)
    root.destroy()

if __name__ == '__main__':
    if ZHIPU_API_KEY == 'YOUR_API_KEY_HERE':
        root = tk.Tk(); root.withdraw()
        messagebox.showerror('Error', 'Please set Zhipu API Key in config.py!')
        root.destroy()
    else:
        result = get_zhipu_usage(ZHIPU_API_KEY)
        display_quota(result)