import gradio as gr
# Tabの中身を受け取るイメージ。
# children : {name, component, [args]}
def MainLayout(children : list[dict[str, callable, list[any]]]):
    # あくまでコンポーネントとみなしているので、launchなどはapp.pyへの配置としています。
    with gr.Blocks():
        for child in children:
            with gr.Tab(child["name"]):
                if "args" in child:
                    child["component"](*child["args"])
                else:
                    child["component"]()
