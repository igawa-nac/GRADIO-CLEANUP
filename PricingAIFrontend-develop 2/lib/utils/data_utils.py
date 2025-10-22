import datetime
# 日付がUNIXタイムスタンプの場合はYYYY-MM-DDに変換
def to_datestr(val):
    if isinstance(val, (float, int)):
        return datetime.datetime.fromtimestamp(val).strftime("%Y-%m-%d")
    return str(val)