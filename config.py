import os
import json

AUTH_FILE_PATH = os.path.expanduser("~/.local/share/opencode/auth.json")
ZHIPU_API_KEY = None
ZAI_API_KEY = None

try:
    with open(AUTH_FILE_PATH, "r", encoding="utf-8") as f:
        auth_data = json.load(f)
        if "zhipuai-coding-plan" in auth_data:
            ZHIPU_API_KEY = auth_data["zhipuai-coding-plan"].get("key")
        if "zai-coding-plan" in auth_data:
            ZAI_API_KEY = auth_data["zai-coding-plan"].get("key")
except FileNotFoundError:
    pass

# Fallback for old compatibility if keys are not found
KEY_FILE_PATH = os.path.join(os.path.dirname(__file__), "key", "zai.key")
if not ZHIPU_API_KEY:
    try:
        with open(KEY_FILE_PATH, "r", encoding="utf-8") as f:
            ZHIPU_API_KEY = f.read().strip()
    except FileNotFoundError:
        ZHIPU_API_KEY = "YOUR_API_KEY_HERE"

