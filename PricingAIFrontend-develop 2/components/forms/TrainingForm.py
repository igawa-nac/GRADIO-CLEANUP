import gradio as gr
from components.inputs.DatePickerInput import DatePickerInput
from lib.api.sending import send_data
from settings import *

def TrainingForm():
    # training
    gr.Markdown("## データ取得条件")
    
    start_date = DatePickerInput(label="取得開始日")
    end_date = DatePickerInput(label="取得最終日")
    
    with gr.Row():
        source_stores = gr.Dropdown(
            choices=STORE_NAMES,
            label="店舗検索 (複数選択可)",
            multiselect=True
            )
        clear_btn = gr.Button("クリア", scale=0)
        clear_btn.click(lambda: [], None, source_stores)

    run_train_btn = gr.Button("学習開始")
    train_start_output = gr.Textbox(label="確認画面",lines=4,interactive=False)
    run_train_btn.click(
        fn=send_data,
        inputs=[source_stores, start_date, end_date],
        outputs=train_start_output
    )