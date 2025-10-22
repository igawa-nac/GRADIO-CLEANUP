import pandas as pd

demodata = {
    "store_code": [17, 27, 30],
    "store_name": ["大間々店","吉井店", "桐生境野店"],
    "price": [2, 1, 3]
}

# Checkbox用のデモデータ
checkbox_demo_data = pd.DataFrame({
    "選択": [False, False, False],
    "JAN": [4902134293421, 49021421, 49020000000421],
    "名前": ["最高牛乳 うまい牛乳", "とある畜産協会 精肉1kg", "プリン社 高級プリン"],
    "O価格": [250.22, 3000.21, 511.37],
    "最大D価格": [10, 700, 80]
})
