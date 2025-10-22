import gradio as gr
def DatePickerInput(label, value=None):
    return gr.DateTime(
            label=label,
            elem_classes=["date_picker"],
            include_time=False,
            value=value
            )