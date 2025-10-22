import os
import logging
import gradio as gr
from components.layouts.MainLayout import MainLayout
from components.tables.SelectableTable import SelectableTable
from components.forms.PredictionForm import PredictionForm
from components.forms.TrainingForm import TrainingForm
from data.demodata import checkbox_demo_data

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Databricks Apps環境判定
IS_DATABRICKS_APPS = os.getenv("APP_NAME") is not None

# ポート設定: Databricks Appsでは APP_PORT が自動設定される
if IS_DATABRICKS_APPS:
    # Databricks Apps環境: 自動設定された環境変数を使用
    SERVER_NAME = "0.0.0.0"
    SERVER_PORT = int(os.getenv("APP_PORT"))  # Databricks Appsが自動設定
    logger.info(f"Running on Databricks Apps environment")
    logger.info(f"App Name: {os.getenv('APP_NAME')}")
    logger.info(f"Workspace ID: {os.getenv('DATABRICKS_WORKSPACE_ID')}")
    logger.info(f"Databricks Host: {os.getenv('DATABRICKS_HOST')}")
else:
    # ローカル開発環境: デフォルト値を使用
    SERVER_NAME = "0.0.0.0"
    SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    logger.info("Running on local development environment")

# Gradioアプリ構築
with gr.Blocks(title="PricingAI - 価格最適化システム") as demo:
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
    logger.info(f"Starting PricingAI Gradio App on {SERVER_NAME}:{SERVER_PORT}")

    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        show_error=True,
        quiet=False
    )