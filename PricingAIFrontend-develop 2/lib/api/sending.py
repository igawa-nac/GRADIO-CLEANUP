from settings import *
from lib.utils.data_utils import to_datestr
from lib.api.apiClient import apiClient


# 学習データ選択の関数
def send_data(selected_stores, start_date, end_date):
    if not selected_stores or not start_date or not end_date:
        return "店舗・期間.をすべて選択してください。"

    start_date_str = to_datestr(start_date)
    end_date_str = to_datestr(end_date)
    # 下２行    list(store_name) => list(str(store_code))
    store_codes = DF_STORES.loc[DF_STORES["store_name"].isin(selected_stores), "store_code"].tolist()
    store_codes_str = [str(code) for code in store_codes]

    payload = {
        "codes": store_codes_str,
        "date1": start_date_str,
        "date2": end_date_str
    }
    
    apiClient(payload=payload)


# 予測条件選択の関数
def send_pre(pred_store_name, pred_date):
    if not pred_store_name or not pred_date:
        return "店舗名と予測日を両方選択してください"
    pred_date_str = to_datestr(pred_date)
    store_code_str = str(DF_STORES.loc[DF_STORES["store_name"] == pred_store_name, "store_code"].iat[0])

    payload = {
        "name": pred_store_name,
        "code": store_code_str,
        "date": pred_date_str,
        "price": store_code_str
    }

    apiClient(payload=payload)