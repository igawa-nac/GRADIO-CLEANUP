# databricks JobsとGradioのAPI接続について
フィールド操作等はまだですが、接続とタスクの実行開始、実行状況取得、結果`dbutils.notebook.exit(f"Jobs側にこれを書く。")`の取得ができたので、軽くまとめます。
なお、急ぎで書いた感じですので、雑になっていると思います。

## Jobsの登録
Jobsを登録しておく。

## フロントエンドのコード
るきあ君のコードを一部流用。API関連に関わるところは---とかで囲んだつもり。

```python
import gradio as gr
import pandas as pd
import datetime
import requests
import os
from dotenv import load_dotenv
from data.demodata import demodata

# URLや機密情報を受け取る。
load_dotenv("config.env")
load_dotenv(".env_local")
load_dotenv(".env")

# URLとトークンを設定。トークンはdatabricksの設定画面から入手できる。
# トークンは機密情報のため扱いに注意。
# (特にAIに読み込ませないように。不安なら有効期間を短く設定するとよい。)
post_source_url = os.getenv("POST_SOURCE_URL")
get_progress_url = os.getenv("GET_PROGRESS_URL")
get_result_url = os.getenv("GET_RESULT_URL")
access_token = os.getenv("ACCESS_TOKEN")

# 今回のデモではJobsの開始で受け取ったrun_idを手動でここに設定&再起動している。
# 本番ではもちろん自動で行う必要がある。
RUN_ID = 687283416244517

# ------------------------- 設定・UI関連 -------------------------
# 初期値
df_stores = pd.DataFrame()
store_names = ["ファイル読み込みエラー"]
loading_error = False

# データ参照
try:
    df_stores = pd.DataFrame(demodata)
    store_names = df_stores['store_name'].tolist()
except Exception as e:
    loading_error = True
    df_stores = pd.DataFrame()
    error_str = f"エラーが発生しました: {e}"
    store_names = []

# 日付がUNIXタイムスタンプの場合はYYYY-MM-DDに変換
def to_datestr(val):
    if isinstance(val, (float, int)):
        return datetime.datetime.fromtimestamp(val).strftime("%Y-%m-%d")
    return str(val)


# ------------------------- ここからJobs API関連 -------------------------
# 学習を開始させる。
def send_train_start(selected_stores, start_date, end_date):
    if not selected_stores or not start_date or not end_date:
        return "店舗・期間をすべて選択してください。"

    # フィールド周りは未実装なので注意。なおJobsのほうでは設定した。
    start_str = to_datestr(start_date)
    end_str = to_datestr(end_date)
    codes = df_stores.loc[df_stores["store_name"].isin(selected_stores), "store_code"].tolist()
    codes_str = [str(code) for code in codes]

    # jsonでJobのIDを指定する。この値はdatabricksのJobs関係のページから取得できる。
    payload = {
        "job_id": 933047963643733
    }
    print("access token len ", len(access_token))
    
    try:
        # ヘッダーには認証周りを設定する。    
        headers = {
            "Authorization": f"Bearer {access_token}",  # アクセストークンをここに入れる
            "Content-Type": "application/json"
        }

        # リンクとヘッダとjsonを入れて送ることができる。
        response = requests.post(post_source_url,headers=headers, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("run_id"):
                # run_idを返される。なお、ここでの変数代入はあまり意味なさそう。
                RUN_ID = res_json.get("run_id")
            return RUN_ID
        else:
            return f"エラー: {response.status_code}, {response.text}"
    except Exception as e:
        return f"通信エラー: {e}"

# 学習Job進行状況の確認
def get_train_status():
    # run_idで指定する。
    payload = {
        "run_id": RUN_ID
    }
    print("access token len ", len(access_token))
    try:   
        headers = {
            "Authorization": f"Bearer {access_token}",  # アクセストークンをここに入れる
            "Content-Type": "application/json"
        }
        # さっきはPOSTだったが今回はGET
        response = requests.get(get_progress_url,headers=headers, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            state = res_json.get("state", {})
            tasks = res_json.get("tasks", {})
            # こうすればJobsの進行ステータスを受け取れる。
            life_cycle_state = state.get("life_cycle_state")
            task_run_id = tasks[0].get("run_id", "waiting") #ここは一旦考慮必要かも
            return f"{life_cycle_state} {task_run_id}←waitingでなければTASK_RUN_IDに左の数字列を指定"
        else:
            return f"エラー: {response.status_code}, {response.text}"
    except Exception as e:
        return f"通信エラー: {e}"
    
TASK_RUN_ID= 59999475160762
def get_Jobs_output():
    # run_idで指定する。
    payload = {
        "run_id": TASK_RUN_ID
    }
    print("access token len ", len(access_token))
    try:   
        headers = {
            "Authorization": f"Bearer {access_token}",  # アクセストークンをここに入れる
        }
        # GETのため注意。
        response = requests.get(get_result_url,headers=headers, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            result = res_json.get("notebook_output", {}).get("result", None)
            return result
        else:
            return f"エラー: {response.status_code}, {response.text}"
    except Exception as e:
        return f"通信エラー: {e}"

# -----------------------------------------------------------------------------

with gr.Blocks(css="""
.gradio-container {
    max-width: 60vw !important;
    width: 60vw !important;
    margin: 0 auto !important;
}

.main {
    max-width: 60vw !important;
    width: 60vw !important;
    margin: 0 auto !important;
}

.container {
    max-width: 60vw !important;
    width: 60vw !important;
    margin: 0 auto !important;
}

/* 全体的なスタイル調整 */
body {
    display: flex !important;
    justify-content: center !important;
}

/* メインUIブロック */
#main-ui-block {
    width: 100% !important;
    max-width: 100% !important;
    margin: 32px auto !important;
    box-sizing: border-box;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 16px #0001;
    padding: 24px 16px;
    display: flex;
    flex-direction: column;
    align-items: stretch;
}

/* 内部コンポーネント（テキスト、ドロップダウン、日付ピッカー） */
input, select, textarea, .date_picker {
    width: 100%;                  /* 横幅いっぱい */
    box-sizing: border-box;
}
""", elem_id="main-ui-block") as demo:
    gr.Markdown("# AI予測ツール")
    if loading_error:
        gr.Markdown(error_str)
   
    gr.Markdown("## データ取得条件")
    start_date = gr.DateTime(
        label="取得開始日",
        elem_classes=["date_picker"],
        include_time=False
    )
    end_date = gr.DateTime(
        label="取得最終日",
        elem_classes=["date_picker"],
        include_time=False
    )
    with gr.Row():
        source_stores = gr.Dropdown(
            choices=store_names,
            label="店舗検索 (複数選択可)",
            multiselect=True
            )
        clear_btn = gr.Button("クリア", scale=0)
        clear_btn.click(lambda: [], None, source_stores)

    run_train_btn = gr.Button("学習開始")
    output1 = gr.Textbox(label="確認画面",lines=4,interactive=False)
    run_train_btn.click(
        fn=send_train_start,
        inputs=[source_stores, start_date, end_date],
        outputs=output1
    )

    gr.Markdown("## 学習結果")
    run_prediction_btn = gr.Button("実行")
    output2 = gr.Textbox(label="出力結果",lines=8, interactive=False)
    run_prediction_btn.click(
        fn=get_train_status,
        outputs=output2
    )
    run_prediction_btn = gr.Button("実行2")
    output3 = gr.Textbox(label="出力結果",lines=8, interactive=False)
    run_prediction_btn.click(
        fn=get_Jobs_output,
        outputs=output3
    )

if __name__ == "__main__":
    demo.launch()

```

