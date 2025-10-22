import requests
from settings import *
def apiClient(payload):
    # .envから取得するようなトークン関係の処理はそのうち含める予定。
    # 一旦デモ用
    try:
        response = requests.post(POST_SOURCE_URL, json=payload)
        if response.status_code == 200:
            return response.json().get("result", "レスポンスにリザルトがありません")
        else:
            return f"エラー: {response.status_code}, {response.text}"
    except Exception as e:
        return f"通信エラー: {e}"