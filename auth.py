import requests
import json

# 🔐 ご自身の kabuステーション の API パスワードを入力してください
API_PASSWORD = "honban1985"
API_BASE_URL = "http://localhost:18080/kabusapi"

def get_token() -> str:
    """
    kabuステーションのAPIトークンを取得します。
    :return: 有効なAPIトークン（失敗時は None）
    """
    url = f"{API_BASE_URL}/token"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps({"APIPassword": API_PASSWORD})

    try:
        response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
        response.raise_for_status()
        token = response.json().get("Token")
        if not token:
            raise ValueError("トークンが取得できませんでした。")
        return token
    except Exception as e:
        print(f"[ERROR] APIトークン取得失敗: {e}", flush=True)
        return None
