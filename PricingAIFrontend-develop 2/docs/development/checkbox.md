# Gradioでチェックボックスを実装する手法
少し躓きやすいところがあったので、サンプルコードを載せておきます。
必要があれば参照してください。

```Python
import gradio as gr
import pandas as pd

# 初期データ
data = pd.DataFrame({
    "選択": [False, False, False],
    "名前": ["りんご", "バナナ", "オレンジ"],
    "価格": [100, 150, 120]
})

# 選択された行を抽出する関数（文字列 "true" に対応）
def filter_selected(df):
    # dfのチェックボックス値はおそらく文字列のtrue, falseで管理されている。
    # "選択"列が文字列の場合に対応
    df["選択"] = df["選択"].apply(lambda x: x == True or str(x).lower() == "true")
    selected = df[df["選択"] == True]
    return selected

with gr.Blocks() as demo:
    df_input = gr.Dataframe(
        value=data,
        interactive=True,
        label="商品一覧",
        datatype=["bool", "str", "number"]
    )
    btn = gr.Button("選択された行を表示")
    df_output = gr.Dataframe(label="選択された商品")

    btn.click(fn=filter_selected, inputs=df_input, outputs=df_output)

demo.launch()
```
## 注意点
- dfがチェックボックス値を取得する際、おそらく文字列"true", "false"でやり取りされていることに留意してほしいです。
- このコードはローカルでしか動かしていないので、databricks上では別の挙動となる可能性がなくもないことにも注意してほしいです。
- Gradioバージョン`5.33.2`で動作確認を行いました。
