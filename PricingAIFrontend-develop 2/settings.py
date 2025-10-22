import pandas as pd
import os
from dotenv import load_dotenv
from data.demodata import demodata

load_dotenv("config/config.env")
load_dotenv(".env")
load_dotenv(".env_local")

POST_SOURCE_URL = os.getenv("POST_SOURCE_URL")
GET_PROGRESS_URL = os.getenv("GET_PROGRESS_URL")
POST_PRED_URL = os.getenv("POST_PRED_URL")

# 初期値
DF_STORES = pd.DataFrame()
STORE_NAMES = []
LOADING_ERROR = False
ERROR_STR = f"エラーが発生しました"

# データ参照
try:
    DF_STORES = pd.DataFrame(demodata)
    STORE_NAMES = DF_STORES['store_name'].tolist()
except Exception as e:
    DF_STORES = pd.DataFrame()
    STORE_NAMES = ["ファイル読み込みエラー"]
    LOADING_ERROR = True
    ERROR_STR = f"エラーが発生しました: {e}"