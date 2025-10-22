import datetime
import gradio as gr
from settings import *
from lib.api.sending import send_pre

def PredictionForm():
    gr.Markdown("## 日次売上予測")
    pred_date = gr.DateTime(
        label="予測日",
        elem_classes=["date_picker"],
        include_time=False,
        value=datetime.datetime.today()
    )
    pred_store = gr.Dropdown(
        choices=STORE_NAMES,
        label="店舗検索 (1つ選択)"
    )
    run_prediction_btn = gr.Button("実行")
    result_output = gr.Textbox(label="出力結果",lines=8, interactive=False)
    run_prediction_btn.click(
        fn=send_pre,
        inputs=[pred_store, pred_date],
        outputs=result_output
    )