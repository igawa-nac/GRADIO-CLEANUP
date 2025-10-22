from components.layouts.MainLayout import MainLayout
from components.tables.SelectableTable import SelectableTable
from components.forms.PredictionForm import PredictionForm
from components.forms.TrainingForm import TrainingForm
from data.demodata import checkbox_demo_data
import gradio as gr

with gr.Blocks() as demo:
    MainLayout(
        [
            {
                "name" : "学習の開始！",
                "component" : TrainingForm
            },
            {
                "name" : "予測の開始！",
                "component" : PredictionForm
            },
            {
                "name" : "予測結果の取得",
                "component" : SelectableTable,
                "args" : [checkbox_demo_data]
            },
        ]
    )

if __name__ == "__main__":
    demo.launch()