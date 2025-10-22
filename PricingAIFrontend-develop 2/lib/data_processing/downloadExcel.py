# Excelにして返す関数
def export_excel(df):
    file_path = "output.xlsx"
    df.to_excel(file_path, index=False)
    return file_path

# 選択された行を抽出してExcelファイルとデータフレームを返す関数。抽出後にチェックボックス用の「選択」カラムは取り除く。
def get_selected_excel_and_df(df):
    # dfのチェックボックス値が文字列のtrue, falseで管理されているのでこのように書いている。
    df["選択"] = df["選択"].apply(lambda x: str(x).lower() == "true")
    selected = df[df["選択"] == True]
    selected_data = selected.drop(columns = ["選択"])
    file = export_excel(selected_data)
    return [file, selected_data]