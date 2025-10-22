import gradio as gr
from lib.data_processing.downloadExcel import get_selected_excel_and_df

# チェックボックス付き表を作成する関数。
def SelectableTable(data):
    if(data.empty):
        with gr.Blocks():
            gr.Markdown("エラー : データがありません。")
        return
    with gr.Blocks():
        df_input = gr.Dataframe(
            value=data,
            interactive=True,
            label="商品一覧",
            datatype=["bool", "number", "str", "number", "number"]
        )
        btn = gr.Button("選択された行を表示")
        file_output = gr.File(label="Excelダウンロードリンク")
        df_output = gr.Dataframe(label="選択された商品")

        btn.click(fn=get_selected_excel_and_df, inputs=df_input, outputs=[file_output, df_output])

