# フロントエンド・バックエンド整合性ガイド

## 概要
このドキュメントでは、PricingAI FrontendのGradio UIとPricingAI_Spark-mainの機械学習バックエンドの整合性を確保するためのガイドラインを説明します。

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                     Gradio UI (Frontend)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ Training    │  │ Prediction  │  │ Result Display   │   │
│  │ Form        │  │ Form        │  │ Table            │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                           │
                           │ Databricks Jobs API
                           │ (REST API)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Databricks Jobs (Orchestration)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Job 1: Training Pipeline                           │   │
│  │  Job 2: Prediction Pipeline                         │   │
│  │  Job 3: Result Export Pipeline                      │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                           │
                           │ Function Call
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           PricingAI_Spark-main (ML Backend)                 │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ train_model()    │  │ predict_result()               │  │
│  │ - jan_feats      │  │ - batch_predict_result()       │  │
│  │ - lv5_feats      │  │ - RandomForestClassifierPrice  │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 1. データモデルの整合性

### 1.1 トレーニングパラメータ

#### フロントエンド (TrainingForm.py)
```python
# 必須パラメータ
training_params = {
    "case_period": tuple[str, str],    # 学習期間 (開始日, 終了日)
    "stores": list[str],                # 店舗コードリスト
    "output_zero": str,                 # ゼロモデル出力パス
    "output_up": str,                   # アップモデル出力パス
    "verbose": bool                     # 詳細ログ出力
}
```

#### バックエンド (Sp_interface.py)
```python
def train_model(case_period, stores, output_zero, output_up, verbose=False):
    """
    Parameters:
    -----------
    case_period : tuple[str, str]
        学習期間 (開始日, 終了日) 例: ("2024-01-01", "2024-12-31")
    stores : list[str]
        店舗コードリスト 例: ["001", "002", "003"]
    output_zero : str
        ゼロモデル保存パス 例: "/path/to/model_zero"
    output_up : str
        アップモデル保存パス 例: "/path/to/model_up"
    verbose : bool
        詳細ログ出力フラグ (デフォルト: False)
    """
```

**整合性確保のチェックリスト**:
- [ ] パラメータ名が一致しているか
- [ ] パラメータ型が一致しているか
- [ ] 日付フォーマットが統一されているか (YYYY-MM-DD)
- [ ] バリデーションロジックがフロント・バック両方に存在するか

### 1.2 予測パラメータ

#### フロントエンド (PredictionForm.py)
```python
prediction_params = {
    "store_cd": str,           # 店舗コード
    "upday": str,              # 値上げ日 (YYYY-MM-DD)
    "model_zero": str,         # ゼロモデルパス
    "model_up": str,           # アップモデルパス
    "item_file": str,          # 商品マスターファイルパス
    "drop_file": str,          # 除外商品ファイルパス
    "verbose": bool            # 詳細ログ出力
}
```

#### バックエンド (Sp_interface.py)
```python
def predict_result(store_cd, upday, model_zero, model_up,
                   item_file, drop_file, verbose=False):
    """
    Returns:
    --------
    df_item : pyspark.sql.DataFrame
        商品別予測結果
    df_uid : pyspark.sql.DataFrame
        ユーザー別予測結果
    """
```

**整合性確保のチェックリスト**:
- [ ] 必須パラメータがすべてフロントエンドから送信されているか
- [ ] ファイルパスがDatabricks Workspace上で有効か
- [ ] 戻り値のスキーマがフロントエンド側で正しく処理されるか

### 1.3 特徴量定義

#### バックエンド (Sp_interface.py)
```python
# JAN (商品コード) レベルの特徴量
jan_feats = [
    "dprice",              # 値引き額
    "dprice_pct",          # 値引き率
    "rscore",              # Recency スコア
    "fscore",              # Frequency スコア
    "mscore",              # Monetary スコア
    "rfm_score",           # RFM統合スコア
    "rfm_score2",          # RFM統合スコア2
    "jan_loy_m",           # JAN ロイヤリティ (M)
    "jan_loy_f",           # JAN ロイヤリティ (F)
    "jan_loy",             # JAN ロイヤリティ
    "pscore_item",         # アイテム価格スコア
    "pscore_ucate",        # カテゴリ価格スコア
    "pscore_ucate_dis050", # カテゴリ価格スコア (50%割引)
    "kani_score",          # 感度スコア
    "kani_score_dis025"    # 感度スコア (25%割引)
]

# LV5 (カテゴリ) レベルの特徴量
lv5_feats = [
    "pprice",              # 元値
    "aprice",              # 値上げ後価格
    "dprice",              # 値引き額
    "dprice_pct",          # 値引き率
    "unitp_cate",          # カテゴリ単価
    "pscore_ucate",        # カテゴリ価格スコア
    "unitp_uid",           # ユーザー単価
    "pscore_ucate_dis050", # カテゴリ価格スコア (50%割引)
    "f_lv5",               # LV5 Frequency
    "m_lv5",               # LV5 Monetary
    "jan_loy_m",           # JAN ロイヤリティ (M)
    "jan_loy_f",           # JAN ロイヤリティ (F)
    "jan_loy",             # JAN ロイヤリティ
    "kani_score",          # 感度スコア
    "kani_score_dis025"    # 感度スコア (25%割引)
]
```

#### フロントエンドでの対応
```python
# components/forms/FeatureSelector.py (新規作成推奨)
class FeatureSelector:
    """特徴量選択コンポーネント"""

    # バックエンドと同一の特徴量リスト
    JAN_FEATURES = [
        "dprice", "dprice_pct", "rscore", "fscore", "mscore",
        "rfm_score", "rfm_score2", "jan_loy_m", "jan_loy_f", "jan_loy",
        "pscore_item", "pscore_ucate", "pscore_ucate_dis050",
        "kani_score", "kani_score_dis025"
    ]

    LV5_FEATURES = [
        "pprice", "aprice", "dprice", "dprice_pct", "unitp_cate",
        "pscore_ucate", "unitp_uid", "pscore_ucate_dis050",
        "f_lv5", "m_lv5", "jan_loy_m", "jan_loy_f", "jan_loy",
        "kani_score", "kani_score_dis025"
    ]

    # 特徴量の説明 (日本語)
    FEATURE_DESCRIPTIONS = {
        "dprice": "値引き額",
        "dprice_pct": "値引き率",
        "rscore": "購入頻度スコア",
        # ... 他の特徴量の説明
    }
```

**整合性確保のチェックリスト**:
- [ ] 特徴量リストがバックエンドと完全一致しているか
- [ ] 特徴量追加時にフロント・バック両方を更新しているか
- [ ] 特徴量の説明がユーザーに分かりやすいか

## 2. API契約の整合性

### 2.1 Databricks Jobs API エンドポイント

#### 学習ジョブ開始
```python
# フロントエンド
POST_SOURCE_URL = os.getenv("POST_SOURCE_URL")
# 例: https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/run-now

payload = {
    "job_id": int,                    # ジョブID
    "notebook_params": {              # Notebookパラメータ
        "case_period_start": str,     # 開始日
        "case_period_end": str,       # 終了日
        "stores": str,                # 店舗コード (カンマ区切り)
        "output_zero": str,           # ゼロモデル出力パス
        "output_up": str,             # アップモデル出力パス
        "verbose": str                # "true" or "false"
    }
}

# レスポンス
{
    "run_id": int                     # 実行ID
}
```

#### ジョブステータス確認
```python
# フロントエンド
GET_PROGRESS_URL = os.getenv("GET_PROGRESS_URL")
# 例: https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/runs/get

payload = {
    "run_id": int                     # 実行ID
}

# レスポンス
{
    "state": {
        "life_cycle_state": str,      # PENDING, RUNNING, TERMINATED
        "state_message": str          # 状態メッセージ
    },
    "tasks": [
        {
            "run_id": int,            # タスク実行ID
            "task_key": str           # タスク名
        }
    ]
}
```

#### 結果取得
```python
# フロントエンド
GET_RESULT_URL = os.getenv("GET_RESULT_URL")
# 例: https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/runs/get-output

payload = {
    "run_id": int                     # タスク実行ID
}

# レスポンス
{
    "notebook_output": {
        "result": str                 # JSON文字列化された結果
    }
}
```

### 2.2 バックエンド Notebook 実装例

```python
# Databricks Notebook: TrainingJob.py

# パラメータ取得
dbutils.widgets.text("case_period_start", "")
dbutils.widgets.text("case_period_end", "")
dbutils.widgets.text("stores", "")
dbutils.widgets.text("output_zero", "")
dbutils.widgets.text("output_up", "")
dbutils.widgets.text("verbose", "false")

case_period_start = dbutils.widgets.get("case_period_start")
case_period_end = dbutils.widgets.get("case_period_end")
stores_str = dbutils.widgets.get("stores")
output_zero = dbutils.widgets.get("output_zero")
output_up = dbutils.widgets.get("output_up")
verbose = dbutils.widgets.get("verbose") == "true"

# パラメータ変換
case_period = (case_period_start, case_period_end)
stores = stores_str.split(",")

# ML関数の実行
%run ./Sp_interface.py

train_model(
    case_period=case_period,
    stores=stores,
    output_zero=output_zero,
    output_up=output_up,
    verbose=verbose
)

# 結果を返す
result = {
    "status": "success",
    "message": "モデルトレーニングが完了しました",
    "model_paths": {
        "zero": output_zero,
        "up": output_up
    }
}

import json
dbutils.notebook.exit(json.dumps(result, ensure_ascii=False))
```

**整合性確保のチェックリスト**:
- [ ] Notebook パラメータ名がフロントエンドのペイロードと一致しているか
- [ ] レスポンス形式がフロントエンドで正しくパースできるか
- [ ] エラーハンドリングが適切に実装されているか
- [ ] タイムアウト処理が考慮されているか

## 3. 環境変数管理

### 3.1 環境変数一覧

```bash
# .env.production (本番環境)
POST_SOURCE_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/run-now
GET_PROGRESS_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/runs/get
POST_PRED_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/run-now
GET_RESULT_URL=https://adb-xxxxx.azuredatabricks.net/api/2.2/jobs/runs/get-output
ACCESS_TOKEN=${DATABRICKS_TOKEN}  # Databricks Appsのシークレットから取得

# ジョブID
TRAINING_JOB_ID=933047963643733
PREDICTION_JOB_ID=933047963643734

# モデル保存先
MODEL_BASE_PATH=/dbfs/mnt/models/pricing_ai
```

```bash
# .env.development (開発環境)
POST_SOURCE_URL=https://adb-yyyyy.azuredatabricks.net/api/2.2/jobs/run-now
GET_PROGRESS_URL=https://adb-yyyyy.azuredatabricks.net/api/2.2/jobs/runs/get
POST_PRED_URL=https://adb-yyyyy.azuredatabricks.net/api/2.2/jobs/run-now
GET_RESULT_URL=https://adb-yyyyy.azuredatabricks.net/api/2.2/jobs/runs/get-output
ACCESS_TOKEN=${DATABRICKS_TOKEN}

TRAINING_JOB_ID=123456789012345
PREDICTION_JOB_ID=123456789012346

MODEL_BASE_PATH=/dbfs/mnt/models/pricing_ai_dev
```

### 3.2 Databricks Apps シークレット設定

```python
# Databricks Appsのシークレット設定
# UI: Workspace > Apps > [App名] > Configuration > Secrets

# 必要なシークレット:
# - DATABRICKS_TOKEN: Databricks アクセストークン
# - DATABRICKS_HOST: Databricks ホストURL
```

**整合性確保のチェックリスト**:
- [ ] 環境ごとに適切な値が設定されているか
- [ ] シークレットがコードにハードコードされていないか
- [ ] .env.example が最新の環境変数を反映しているか

## 4. データスキーマの整合性

### 4.1 予測結果スキーマ

#### バックエンド出力
```python
# df_item スキーマ (商品別予測結果)
df_item_schema = {
    "store_cd": "string",        # 店舗コード
    "lv4_nm": "string",          # カテゴリレベル4名
    "lv5_nm": "string",          # カテゴリレベル5名
    "jan": "string",             # JANコード
    "astart": "date",            # 値上げ開始日
    "pprice": "double",          # 元値
    "uid": "string",             # ユーザーID
    "sample_amt_jan": "double",  # サンプル金額
    "prob_jan_0": "double",      # JAN 確率 (値上げなし)
    "prob_jan_-10": "double",    # JAN 確率 (-10円)
    "prob_jan_-20": "double",    # JAN 確率 (-20円)
    "prob_lv5_0": "double",      # LV5 確率 (値上げなし)
    "prob_lv5_-10": "double",    # LV5 確率 (-10円)
    "prob_lv5_-20": "double"     # LV5 確率 (-20円)
}

# df_uid スキーマ (ユーザー別予測結果)
df_uid_schema = {
    "store_cd": "string",        # 店舗コード
    "uid": "string",             # ユーザーID
    "predicted_revenue": "double",  # 予測売上
    "predicted_margin": "double"    # 予測粗利
}
```

#### フロントエンド表示
```python
# components/tables/SelectableTable.py
# 表示カラムの定義
display_columns = [
    {"field": "store_cd", "headerName": "店舗コード", "width": 100},
    {"field": "jan", "headerName": "JANコード", "width": 150},
    {"field": "lv5_nm", "headerName": "カテゴリ", "width": 200},
    {"field": "pprice", "headerName": "元値", "width": 100},
    {"field": "prob_jan_0", "headerName": "確率(±0円)", "width": 120},
    {"field": "prob_jan_-10", "headerName": "確率(-10円)", "width": 120},
    {"field": "prob_jan_-20", "headerName": "確率(-20円)", "width": 120}
]
```

**整合性確保のチェックリスト**:
- [ ] カラム名がバックエンド出力と一致しているか
- [ ] データ型が適切に処理されているか (特に日付型)
- [ ] NULL値の処理が適切か
- [ ] 数値の丸め処理が統一されているか

## 5. バージョン管理とデプロイ

### 5.1 フロント・バックバージョンの対応表

| Frontend Version | Backend Version | 互換性 | 備考 |
|-----------------|----------------|-------|------|
| v1.0.0 | v1.0.0 | ✓ | 初期リリース |
| v1.1.0 | v1.0.0 | ✓ | UI改善のみ |
| v1.2.0 | v1.1.0 | ✓ | 新特徴量対応 |
| v2.0.0 | v2.0.0 | ✓ | API変更 (破壊的変更) |

### 5.2 バージョン互換性チェック

```python
# lib/api/version_check.py (新規作成推奨)
class VersionChecker:
    """フロント・バックバージョン互換性チェック"""

    FRONTEND_VERSION = "1.2.0"
    COMPATIBLE_BACKEND_VERSIONS = ["1.0.0", "1.1.0", "1.2.0"]

    @staticmethod
    def check_compatibility(backend_version: str) -> bool:
        """
        バックエンドバージョンとの互換性をチェック

        Parameters:
        -----------
        backend_version : str
            バックエンドのバージョン

        Returns:
        --------
        bool
            互換性があればTrue
        """
        return backend_version in VersionChecker.COMPATIBLE_BACKEND_VERSIONS

    @staticmethod
    def get_backend_version() -> str:
        """
        バックエンドのバージョンを取得 (API経由)
        """
        # バックエンドAPIからバージョン情報を取得
        # 実装は環境に応じて調整
        pass
```

**整合性確保のチェックリスト**:
- [ ] バージョン番号がセマンティックバージョニングに従っているか
- [ ] 破壊的変更時はメジャーバージョンを上げているか
- [ ] バージョン互換性表が最新か

## 6. テスト戦略

### 6.1 統合テスト

```python
# tests/integration/test_training_pipeline.py
import pytest
from components.forms.TrainingForm import TrainingForm
from lib.api.apiClient import apiClient

class TestTrainingPipeline:
    """トレーニングパイプライン統合テスト"""

    def test_training_e2e(self):
        """E2Eトレーニングテスト"""
        # 1. フロントエンドからパラメータ作成
        params = {
            "case_period_start": "2024-01-01",
            "case_period_end": "2024-12-31",
            "stores": "001,002,003",
            "output_zero": "/dbfs/test/model_zero",
            "output_up": "/dbfs/test/model_up",
            "verbose": "true"
        }

        # 2. API経由でジョブ実行
        response = apiClient(params)
        assert response["status"] == "success"

        # 3. 結果検証
        assert "model_paths" in response
        assert response["model_paths"]["zero"] == params["output_zero"]

    def test_parameter_validation(self):
        """パラメータバリデーションテスト"""
        # 不正なパラメータ
        invalid_params = {
            "case_period_start": "invalid-date",
            "stores": "",
        }

        # バリデーションエラーが発生することを確認
        with pytest.raises(ValueError):
            apiClient(invalid_params)
```

### 6.2 契約テスト (Contract Testing)

```python
# tests/contract/test_api_contract.py
import pytest
from pydantic import BaseModel, validator

class TrainingRequest(BaseModel):
    """トレーニングリクエストスキーマ"""
    case_period_start: str
    case_period_end: str
    stores: str
    output_zero: str
    output_up: str
    verbose: str

    @validator('case_period_start', 'case_period_end')
    def validate_date(cls, v):
        # 日付フォーマット検証
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("日付は YYYY-MM-DD 形式である必要があります")
        return v

class TrainingResponse(BaseModel):
    """トレーニングレスポンススキーマ"""
    status: str
    message: str
    model_paths: dict

def test_request_schema():
    """リクエストスキーマテスト"""
    valid_request = {
        "case_period_start": "2024-01-01",
        "case_period_end": "2024-12-31",
        "stores": "001",
        "output_zero": "/path",
        "output_up": "/path",
        "verbose": "true"
    }

    # スキーマ検証
    request = TrainingRequest(**valid_request)
    assert request.case_period_start == "2024-01-01"

def test_response_schema():
    """レスポンススキーマテスト"""
    valid_response = {
        "status": "success",
        "message": "完了",
        "model_paths": {"zero": "/path", "up": "/path"}
    }

    # スキーマ検証
    response = TrainingResponse(**valid_response)
    assert response.status == "success"
```

**整合性確保のチェックリスト**:
- [ ] 統合テストが定期的に実行されているか
- [ ] 契約テストがCI/CDパイプラインに組み込まれているか
- [ ] テストカバレッジが十分か (目標: 80%以上)

## 7. ドキュメント同期

### 7.1 API仕様書の管理

```yaml
# docs/api/openapi.yaml
openapi: 3.0.0
info:
  title: PricingAI API
  version: 1.0.0
  description: PricingAI フロント・バック API仕様

paths:
  /api/2.2/jobs/run-now:
    post:
      summary: トレーニングジョブ実行
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                job_id:
                  type: integer
                  example: 933047963643733
                notebook_params:
                  type: object
                  properties:
                    case_period_start:
                      type: string
                      format: date
                      example: "2024-01-01"
                    case_period_end:
                      type: string
                      format: date
                      example: "2024-12-31"
                    stores:
                      type: string
                      example: "001,002,003"
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  run_id:
                    type: integer
                    example: 687283416244517
```

### 7.2 変更管理プロセス

1. **バックエンド変更時**:
   ```bash
   # 1. バックエンドコード変更
   # 2. API仕様書更新
   # 3. フロントエンドに影響確認
   # 4. フロントエンドコード更新
   # 5. 統合テスト実行
   # 6. ドキュメント更新
   ```

2. **フロントエンド変更時**:
   ```bash
   # 1. フロントエンドコード変更
   # 2. バックエンドに新規要件確認
   # 3. バックエンド変更必要な場合は Issue 作成
   # 4. 統合テスト実行
   # 5. ドキュメント更新
   ```

**整合性確保のチェックリスト**:
- [ ] API仕様書が最新か
- [ ] 変更履歴が記録されているか (CHANGELOG.md)
- [ ] フロント・バック両チームが変更を認識しているか

## 8. トラブルシューティング

### 8.1 よくある整合性エラー

#### エラー1: パラメータ名の不一致
```
エラー: KeyError: 'case_period_start'

原因: フロントエンドが "start_date" を送信、バックエンドが "case_period_start" を期待

解決策:
1. フロントエンドのパラメータ名を修正
2. または、バックエンドで両方のパラメータ名を受け入れる
```

#### エラー2: 日付フォーマットの不一致
```
エラー: ValueError: time data '01/01/2024' does not match format '%Y-%m-%d'

原因: フロントエンドが MM/DD/YYYY、バックエンドが YYYY-MM-DD を期待

解決策:
フロントエンドで統一フォーマットに変換:
```python
from datetime import datetime

def format_date(date_str: str) -> str:
    """日付を YYYY-MM-DD 形式に変換"""
    # MM/DD/YYYY → YYYY-MM-DD
    dt = datetime.strptime(date_str, "%m/%d/%Y")
    return dt.strftime("%Y-%m-%d")
```

#### エラー3: 特徴量リストの不一致
```
エラー: KeyError: 'pscore_item'

原因: バックエンドで特徴量 "pscore_item" が削除されたが、フロントエンドは古いリストを使用

解決策:
1. フロントエンドの特徴量リストを更新
2. バージョン互換性チェックを実装
```

### 8.2 デバッグ手法

```python
# lib/utils/debug_utils.py
import json
import logging

class IntegrationDebugger:
    """フロント・バック統合デバッグツール"""

    @staticmethod
    def log_request(params: dict, endpoint: str):
        """リクエストをログ出力"""
        logging.info(f"=== Request to {endpoint} ===")
        logging.info(json.dumps(params, indent=2, ensure_ascii=False))

    @staticmethod
    def log_response(response: dict, endpoint: str):
        """レスポンスをログ出力"""
        logging.info(f"=== Response from {endpoint} ===")
        logging.info(json.dumps(response, indent=2, ensure_ascii=False))

    @staticmethod
    def validate_schema(data: dict, schema: dict) -> list:
        """スキーマ検証"""
        errors = []
        for key, expected_type in schema.items():
            if key not in data:
                errors.append(f"Missing required field: {key}")
            elif not isinstance(data[key], expected_type):
                errors.append(
                    f"Type mismatch for {key}: "
                    f"expected {expected_type}, got {type(data[key])}"
                )
        return errors
```

## 9. まとめ

フロントエンド・バックエンドの整合性を確保するために:

1. **パラメータ・スキーマの統一**: 命名規則、データ型、フォーマットを統一
2. **バージョン管理**: セマンティックバージョニングと互換性管理
3. **契約テスト**: API契約の自動検証
4. **ドキュメント同期**: API仕様書の定期更新
5. **定期的な統合テスト**: CI/CDパイプラインでの自動テスト
6. **コミュニケーション**: フロント・バックチーム間の密な連携

このガイドラインを遵守し、常に整合性を意識した開発を行ってください。
