# Databricks Apps 実装計画 - 既存UI開発者向け

## 📊 現状評価

### ✅ 既に完了している部分
- [x] Gradio UIの基本実装 (TrainingForm, PredictionForm, SelectableTable)
- [x] コンポーネント構造 (components/, lib/, data/)
- [x] 基本的なAPI通信機能 (apiClient.py)
- [x] 設定管理 (settings.py)
- [x] データ処理ユーティリティ

### ❌ 未実装・不完全な部分
- [ ] Databricks Apps設定ファイル (app.yaml)
- [ ] 環境変数設定 (.env, .env.example)
- [ ] Databricks Jobs API完全統合
- [ ] Databricks Notebookの作成
- [ ] CI/CDパイプライン
- [ ] Secret Scope設定
- [ ] テストコード
- [ ] ロギング・モニタリング機能

## 🎯 実装計画の全体像

```
Phase 1: ローカル環境整備 (1-2日)
  └─> Phase 2: Databricks統合準備 (2-3日)
       └─> Phase 3: Databricks Apps デプロイ (3-5日)
            └─> Phase 4: 本番統合とテスト (5-7日)
                 └─> Phase 5: 本番リリース (1日)
```

## 📅 Phase 1: ローカル環境整備 (1-2日)

### 目標
既存のUIコードをDatabricks Apps対応に準備し、ローカルで動作確認できる状態にする

### タスク

#### 1.1 環境変数設定ファイルの作成 ⭐ **最優先**

**所要時間**: 1時間

**作成ファイル**:
```bash
PricingAIFrontend-develop 2/
├── .env.example          # テンプレート（Git管理対象）
├── .env.local.example    # ローカル開発用テンプレート
└── config/
    └── config.env        # 共通設定（非機密情報のみ）
```

**実装内容**:
```bash
# .env.example
# Databricks API エンドポイント
POST_SOURCE_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/run-now
GET_PROGRESS_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/runs/get
POST_PRED_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/run-now
GET_RESULT_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/runs/get-output

# Databricks Jobs ID (後で設定)
TRAINING_JOB_ID=
PREDICTION_JOB_ID=

# Databricks アクセストークン (ローカル開発用 - 実際の値は .env.local に記載)
DATABRICKS_TOKEN=

# Gradio 設定
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_ANALYTICS_ENABLED=False
```

**チェックリスト**:
- [ ] .env.example 作成
- [ ] .env.local.example 作成
- [ ] .gitignore に .env.local 追加
- [ ] settings.py の環境変数読み込み確認

---

#### 1.2 app.yaml の作成 ⭐ **最優先**

**所要時間**: 1-2時間

**ファイルパス**: `PricingAIFrontend-develop 2/app.yaml`

**実装内容**:
```yaml
# Databricks Apps 設定ファイル
name: pricing-ai-frontend
version: 1.0.0

# エントリーポイント
command:
  - python
  - app.py

# 環境変数
env:
  GRADIO_SERVER_NAME: "0.0.0.0"
  GRADIO_SERVER_PORT: "8080"
  GRADIO_ANALYTICS_ENABLED: "False"
  PYTHONPATH: "/workspace"

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

# シークレット (Phase 2で設定)
# secrets:
#   - scope: pricing-ai-secrets
#     key: databricks-token
#     env_var: DATABRICKS_TOKEN
```

**チェックリスト**:
- [ ] app.yaml 作成
- [ ] requirements.txt の依存関係確認・更新
- [ ] app.py がDatabricks Apps環境変数を使用するように修正

---

#### 1.3 app.py の Databricks Apps 対応修正

**所要時間**: 30分

**修正内容**:
```python
# app.py (修正版)
from components.layouts.MainLayout import MainLayout
from components.tables.SelectableTable import SelectableTable
from components.forms.PredictionForm import PredictionForm
from components.forms.TrainingForm import TrainingForm
from data.demodata import checkbox_demo_data
import gradio as gr
import os
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Databricks Apps 環境変数
SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

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
    logger.info(f"Starting PricingAI Gradio App on {SERVER_NAME}:{SERVER_PORT}")

    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        show_error=True,
        quiet=False
    )
```

**チェックリスト**:
- [ ] app.py に環境変数設定追加
- [ ] ロギング設定追加
- [ ] ローカルで動作確認 (`python app.py`)

---

#### 1.4 .gitignore の更新

**所要時間**: 10分

**追加内容**:
```gitignore
# 環境変数
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Gradio
gradio_cached_examples/
flagged/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Databricks
.databricks/

# Logs
*.log
```

**チェックリスト**:
- [ ] .gitignore 更新
- [ ] 不要なファイルが除外されていることを確認

---

### Phase 1 完了基準
- [ ] .env.example と app.yaml が作成済み
- [ ] app.py が環境変数を使用するように修正済み
- [ ] ローカル環境で `python app.py` が正常に起動
- [ ] .gitignore が適切に設定済み

---

## 📅 Phase 2: Databricks統合準備 (2-3日)

### 目標
Databricks Jobs APIとの統合を完成させ、Databricks Notebookを作成する

### タスク

#### 2.1 Databricks Notebookの作成 ⭐ **重要**

**所要時間**: 3-4時間

**作成場所**: Databricks Workspace `/Users/{your_email}/PricingAI/`

**ファイル構成**:
```
/Users/{your_email}/PricingAI/
├── TrainingNotebook.py          # トレーニングジョブ用Notebook
├── PredictionNotebook.py        # 予測ジョブ用Notebook
└── Sp_interface.py              # ML関数 (PricingAI_Spark-main からコピー)
```

**TrainingNotebook.py の実装**:
```python
# Databricks notebook source
# MAGIC %md
# MAGIC # PricingAI モデルトレーニング Notebook

# COMMAND ----------
# パラメータウィジェットの作成
dbutils.widgets.text("case_period_start", "2024-01-01")
dbutils.widgets.text("case_period_end", "2024-12-31")
dbutils.widgets.text("stores", "001,002,003")
dbutils.widgets.text("output_zero", "/dbfs/mnt/models/pricing_ai/model_zero")
dbutils.widgets.text("output_up", "/dbfs/mnt/models/pricing_ai/model_up")
dbutils.widgets.text("verbose", "true")

# COMMAND ----------
# パラメータの取得と検証
case_period_start = dbutils.widgets.get("case_period_start")
case_period_end = dbutils.widgets.get("case_period_end")
stores_str = dbutils.widgets.get("stores")
output_zero = dbutils.widgets.get("output_zero")
output_up = dbutils.widgets.get("output_up")
verbose = dbutils.widgets.get("verbose").lower() == "true"

# バリデーション
from datetime import datetime
try:
    datetime.strptime(case_period_start, "%Y-%m-%d")
    datetime.strptime(case_period_end, "%Y-%m-%d")
except ValueError as e:
    dbutils.notebook.exit(json.dumps({
        "status": "error",
        "message": f"日付フォーマットエラー: {str(e)}"
    }))

# COMMAND ----------
# パラメータ変換
case_period = (case_period_start, case_period_end)
stores = stores_str.split(",")

print(f"学習期間: {case_period}")
print(f"対象店舗: {stores}")
print(f"Verbose: {verbose}")

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

    dbutils.notebook.exit(json.dumps(result, ensure_ascii=False))

except Exception as e:
    import traceback
    error_result = {
        "status": "error",
        "message": str(e),
        "error_type": type(e).__name__,
        "traceback": traceback.format_exc()
    }

    print("=== トレーニングエラー ===")
    print(json.dumps(error_result, indent=2, ensure_ascii=False))

    dbutils.notebook.exit(json.dumps(error_result, ensure_ascii=False))

# COMMAND ----------
```

**チェックリスト**:
- [ ] TrainingNotebook.py 作成
- [ ] PredictionNotebook.py 作成
- [ ] PricingAI_Spark-main の ML関数を Databricks Workspace にアップロード
- [ ] Notebook 単体で動作確認

---

#### 2.2 Databricks Jobs の作成

**所要時間**: 2時間

**手順**:

1. **トレーニングジョブ作成**:
   - Databricks UI: Workflows > Jobs > Create Job
   - Job Name: `PricingAI-Training`
   - Task: Notebook
   - Notebook Path: `/Users/{your_email}/PricingAI/TrainingNotebook`
   - Cluster: 新規クラスター (Spark 3.x, Standard_DS3_v2, 2 workers)

2. **予測ジョブ作成**:
   - Job Name: `PricingAI-Prediction`
   - Notebook Path: `/Users/{your_email}/PricingAI/PredictionNotebook`

3. **Job ID の取得**:
   - 各ジョブの詳細ページからJob IDを取得
   - .env.local に設定:
     ```bash
     TRAINING_JOB_ID=933047963643733
     PREDICTION_JOB_ID=933047963643734
     ```

**チェックリスト**:
- [ ] トレーニングジョブ作成完了
- [ ] 予測ジョブ作成完了
- [ ] Job ID を .env.local に設定
- [ ] 手動実行で動作確認

---

#### 2.3 API統合コードの改善

**所要時間**: 2-3時間

**修正ファイル**: `lib/api/apiClient.py`

**改善内容**:
```python
# lib/api/apiClient.py (改善版)
import requests
import os
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabricksJobsClient:
    """Databricks Jobs API クライアント"""

    def __init__(self):
        self.host = os.getenv("DATABRICKS_HOST", "").rstrip("/")
        self.token = os.getenv("DATABRICKS_TOKEN")

        if not self.host or not self.token:
            raise ValueError("DATABRICKS_HOST と DATABRICKS_TOKEN を設定してください")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def run_job(self, job_id: int, notebook_params: Dict[str, str]) -> Dict[str, Any]:
        """
        Databricks Jobを実行

        Parameters:
        -----------
        job_id : int
            実行するジョブのID
        notebook_params : Dict[str, str]
            Notebookに渡すパラメータ

        Returns:
        --------
        Dict[str, Any]
            run_id を含むレスポンス
        """
        url = f"{self.host}/api/2.2/jobs/run-now"
        payload = {
            "job_id": job_id,
            "notebook_params": notebook_params
        }

        logger.info(f"Running job {job_id} with params: {notebook_params}")

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Job started successfully. Run ID: {result.get('run_id')}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to run job: {str(e)}")
            raise

    def get_run_status(self, run_id: int) -> Dict[str, Any]:
        """
        ジョブ実行のステータスを取得

        Parameters:
        -----------
        run_id : int
            実行ID

        Returns:
        --------
        Dict[str, Any]
            実行ステータス情報
        """
        url = f"{self.host}/api/2.2/jobs/runs/get"
        params = {"run_id": run_id}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get run status: {str(e)}")
            raise

    def get_run_output(self, run_id: int) -> Optional[str]:
        """
        ジョブ実行の出力結果を取得

        Parameters:
        -----------
        run_id : int
            実行ID (task run_id)

        Returns:
        --------
        Optional[str]
            実行結果 (JSON文字列)
        """
        url = f"{self.host}/api/2.2/jobs/runs/get-output"
        params = {"run_id": run_id}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            result = response.json()
            return result.get("notebook_output", {}).get("result")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get run output: {str(e)}")
            raise

    def wait_for_completion(self, run_id: int, max_wait: int = 3600,
                           check_interval: int = 10) -> Dict[str, Any]:
        """
        ジョブ実行の完了を待機

        Parameters:
        -----------
        run_id : int
            実行ID
        max_wait : int
            最大待機時間（秒）
        check_interval : int
            チェック間隔（秒）

        Returns:
        --------
        Dict[str, Any]
            最終的な実行ステータス
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = self.get_run_status(run_id)
            state = status.get("state", {})
            life_cycle_state = state.get("life_cycle_state")

            logger.info(f"Run {run_id} status: {life_cycle_state}")

            if life_cycle_state in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
                return status

            time.sleep(check_interval)

        raise TimeoutError(f"Job execution timed out after {max_wait} seconds")

# グローバルクライアントインスタンス
_client = None

def get_databricks_client() -> DatabricksJobsClient:
    """Databricks Jobs APIクライアントのシングルトンインスタンスを取得"""
    global _client
    if _client is None:
        _client = DatabricksJobsClient()
    return _client


# 後方互換性のため残す
def apiClient(payload):
    """
    旧APIクライアント (後方互換性のため残す)

    新しいコードでは get_databricks_client() を使用してください
    """
    logger.warning("apiClient() は非推奨です。get_databricks_client() を使用してください。")
    # 簡易的な実装
    return {"status": "deprecated"}
```

**チェックリスト**:
- [ ] apiClient.py を改善版に更新
- [ ] 環境変数 DATABRICKS_HOST を .env.example に追加
- [ ] ユニットテストを作成（後で可）

---

#### 2.4 フォーム送信処理の更新

**所要時間**: 1-2時間

**修正ファイル**: `lib/api/sending.py`

**改善内容**:
```python
# lib/api/sending.py (改善版)
from settings import *
from lib.utils.data_utils import to_datestr
from lib.api.apiClient import get_databricks_client
import logging
import os
import json

logger = logging.getLogger(__name__)

def send_data(selected_stores, start_date, end_date):
    """
    学習ジョブを開始

    Parameters:
    -----------
    selected_stores : list[str]
        選択された店舗名のリスト
    start_date : str
        開始日
    end_date : str
        終了日

    Returns:
    --------
    str
        実行結果メッセージ
    """
    # バリデーション
    if not selected_stores or not start_date or not end_date:
        return "❌ 店舗・期間をすべて選択してください。"

    try:
        # 日付変換
        start_date_str = to_datestr(start_date)
        end_date_str = to_datestr(end_date)

        # 店舗コード取得
        store_codes = DF_STORES.loc[
            DF_STORES["store_name"].isin(selected_stores),
            "store_code"
        ].tolist()
        store_codes_str = ",".join([str(code) for code in store_codes])

        # Job パラメータ作成
        notebook_params = {
            "case_period_start": start_date_str,
            "case_period_end": end_date_str,
            "stores": store_codes_str,
            "output_zero": "/dbfs/mnt/models/pricing_ai/model_zero",
            "output_up": "/dbfs/mnt/models/pricing_ai/model_up",
            "verbose": "true"
        }

        # Databricks Jobs API実行
        client = get_databricks_client()
        training_job_id = int(os.getenv("TRAINING_JOB_ID"))

        logger.info(f"Starting training job {training_job_id}")
        result = client.run_job(training_job_id, notebook_params)

        run_id = result.get("run_id")

        return f"""✅ 学習ジョブを開始しました

🆔 Run ID: {run_id}
📅 学習期間: {start_date_str} ~ {end_date_str}
🏪 対象店舗: {len(store_codes)}店舗

ジョブの進行状況は Databricks UI で確認できます。
"""

    except Exception as e:
        logger.error(f"Failed to start training job: {str(e)}")
        return f"❌ エラーが発生しました: {str(e)}"


def send_pre(pred_store_name, pred_date):
    """
    予測ジョブを開始

    Parameters:
    -----------
    pred_store_name : str
        予測対象店舗名
    pred_date : str
        予測日

    Returns:
    --------
    str
        実行結果メッセージ
    """
    # バリデーション
    if not pred_store_name or not pred_date:
        return "❌ 店舗名と予測日を両方選択してください"

    try:
        pred_date_str = to_datestr(pred_date)
        store_code_str = str(
            DF_STORES.loc[DF_STORES["store_name"] == pred_store_name, "store_code"].iat[0]
        )

        # Job パラメータ作成
        notebook_params = {
            "store_cd": store_code_str,
            "upday": pred_date_str,
            "model_zero": "/dbfs/mnt/models/pricing_ai/model_zero",
            "model_up": "/dbfs/mnt/models/pricing_ai/model_up",
            "item_file": "/dbfs/mnt/data/item_master.csv",
            "drop_file": "/dbfs/mnt/data/drop_items.csv",
            "verbose": "true"
        }

        # Databricks Jobs API実行
        client = get_databricks_client()
        prediction_job_id = int(os.getenv("PREDICTION_JOB_ID"))

        logger.info(f"Starting prediction job {prediction_job_id}")
        result = client.run_job(prediction_job_id, notebook_params)

        run_id = result.get("run_id")

        return f"""✅ 予測ジョブを開始しました

🆔 Run ID: {run_id}
🏪 対象店舗: {pred_store_name} ({store_code_str})
📅 予測日: {pred_date_str}

ジョブの進行状況は Databricks UI で確認できます。
"""

    except Exception as e:
        logger.error(f"Failed to start prediction job: {str(e)}")
        return f"❌ エラーが発生しました: {str(e)}"
```

**チェックリスト**:
- [ ] sending.py を改善版に更新
- [ ] TrainingForm.py, PredictionForm.py で動作確認
- [ ] エラーハンドリングの確認

---

#### 2.5 Secret Scope の作成

**所要時間**: 30分

**手順**:

1. Databricks UI で Secret Scope 作成:
   - Settings > Developer > Secret Scopes
   - Scope Name: `pricing-ai-secrets`
   - Manage Principal: Creator

2. Secret の登録:
   ```bash
   databricks secrets put-secret \
     --scope pricing-ai-secrets \
     --key databricks-token
   # プロンプトでトークンを入力
   ```

3. app.yaml にシークレット設定追加:
   ```yaml
   secrets:
     - scope: pricing-ai-secrets
       key: databricks-token
       env_var: DATABRICKS_TOKEN
   ```

**チェックリスト**:
- [ ] Secret Scope作成完了
- [ ] databricks-token シークレット登録完了
- [ ] app.yaml にシークレット設定追加

---

### Phase 2 完了基準
- [ ] Databricks Notebook作成完了
- [ ] Databricks Jobs作成完了
- [ ] API統合コード改善完了
- [ ] Secret Scope設定完了
- [ ] ローカル→Databricks Jobs の通信確認完了

---

## 📅 Phase 3: Databricks Apps デプロイ (3-5日)

### 目標
Databricks AppsにGradio UIをデプロイし、動作確認する

### タスク

#### 3.1 Databricks App の作成

**所要時間**: 1時間

**手順** (CLI使用):
```bash
# 1. Databricks CLI インストール
pip install databricks-cli

# 2. 認証設定
databricks configure --token
# Host: https://adb-xxxxx.azuredatabricks.net
# Token: [your access token]

# 3. App 作成
databricks apps create \
  --app-name pricing-ai-frontend-development \
  --git-url https://github.com/igawa-nac/GRADIO-CLEANUP.git \
  --git-branch develop \
  --git-path "PricingAIFrontend-develop 2" \
  --description "PricingAI Gradio UI - 開発環境"
```

**または UI から**:
1. Apps > Create App
2. 設定:
   - App Name: `pricing-ai-frontend-development`
   - Source: Git Repository
   - Repository: `https://github.com/igawa-nac/GRADIO-CLEANUP.git`
   - Branch: `develop`
   - Path: `PricingAIFrontend-develop 2`

**チェックリスト**:
- [ ] App作成完了
- [ ] Git連携設定完了
- [ ] App URLの取得

---

#### 3.2 初回デプロイとトラブルシューティング

**所要時間**: 2-3時間

**デプロイ実行**:
```bash
databricks apps deploy --app-name pricing-ai-frontend-development
```

**想定される問題と対処**:

| 問題 | 原因 | 解決策 |
|------|------|--------|
| ModuleNotFoundError | requirements.txt 不足 | 依存関係を追加 |
| Port binding error | ポート設定ミス | app.yaml のポート確認 |
| Secret not found | シークレット未設定 | Secret Scope確認 |
| Permission denied | アクセス権限不足 | Workspace管理者に連絡 |

**ログ確認**:
```bash
# ログの確認
databricks apps logs --app-name pricing-ai-frontend-development --tail 100

# リアルタイムログ
databricks apps logs --app-name pricing-ai-frontend-development --follow
```

**チェックリスト**:
- [ ] デプロイ成功
- [ ] アプリが起動
- [ ] UIにアクセス可能
- [ ] エラーログがないことを確認

---

#### 3.3 動作確認とデバッグ

**所要時間**: 2-3時間

**確認項目**:

1. **UI表示確認**:
   - [ ] トレーニングフォームが正常に表示
   - [ ] 予測フォームが正常に表示
   - [ ] テーブルが正常に表示

2. **機能確認**:
   - [ ] 店舗選択ドロップダウンが動作
   - [ ] 日付ピッカーが動作
   - [ ] 学習開始ボタンクリック → Run ID表示
   - [ ] Databricks Jobsが実際に起動

3. **エラーハンドリング確認**:
   - [ ] 必須項目未入力時のエラーメッセージ
   - [ ] API通信エラー時の適切なメッセージ

**チェックリスト**:
- [ ] すべての機能が正常動作
- [ ] エラーハンドリングが適切
- [ ] ログに異常がない

---

### Phase 3 完了基準
- [ ] Databricks Apps デプロイ完了
- [ ] UI が正常に動作
- [ ] Databricks Jobs との連携確認完了
- [ ] 基本的な動作確認完了

---

## 📅 Phase 4: 本番統合とテスト (5-7日)

### 目標
本番環境への準備と、包括的なテストの実施

### タスク

#### 4.1 CI/CDパイプラインの構築

**所要時間**: 3-4時間

**ファイルパス**: `.github/workflows/deploy-databricks-apps.yml`

**実装内容**:
```yaml
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

      - name: Install dependencies
        working-directory: ./PricingAIFrontend-develop 2
        run: |
          pip install -r requirements.txt
          pip install pytest ruff

      - name: Lint with ruff
        working-directory: ./PricingAIFrontend-develop 2
        run: |
          ruff check .

      - name: Run tests
        working-directory: ./PricingAIFrontend-develop 2
        run: |
          pytest tests/ || echo "No tests found"

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

**GitHub Secrets 設定**:
- `DATABRICKS_HOST`: Databricks ワークスペースURL
- `DATABRICKS_TOKEN`: Databricksアクセストークン

**チェックリスト**:
- [ ] GitHub Actions ワークフロー作成
- [ ] GitHub Secrets 設定
- [ ] develop ブランチへのpushで自動デプロイ確認
- [ ] main ブランチへのpushで自動デプロイ確認

---

#### 4.2 テストコードの作成

**所要時間**: 4-6時間

**ディレクトリ構造**:
```
PricingAIFrontend-develop 2/
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── test_api_client.py
    │   ├── test_sending.py
    │   └── test_data_utils.py
    ├── integration/
    │   ├── test_training_flow.py
    │   └── test_prediction_flow.py
    └── conftest.py
```

**サンプルテストコード**:
```python
# tests/unit/test_api_client.py
import pytest
from unittest.mock import Mock, patch
from lib.api.apiClient import DatabricksJobsClient

@pytest.fixture
def mock_env(monkeypatch):
    """環境変数のモック"""
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.azuredatabricks.net")
    monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")

def test_databricks_client_initialization(mock_env):
    """クライアント初期化のテスト"""
    client = DatabricksJobsClient()
    assert client.host == "https://test.azuredatabricks.net"
    assert client.token == "test-token"

@patch('requests.post')
def test_run_job_success(mock_post, mock_env):
    """ジョブ実行成功のテスト"""
    # モックレスポンス
    mock_response = Mock()
    mock_response.json.return_value = {"run_id": 12345}
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    client = DatabricksJobsClient()
    result = client.run_job(
        job_id=123,
        notebook_params={"test": "param"}
    )

    assert result["run_id"] == 12345
    mock_post.assert_called_once()
```

**チェックリスト**:
- [ ] ユニットテスト作成
- [ ] 統合テスト作成
- [ ] テストカバレッジ > 70%
- [ ] すべてのテストが合格

---

#### 4.3 本番環境用Appの作成

**所要時間**: 1時間

**手順**:
```bash
databricks apps create \
  --app-name pricing-ai-frontend-production \
  --git-url https://github.com/igawa-nac/GRADIO-CLEANUP.git \
  --git-branch main \
  --git-path "PricingAIFrontend-develop 2" \
  --description "PricingAI Gradio UI - 本番環境"
```

**本番環境用設定**:
- アクセス制限の設定
- ログレベルの調整
- リソース設定の最適化

**チェックリスト**:
- [ ] 本番App作成完了
- [ ] アクセス制限設定
- [ ] 本番用Secret Scope設定
- [ ] 本番用Jobs作成

---

#### 4.4 ドキュメント最終更新

**所要時間**: 2時間

**更新ドキュメント**:
- [ ] README.md: 実際のデプロイ手順を反映
- [ ] STRATEGY.md: 最新の情報に更新
- [ ] DatabricksAppsSetup.md: 実際の構築手順を追加

---

### Phase 4 完了基準
- [ ] CI/CDパイプライン構築完了
- [ ] テストコード作成・実行完了
- [ ] 本番環境App作成完了
- [ ] ドキュメント更新完了

---

## 📅 Phase 5: 本番リリース (1日)

### 目標
本番環境へのリリースと監視体制の確立

### タスク

#### 5.1 本番リリース

**所要時間**: 2-3時間

**手順**:
1. develop ブランチの最終確認
2. release ブランチ作成
3. リリースノート作成
4. main ブランチへマージ
5. タグ付与 (v1.0.0)
6. 自動デプロイ確認

**チェックリスト**:
- [ ] release ブランチ作成
- [ ] リリースノート作成
- [ ] main へマージ
- [ ] タグ付与・プッシュ
- [ ] 本番環境デプロイ確認

---

#### 5.2 監視とアラート設定

**所要時間**: 1-2時間

**設定項目**:
- [ ] アプリケーションログの定期確認
- [ ] エラー率の監視
- [ ] レスポンス時間の監視
- [ ] DBU消費量の監視

---

#### 5.3 運用ドキュメント作成

**所要時間**: 1-2時間

**作成ドキュメント**:
- [ ] 運用手順書
- [ ] トラブルシューティングガイド
- [ ] ロールバック手順

---

### Phase 5 完了基準
- [ ] 本番環境リリース完了
- [ ] 監視体制確立
- [ ] 運用ドキュメント作成完了

---

## 📋 全体チェックリスト

### 環境構築
- [ ] .env.example 作成
- [ ] app.yaml 作成
- [ ] app.py Databricks Apps 対応
- [ ] .gitignore 更新

### Databricks統合
- [ ] Databricks Notebook 作成
- [ ] Databricks Jobs 作成
- [ ] Secret Scope 作成
- [ ] API統合コード改善

### デプロイ
- [ ] 開発環境App作成
- [ ] 初回デプロイ成功
- [ ] 動作確認完了
- [ ] 本番環境App作成

### テスト・品質保証
- [ ] CI/CDパイプライン構築
- [ ] テストコード作成
- [ ] テスト実行・合格
- [ ] ドキュメント更新

### 本番リリース
- [ ] リリースブランチ作成
- [ ] 本番デプロイ
- [ ] 監視設定
- [ ] 運用ドキュメント作成

---

## 🎯 優先順位まとめ

### 最優先 (今すぐ着手)
1. **.env.example と app.yaml の作成** (Phase 1.1, 1.2)
2. **Databricks Notebook の作成** (Phase 2.1)
3. **Databricks Jobs の作成** (Phase 2.2)

### 高優先 (1週間以内)
4. **API統合コードの改善** (Phase 2.3, 2.4)
5. **Secret Scope の設定** (Phase 2.5)
6. **Databricks Apps デプロイ** (Phase 3.1-3.3)

### 中優先 (2週間以内)
7. **CI/CDパイプライン構築** (Phase 4.1)
8. **テストコード作成** (Phase 4.2)
9. **本番環境準備** (Phase 4.3)

### 低優先 (3週間以内)
10. **本番リリース** (Phase 5)

---

## 📞 サポート

困ったときは:
1. **ドキュメント参照**: STRATEGY.md, DatabricksAppsSetup.md
2. **ログ確認**: `databricks apps logs --app-name <app-name> --tail 100`
3. **Issue作成**: DatabricksAppsIssueStrategy.md に従ってIssue作成

---

**最終更新**: 2025-10-22
**対象者**: 既存UI開発者
**前提**: Databricks Workspaceアクセス権限あり
