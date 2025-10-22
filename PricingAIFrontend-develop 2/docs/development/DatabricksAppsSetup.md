# Databricks Apps セットアップガイド - Gradio UI

## 概要
このドキュメントでは、Azure DatabricksのDatabricks Appsを使用してGradio UIをデプロイするための詳細な手順を説明します。

## 前提条件

### 必要な権限
- [ ] Azure Databricks Workspaceへのアクセス権
- [ ] Apps作成権限 (Workspace Admin または Apps Creator)
- [ ] Databricks Jobs実行権限
- [ ] Secret Scope作成権限

### 必要なリソース
- [ ] Azure Databricks Workspace (Premium または Enterprise tier)
- [ ] Databricks Runtime 13.3 LTS 以上
- [ ] GitHub リポジトリへのアクセス

## 1. Databricks Apps の作成

### 1.1 App の初期作成

#### UI から作成
1. Databricks Workspace にログイン
2. 左サイドバーから **Apps** をクリック
3. **Create App** をクリック
4. 以下の情報を入力:

```
App Name: pricing-ai-frontend-production
Description: PricingAI Gradio UI - 本番環境
Source: Git Repository
Repository URL: https://github.com/your-org/GRADIO-CLEANUP.git
Branch: main
Path: PricingAIFrontend-develop 2
```

#### CLI から作成
```bash
# Databricks CLI のインストール
pip install databricks-cli

# 認証設定
databricks configure --token

# App 作成
databricks apps create \
  --app-name pricing-ai-frontend-production \
  --git-url https://github.com/your-org/GRADIO-CLEANUP.git \
  --git-branch main \
  --git-path "PricingAIFrontend-develop 2" \
  --description "PricingAI Gradio UI - 本番環境"
```

### 1.2 App 設定ファイルの作成

Databricks Apps は `app.yaml` で設定を管理します。

```yaml
# PricingAIFrontend-develop 2/app.yaml
name: pricing-ai-frontend
version: 1.0.0

# エントリーポイント
command:
  - python
  - app.py

# 環境変数
env:
  # Gradio 設定
  GRADIO_SERVER_NAME: "0.0.0.0"
  GRADIO_SERVER_PORT: "8080"
  GRADIO_ANALYTICS_ENABLED: "False"

  # アプリケーション設定
  PYTHONPATH: "/workspace/PricingAIFrontend-develop 2"

# リソース設定
resources:
  driver:
    memory: "4g"
    cores: 2

# 依存関係
dependencies:
  python:
    requirements: requirements.txt

# ヘルスチェック
health_check:
  path: /
  interval: 30
  timeout: 10
  retries: 3

# ポート公開
ports:
  - port: 8080
    protocol: http
```

### 1.3 app.py の修正 (Databricks Apps 対応)

```python
# app.py
from components.layouts.MainLayout import MainLayout
from components.tables.SelectableTable import SelectableTable
from components.forms.PredictionForm import PredictionForm
from components.forms.TrainingForm import TrainingForm
from data.demodata import checkbox_demo_data
import gradio as gr
import os

# Databricks Apps 環境変数
SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "8080"))

with gr.Blocks() as demo:
    MainLayout(
        [
            {
                "name" : "学習の開始!",
                "component" : TrainingForm
            },
            {
                "name" : "予測の開始!",
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
    # Databricks Apps 用の設定
    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        show_error=True,
        quiet=False
    )
```

## 2. シークレット管理

### 2.1 Secret Scope の作成

#### UI から作成
1. Workspace Settings > Developer > Secret Scopes
2. **Create Secret Scope** をクリック
3. 以下の情報を入力:

```
Scope Name: pricing-ai-secrets
Manage Principal: Creator
```

#### CLI から作成
```bash
databricks secrets create-scope \
  --scope pricing-ai-secrets \
  --scope-backend-type DATABRICKS
```

### 2.2 Secret の登録

```bash
# Databricks アクセストークン
databricks secrets put-secret \
  --scope pricing-ai-secrets \
  --key databricks-token

# API エンドポイント
databricks secrets put-secret \
  --scope pricing-ai-secrets \
  --key post-source-url

databricks secrets put-secret \
  --scope pricing-ai-secrets \
  --key get-progress-url

databricks secrets put-secret \
  --scope pricing-ai-secrets \
  --key post-pred-url
```

### 2.3 アプリからシークレットを参照

```python
# settings.py
import os
from dotenv import load_dotenv

# ローカル開発用の .env ファイル読み込み
load_dotenv("config/config.env")
load_dotenv(".env")
load_dotenv(".env_local")

# Databricks Apps 環境では、シークレットは環境変数として自動注入される
# 注: Databricks Apps の設定でシークレットスコープを指定する必要がある

def get_secret(key: str, default: str = None) -> str:
    """
    環境変数またはDatabricksシークレットから値を取得

    Parameters:
    -----------
    key : str
        シークレットキー
    default : str, optional
        デフォルト値

    Returns:
    --------
    str
        シークレット値
    """
    # 1. 環境変数から取得を試行
    value = os.getenv(key)

    if value is None and default is not None:
        value = default

    return value

# API エンドポイント
POST_SOURCE_URL = get_secret("POST_SOURCE_URL")
GET_PROGRESS_URL = get_secret("GET_PROGRESS_URL")
POST_PRED_URL = get_secret("POST_PRED_URL")
GET_RESULT_URL = get_secret("GET_RESULT_URL")

# アクセストークン
ACCESS_TOKEN = get_secret("DATABRICKS_TOKEN")
```

### 2.4 App 設定でシークレットを注入

```yaml
# app.yaml に追加
secrets:
  - scope: pricing-ai-secrets
    key: databricks-token
    env_var: DATABRICKS_TOKEN

  - scope: pricing-ai-secrets
    key: post-source-url
    env_var: POST_SOURCE_URL

  - scope: pricing-ai-secrets
    key: get-progress-url
    env_var: GET_PROGRESS_URL

  - scope: pricing-ai-secrets
    key: post-pred-url
    env_var: POST_PRED_URL

  - scope: pricing-ai-secrets
    key: get-result-url
    env_var: GET_RESULT_URL
```

## 3. Databricks Jobs との統合

### 3.1 トレーニングジョブの作成

#### UI から作成
1. Workflows > Jobs > Create Job
2. 以下の設定:

```
Job Name: PricingAI-Training
Task Name: train-model
Type: Notebook
Notebook Path: /Workspace/Users/{user}/PricingAI_Spark-main/TrainingNotebook
Cluster: Existing All-Purpose Cluster または New Job Cluster

Parameters:
- case_period_start: (動的に設定)
- case_period_end: (動的に設定)
- stores: (動的に設定)
- output_zero: /dbfs/mnt/models/pricing_ai/model_zero
- output_up: /dbfs/mnt/models/pricing_ai/model_up
- verbose: true
```

#### JSON 定義
```json
{
  "name": "PricingAI-Training",
  "tasks": [
    {
      "task_key": "train-model",
      "notebook_task": {
        "notebook_path": "/Workspace/Users/{user}/PricingAI_Spark-main/TrainingNotebook",
        "base_parameters": {
          "case_period_start": "",
          "case_period_end": "",
          "stores": "",
          "output_zero": "/dbfs/mnt/models/pricing_ai/model_zero",
          "output_up": "/dbfs/mnt/models/pricing_ai/model_up",
          "verbose": "true"
        }
      },
      "new_cluster": {
        "spark_version": "13.3.x-scala2.12",
        "node_type_id": "Standard_DS3_v2",
        "num_workers": 2
      }
    }
  ]
}
```

### 3.2 トレーニング Notebook の作成

```python
# Databricks Notebook: TrainingNotebook.py

# COMMAND ----------
# パラメータウィジェットの作成
dbutils.widgets.text("case_period_start", "")
dbutils.widgets.text("case_period_end", "")
dbutils.widgets.text("stores", "")
dbutils.widgets.text("output_zero", "")
dbutils.widgets.text("output_up", "")
dbutils.widgets.text("verbose", "false")

# COMMAND ----------
# パラメータの取得
case_period_start = dbutils.widgets.get("case_period_start")
case_period_end = dbutils.widgets.get("case_period_end")
stores_str = dbutils.widgets.get("stores")
output_zero = dbutils.widgets.get("output_zero")
output_up = dbutils.widgets.get("output_up")
verbose = dbutils.widgets.get("verbose") == "true"

# COMMAND ----------
# パラメータ変換
case_period = (case_period_start, case_period_end)
stores = stores_str.split(",")

print(f"学習期間: {case_period}")
print(f"対象店舗: {stores}")
print(f"出力パス (Zero): {output_zero}")
print(f"出力パス (Up): {output_up}")

# COMMAND ----------
# ML関数の読み込み
%run ./Sp_interface

# COMMAND ----------
# モデルトレーニング実行
import time
import json

start_time = time.time()

try:
    train_model(
        case_period=case_period,
        stores=stores,
        output_zero=output_zero,
        output_up=output_up,
        verbose=verbose
    )

    elapsed_time = time.time() - start_time

    result = {
        "status": "success",
        "message": "モデルトレーニングが完了しました",
        "elapsed_time": elapsed_time,
        "model_paths": {
            "zero": output_zero,
            "up": output_up
        },
        "parameters": {
            "case_period": case_period,
            "stores": stores
        }
    }

    print("=== トレーニング完了 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Gradioに返す結果
    dbutils.notebook.exit(json.dumps(result, ensure_ascii=False))

except Exception as e:
    error_result = {
        "status": "error",
        "message": str(e),
        "error_type": type(e).__name__
    }

    print("=== トレーニングエラー ===")
    print(json.dumps(error_result, indent=2, ensure_ascii=False))

    # エラーを返す
    dbutils.notebook.exit(json.dumps(error_result, ensure_ascii=False))

# COMMAND ----------
```

### 3.3 予測ジョブの作成

同様に、予測ジョブも作成します。

```json
{
  "name": "PricingAI-Prediction",
  "tasks": [
    {
      "task_key": "predict-result",
      "notebook_task": {
        "notebook_path": "/Workspace/Users/{user}/PricingAI_Spark-main/PredictionNotebook",
        "base_parameters": {
          "store_cd": "",
          "upday": "",
          "model_zero": "/dbfs/mnt/models/pricing_ai/model_zero",
          "model_up": "/dbfs/mnt/models/pricing_ai/model_up",
          "item_file": "",
          "drop_file": "",
          "verbose": "true"
        }
      },
      "new_cluster": {
        "spark_version": "13.3.x-scala2.12",
        "node_type_id": "Standard_DS3_v2",
        "num_workers": 2
      }
    }
  ]
}
```

## 4. ネットワーク設定

### 4.1 アプリのアクセス制御

```yaml
# app.yaml に追加
access_control:
  # 認証要求
  authentication:
    enabled: true
    provider: databricks

  # IP制限 (オプション)
  ip_whitelist:
    - "192.168.1.0/24"    # 社内ネットワーク
    - "10.0.0.0/8"        # VPN

  # ユーザー/グループ制限
  allowed_users:
    - user1@company.com
    - user2@company.com

  allowed_groups:
    - pricing-ai-users
    - data-scientists
```

### 4.2 CORS 設定 (必要な場合)

```python
# app.py に追加
import gradio as gr

demo = gr.Blocks()

# CORS 設定
demo.launch(
    server_name="0.0.0.0",
    server_port=8080,
    allowed_paths=["/api/*"],  # API エンドポイント
    root_path="/",             # ルートパス
    share=False
)
```

## 5. モニタリングとログ

### 5.1 アプリケーションログ

Databricks Apps は標準出力/エラー出力を自動的に収集します。

```python
# lib/utils/logging_config.py
import logging
import sys

def setup_logging(level=logging.INFO):
    """
    ロギング設定

    Parameters:
    -----------
    level : int
        ログレベル
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # 標準出力に出力
        ]
    )

    # Databricks Apps では標準出力がログとして収集される
    logger = logging.getLogger(__name__)
    logger.info("Logging configured for Databricks Apps")

    return logger
```

```python
# app.py で使用
from lib.utils.logging_config import setup_logging

logger = setup_logging()

if __name__ == "__main__":
    logger.info("Starting PricingAI Gradio App")
    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        show_error=True,
        quiet=False
    )
```

### 5.2 ログの確認

#### UI から確認
1. Apps > [App名] > Logs
2. フィルタリングオプション:
   - Time Range
   - Log Level
   - Search Text

#### CLI から確認
```bash
# 最新のログを取得
databricks apps logs --app-name pricing-ai-frontend-production --tail 100

# ログをリアルタイムで監視
databricks apps logs --app-name pricing-ai-frontend-production --follow
```

### 5.3 メトリクス収集

```python
# lib/utils/metrics.py
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def track_execution_time(func):
    """関数の実行時間を追跡"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time

        logger.info(
            f"Function {func.__name__} executed in {elapsed_time:.2f} seconds"
        )

        return result
    return wrapper

# 使用例
@track_execution_time
def send_train_start(selected_stores, start_date, end_date):
    # ... 処理 ...
    pass
```

## 6. デプロイメント

### 6.1 手動デプロイ

#### UI から
1. Apps > [App名] > Deploy
2. Branch / Commit を選択
3. **Deploy** をクリック

#### CLI から
```bash
# 特定のブランチをデプロイ
databricks apps deploy \
  --app-name pricing-ai-frontend-production \
  --git-branch main

# 特定のコミットをデプロイ
databricks apps deploy \
  --app-name pricing-ai-frontend-production \
  --git-commit abc123def456
```

### 6.2 自動デプロイ (CI/CD)

```yaml
# .github/workflows/deploy-databricks-apps.yml
name: Deploy to Databricks Apps

on:
  push:
    branches:
      - main
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Databricks CLI
        run: |
          pip install databricks-cli

      - name: Configure Databricks CLI
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          echo "[DEFAULT]" > ~/.databrickscfg
          echo "host = $DATABRICKS_HOST" >> ~/.databrickscfg
          echo "token = $DATABRICKS_TOKEN" >> ~/.databrickscfg

      - name: Determine environment
        id: env
        run: |
          if [ "${{ github.ref }}" == "refs/heads/main" ]; then
            echo "app_name=pricing-ai-frontend-production" >> $GITHUB_OUTPUT
            echo "environment=production" >> $GITHUB_OUTPUT
          else
            echo "app_name=pricing-ai-frontend-development" >> $GITHUB_OUTPUT
            echo "environment=development" >> $GITHUB_OUTPUT
          fi

      - name: Deploy to Databricks Apps
        run: |
          databricks apps deploy \
            --app-name ${{ steps.env.outputs.app_name }} \
            --git-branch ${{ github.ref_name }}

      - name: Verify deployment
        run: |
          databricks apps get --app-name ${{ steps.env.outputs.app_name }}

      - name: Notify deployment
        if: success()
        run: |
          echo "Deployment to ${{ steps.env.outputs.environment }} successful!"
```

### 6.3 ロールバック

```bash
# 以前のバージョンにロールバック
databricks apps deploy \
  --app-name pricing-ai-frontend-production \
  --git-commit <previous-commit-hash>

# または、以前のリリースタグにロールバック
databricks apps deploy \
  --app-name pricing-ai-frontend-production \
  --git-tag v1.0.0
```

## 7. パフォーマンス最適化

### 7.1 リソース設定の調整

```yaml
# app.yaml
resources:
  driver:
    memory: "8g"      # メモリ増量
    cores: 4          # CPU コア増量

  # Auto-scaling 設定
  autoscaling:
    enabled: true
    min_workers: 1
    max_workers: 5
```

### 7.2 キャッシング

```python
# lib/utils/cache.py
from functools import lru_cache
import pandas as pd

@lru_cache(maxsize=128)
def load_store_data():
    """店舗データをキャッシュ"""
    # データ読み込み処理
    return pd.DataFrame()

# 使用例
df_stores = load_store_data()
```

### 7.3 レスポンス最適化

```python
# components/forms/TrainingForm.py
import gradio as gr
from lib.api.apiClient import apiClient

def send_train_start_async(selected_stores, start_date, end_date):
    """
    非同期でトレーニングを開始

    すぐにレスポンスを返し、バックグラウンドで処理
    """
    # パラメータ検証
    if not selected_stores or not start_date or not end_date:
        return "エラー: すべてのフィールドを入力してください"

    # ジョブを非同期で開始
    try:
        response = apiClient({
            "case_period_start": start_date,
            "case_period_end": end_date,
            "stores": ",".join(selected_stores)
        })

        run_id = response.get("run_id")

        return f"トレーニングジョブを開始しました。Run ID: {run_id}"

    except Exception as e:
        return f"エラー: {str(e)}"
```

## 8. トラブルシューティング

### 8.1 よくある問題

#### 問題 1: アプリが起動しない
```
エラー: ModuleNotFoundError: No module named 'gradio'

解決策:
1. requirements.txt に gradio が記載されているか確認
2. app.yaml で requirements.txt が指定されているか確認
```

#### 問題 2: シークレットが読み込めない
```
エラー: KeyError: 'DATABRICKS_TOKEN'

解決策:
1. Secret Scope が正しく作成されているか確認
2. app.yaml でシークレットが正しくマッピングされているか確認
3. App に Secret Scope へのアクセス権があるか確認
```

#### 問題 3: Jobs API にアクセスできない
```
エラー: 403 Forbidden

解決策:
1. アクセストークンが有効か確認
2. トークンに Jobs 実行権限があるか確認
3. IP制限に引っかかっていないか確認
```

### 8.2 デバッグモード

```python
# app.py
import os

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if __name__ == "__main__":
    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        show_error=DEBUG,  # デバッグモードではエラー詳細を表示
        debug=DEBUG
    )
```

```yaml
# app.yaml (開発環境)
env:
  DEBUG: "true"
```

## 9. セキュリティベストプラクティス

### 9.1 アクセストークンの管理
- [ ] トークンは必ず Secret Scope に保存
- [ ] トークンの有効期限を設定 (推奨: 90日)
- [ ] 定期的なトークンローテーション
- [ ] コードにトークンをハードコードしない

### 9.2 入力バリデーション
```python
# lib/utils/validation.py
import re
from datetime import datetime

def validate_date(date_str: str) -> bool:
    """日付フォーマットを検証"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_store_code(store_code: str) -> bool:
    """店舗コードを検証"""
    # 店舗コードは3桁の数字
    pattern = r'^\d{3}$'
    return bool(re.match(pattern, store_code))

def sanitize_input(input_str: str) -> str:
    """入力をサニタイズ"""
    # SQLインジェクション対策など
    return input_str.strip()
```

### 9.3 API レート制限
```python
# lib/utils/rate_limiter.py
import time
from functools import wraps

class RateLimiter:
    """APIレート制限"""

    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()

            # 古い呼び出しを削除
            self.calls = [
                call_time for call_time in self.calls
                if now - call_time < self.period
            ]

            if len(self.calls) >= self.max_calls:
                raise Exception(
                    f"レート制限超過: {self.max_calls}回/{self.period}秒"
                )

            self.calls.append(now)
            return func(*args, **kwargs)

        return wrapper

# 使用例
rate_limiter = RateLimiter(max_calls=10, period=60)

@rate_limiter
def send_api_request():
    # API リクエスト処理
    pass
```

## 10. まとめ

Databricks Apps でGradio UIを成功裏にデプロイするために:

1. **app.yaml の適切な設定**: リソース、シークレット、ネットワーク
2. **シークレット管理**: Secret Scope の活用
3. **Databricks Jobs 統合**: Notebook によるML パイプライン実行
4. **モニタリング**: ログとメトリクスの収集
5. **CI/CD**: 自動デプロイメントパイプライン
6. **セキュリティ**: 入力バリデーション、アクセス制御

このガイドに従い、安全で効率的なDatabricks Apps環境を構築してください。
