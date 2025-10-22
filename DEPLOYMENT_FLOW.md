# Databricks Apps デプロイフロー - PricingAI Gradio UI

## 🎯 デプロイフロー概要

```
┌─────────────────────────────────────────────────────────────┐
│               ローカル開発 (Venv)                            │
│  - localhost:7860 でUI確認                                  │
│  - pytest テスト実行                                        │
│  - Lintチェック                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ git commit & push
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│  - develop ブランチへ push                                   │
│  - GitHub Actions トリガー                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ GitHub Actions実行
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               GitHub Actions (CI/CD)                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 1. Checkout コード                                  │     │
│  │ 2. Python環境セットアップ                           │     │
│  │ 3. 依存関係インストール                             │     │
│  │ 4. Lintチェック (ruff)                             │     │
│  │ 5. ユニットテスト (pytest)                          │     │
│  │ 6. Databricks CLI セットアップ                     │     │
│  │ 7. app.yaml 設定                                   │     │
│  │ 8. Databricks Apps デプロイ                        │     │
│  └────────────────────────────────────────────────────┘     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ デプロイ実行
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Azure Databricks Apps (本番環境)                     │
│  - アプリ自動起動                                            │
│  - Secret Scope から環境変数取得                             │
│  - 実データでモデル学習・予測実行                             │
│  - ポート 8080 でアクセス可能                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 前提条件

### Azure Databricks 環境
- Databricks Workspace URL (例: `https://adb-xxxxx.azuredatabricks.net`)
- Databricks Access Token (CI/CD用)
- Secret Scope 作成済み (`pricing-ai-secrets`)

### GitHub リポジトリ
- GitHub Actions 有効化
- GitHub Secrets 設定:
  - `DATABRICKS_HOST`: Databricks Workspace URL
  - `DATABRICKS_TOKEN`: Databricks アクセストークン

### 必要な権限
- Databricks Apps 作成・デプロイ権限
- Secret Scope 読み取り権限
- Databricks Jobs 実行権限

---

## 🚀 デプロイステップ詳細

### ステップ1: GitHub Actions ワークフロー作成

**.github/workflows/deploy-databricks-apps.yml**:

```yaml
name: Deploy to Databricks Apps

on:
  push:
    branches:
      - develop
      - main
  pull_request:
    branches:
      - develop

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd "PricingAIFrontend-develop 2"
          pip install -r requirements.txt
          pip install ruff pytest pytest-cov

      - name: Run Ruff linting
        run: |
          cd "PricingAIFrontend-develop 2"
          ruff check .

      - name: Run pytest
        run: |
          cd "PricingAIFrontend-develop 2"
          pytest tests/ --cov=components --cov-report=xml

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/develop' || github.ref == 'refs/heads/main'
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
        run: |
          databricks configure --token <<EOF
          ${{ secrets.DATABRICKS_HOST }}
          ${{ secrets.DATABRICKS_TOKEN }}
          EOF

      - name: Deploy to Databricks Apps
        run: |
          cd "PricingAIFrontend-develop 2"
          databricks apps deploy pricing-ai-gradio-app \
            --source-dir . \
            --app-yaml app.yaml

      - name: Verify deployment
        run: |
          databricks apps get pricing-ai-gradio-app
```

---

### ステップ2: databricks.yml 設定（リソース宣言）

**databricks.yml** (プロジェクトルート):

```yaml
bundle:
  name: pricing-ai-app-bundle

# アプリとリソースの定義
resources:
  apps:
    pricing_ai_app:
      name: 'pricing-ai-gradio-app'
      source_code_path: './PricingAIFrontend-develop 2'
      description: 'PricingAI - 価格最適化システム Gradio UI'

      # リソース宣言（app.yamlから参照される）
      resources:
        # Secret Scopeのシークレット
        secrets:
          databricks_token:
            scope: pricing-ai-secrets
            key: databricks-token
          training_job_id:
            scope: pricing-ai-secrets
            key: training-job-id
          prediction_job_id:
            scope: pricing-ai-secrets
            key: prediction-job-id

          # データファイルパス（環境別に管理）
          kkk_file_path:
            scope: pricing-ai-secrets
            key: kkk-file-path
          series_file_path:
            scope: pricing-ai-secrets
            key: series-file-path
          item_file_path:
            scope: pricing-ai-secrets
            key: item-file-path
          drop_file_path:
            scope: pricing-ai-secrets
            key: drop-file-path

          # モデル保存先パス
          model_zero_path:
            scope: pricing-ai-secrets
            key: model-zero-path
          model_up_path:
            scope: pricing-ai-secrets
            key: model-up-path

# 環境別ターゲット
targets:
  dev:
    mode: development
    workspace:
      host: https://adb-xxxxx-dev.azuredatabricks.net

  prod:
    mode: production
    workspace:
      host: https://adb-xxxxx-prod.azuredatabricks.net
```

---

### ステップ3: app.yaml 設定（環境変数定義）

**PricingAIFrontend-develop 2/app.yaml**:

```yaml
# アプリケーション設定
command:
  - "python"
  - "app.py"

# 環境変数定義
env:
  # 静的な設定値（非機密情報のみ）
  - name: LOG_LEVEL
    value: "info"
  - name: GRADIO_ANALYTICS_ENABLED
    value: "false"

  # リソース参照（databricks.ymlで宣言したリソースキーを使用）
  # 重要: DATABRICKS_HOST, APP_PORTは自動設定されるため不要

  - name: DATABRICKS_TOKEN
    valueFrom: databricks_token

  - name: TRAINING_JOB_ID
    valueFrom: training_job_id

  - name: PREDICTION_JOB_ID
    valueFrom: prediction_job_id

  # データファイルパス（環境別）
  - name: KKK_FILE
    valueFrom: kkk_file_path

  - name: SERIES_FILE
    valueFrom: series_file_path

  - name: ITEM_FILE
    valueFrom: item_file_path

  - name: DROP_FILE
    valueFrom: drop_file_path

  # モデル保存先
  - name: OUTPUT_ZERO
    valueFrom: model_zero_path

  - name: OUTPUT_UP
    valueFrom: model_up_path
```

**重要なポイント**:
- ✅ `DATABRICKS_HOST`, `APP_PORT`: Databricks Appsで**自動設定**されるため、手動設定不要
- ✅ `valueFrom`: databricks.ymlで宣言したリソースキーを参照
- ✅ 機密情報は**絶対にハードコードしない** - すべて`valueFrom`で参照
- ✅ 環境固有の値（ファイルパス、Job IDなど）もSecretで管理し、環境間のポータビリティを確保

---

### ステップ4: Secret Scope セットアップ

Databricks Workspace で Secret Scope を作成し、環境固有の値を登録:

```bash
# 1. Secret Scope作成（初回のみ）
databricks secrets create-scope pricing-ai-secrets

# 2. 認証情報の登録
databricks secrets put-secret pricing-ai-secrets databricks-token \
  --string-value "dapi_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 3. Databricks Jobs IDの登録
databricks secrets put-secret pricing-ai-secrets training-job-id \
  --string-value "123456"

databricks secrets put-secret pricing-ai-secrets prediction-job-id \
  --string-value "789012"

# 4. データファイルパスの登録（環境別）
# Dev環境
databricks secrets put-secret pricing-ai-secrets kkk-file-path \
  --string-value "/dbfs/mnt/dev/data/kkk_master_20250903.csv"

databricks secrets put-secret pricing-ai-secrets series-file-path \
  --string-value "/dbfs/mnt/dev/data/series_mst_20250626.csv"

databricks secrets put-secret pricing-ai-secrets item-file-path \
  --string-value "/dbfs/mnt/dev/data/item_master.csv"

databricks secrets put-secret pricing-ai-secrets drop-file-path \
  --string-value "/dbfs/mnt/dev/data/drop_items.csv"

# 5. モデル保存先パスの登録（環境別）
databricks secrets put-secret pricing-ai-secrets model-zero-path \
  --string-value "/dbfs/mnt/dev/models/pricing_ai/model_zero"

databricks secrets put-secret pricing-ai-secrets model-up-path \
  --string-value "/dbfs/mnt/dev/models/pricing_ai/model_up"
```

**環境別Secret管理のベストプラクティス**:
- Dev環境: `/dbfs/mnt/dev/...`
- Prod環境: `/dbfs/mnt/prod/...`
- 環境ごとに異なるSecret Scopeを作成 (`pricing-ai-secrets-dev`, `pricing-ai-secrets-prod`)

**Secret Scope確認**:
```bash
# Secret Scope一覧
databricks secrets list-scopes

# Secret一覧
databricks secrets list-secrets pricing-ai-secrets
```

---

### ステップ5: app.py の Databricks Apps対応

**PricingAIFrontend-develop 2/app.py** (修正版):

```python
import os
import logging
import gradio as gr
from components.pages.TrainingPage import TrainingPage
from components.pages.PredictionPage import PredictionPage

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
    gr.Markdown("# PricingAI - 価格最適化システム")

    with gr.Tabs():
        with gr.Tab("モデル学習"):
            TrainingPage()

        with gr.Tab("価格予測"):
            PredictionPage()

if __name__ == "__main__":
    logger.info(f"Starting PricingAI Gradio App on {SERVER_NAME}:{SERVER_PORT}")

    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        show_error=True,
        quiet=False,
        # Databricks Apps では認証不要
        auth=None
    )
```

**自動設定される環境変数の活用**:
```python
# Databricks Appsで自動的に利用可能な環境変数
APP_NAME = os.getenv("APP_NAME")                          # アプリ名
APP_PORT = os.getenv("APP_PORT")                          # アプリポート（必須）
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")            # ワークスペースURL
DATABRICKS_WORKSPACE_ID = os.getenv("DATABRICKS_WORKSPACE_ID")
DATABRICKS_CLIENT_ID = os.getenv("DATABRICKS_CLIENT_ID")  # サービスプリンシパル
DATABRICKS_CLIENT_SECRET = os.getenv("DATABRICKS_CLIENT_SECRET")
```

---

## 🔄 デプロイ実行フロー

### 開発者の作業フロー

```bash
# === 1. ローカルで開発・テスト ===
cd GRADIO-CLEANUP
cd "PricingAIFrontend-develop 2"

# Venv有効化
source ../venv/bin/activate  # Mac/Linux
# または
..\venv\Scripts\activate  # Windows

# ローカルテスト
python app.py
# → http://localhost:7860 でUI確認

pytest tests/
ruff check .

# === 2. Git commit & push ===
git add .
git commit -m "[#FE-XXX] 新機能実装"
git push origin feature/FE-XXX-NewFeature

# === 3. Pull Request作成 ===
# GitHubでPR作成 → develop へマージ

# === 4. 自動デプロイ実行 ===
# develop へのマージで GitHub Actions が自動実行
# → Databricks Apps に自動デプロイ
```

### GitHub Actions 自動実行

```
develop ブランチへのpush/merge
  ↓
GitHub Actions トリガー
  ↓
┌─────────────────────────┐
│ 1. Checkout             │
│ 2. Python Setup         │
│ 3. Install Dependencies │
│ 4. Ruff Lint            │
│ 5. Pytest               │
└───────────┬─────────────┘
            │
            ↓ (成功時のみ)
┌─────────────────────────┐
│ 6. Databricks CLI Setup │
│ 7. Deploy to Apps       │
│ 8. Verify Deployment    │
└───────────┬─────────────┘
            │
            ↓
Databricks Apps 起動
```

---

## ✅ デプロイ確認

### 1. GitHub Actions ログ確認

```
GitHub → Actions タブ → 最新のワークフロー実行
```

成功時のログ例:
```
✅ Ruff linting passed
✅ Pytest passed (XX tests, 90% coverage)
✅ Databricks Apps deployment successful
✅ App URL: https://adb-xxxxx.azuredatabricks.net/apps/pricing-ai-gradio-app
```

### 2. Databricks Apps 確認

Databricks CLI:
```bash
# アプリ一覧
databricks apps list

# 特定アプリの状態
databricks apps get pricing-ai-gradio-app

# ログ確認
databricks apps logs pricing-ai-gradio-app
```

Databricks Workspace UI:
```
Databricks Workspace → Apps → pricing-ai-gradio-app
```

### 3. アプリ動作確認

ブラウザでアクセス:
```
https://adb-xxxxx.azuredatabricks.net/apps/pricing-ai-gradio-app
```

確認項目:
- [ ] UIが正しく表示される
- [ ] モデル学習が実行できる
- [ ] 価格予測が実行できる
- [ ] Secret Scopeから環境変数が読み込まれている
- [ ] Databricks Jobs が正常に実行される

---

## 🐛 トラブルシューティング

### 問題1: デプロイが失敗する

```bash
エラー: Error deploying app: Invalid app.yaml configuration

解決策:
# app.yaml の構文確認
yamllint PricingAIFrontend-develop\ 2/app.yaml

# Databricks CLI バージョン確認
databricks --version

# 最新版にアップデート
pip install --upgrade databricks-cli
```

### 問題2: Secret が読み込めない

```bash
エラー: KeyError: 'DATABRICKS_TOKEN'

解決策:
# Secret Scope確認
databricks secrets list-secrets pricing-ai-secrets

# Secret が存在しない場合は作成
databricks secrets put-secret pricing-ai-secrets databricks-token \
  --string-value "dapi_xxxxxxxx"

# app.yaml で Secret参照が正しいか確認
```

### 問題3: アプリが起動しない

```bash
解決策:
# ログ確認
databricks apps logs pricing-ai-gradio-app

# よくあるエラー:
# - ポート番号が 8080 でない
# - server_name が 0.0.0.0 でない
# - 依存関係が不足

# app.py 修正例:
SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "8080"))
```

### 問題4: GitHub Actions が失敗

```bash
エラー: pytest failed

解決策:
# ローカルで同じコマンド実行
cd "PricingAIFrontend-develop 2"
pip install -r requirements.txt
pytest tests/

# テストが通ることを確認してから push
```

---

## 🔄 ロールバック手順

### 手動ロールバック

```bash
# 1. 前のバージョンに戻す
git checkout <前回の安定版commit>

# 2. 再デプロイ
git push origin develop -f

# または、GitHub Actions で手動デプロイ
# GitHub → Actions → Re-run workflow
```

### Databricks Apps ロールバック

```bash
# 前のバージョンに戻す
databricks apps deploy pricing-ai-gradio-app \
  --source-dir . \
  --app-yaml app.yaml \
  --revision <前回のrevision>
```

---

## 📊 環境別設定比較

| 項目 | ローカル (Venv) | Databricks Apps |
|------|----------------|-----------------|
| **Python環境** | Venv | Databricks Runtime |
| **ポート** | 7860 (GRADIO_SERVER_PORT) | APP_PORT（自動設定） |
| **サーバー名** | 0.0.0.0 | 0.0.0.0 |
| **ホスト名** | - | DATABRICKS_HOST（自動設定） |
| **環境変数管理** | .env.local（ファイル） | databricks.yml + Secret Scope |
| **環境変数参照** | dotenv | valueFrom（リソース参照） |
| **データパス** | ./local_test_data/ | /dbfs/mnt/{env}/data/ |
| **モデル保存先** | ./local_models/ | /dbfs/mnt/{env}/models/ |
| **Databricks API** | Mock Client | 実際のAPI（自動認証） |
| **テストデータ** | ダミーデータ | 実データ |
| **認証** | 不要 | 自動（サービスプリンシパル） |
| **設定ファイル** | .env.local | databricks.yml, app.yaml |

---

## ✅ デプロイチェックリスト

### デプロイ前
- [ ] ローカルテスト完了 (localhost:7860)
- [ ] pytest 全テスト合格
- [ ] ruff Lintチェック合格
- [ ] .env.local がコミットされていない
- [ ] databricks.yml にリソース宣言完了
- [ ] app.yaml で valueFrom によるリソース参照確認
- [ ] Secret Scope に全ての環境変数登録完了
- [ ] app.py で APP_PORT を使用していることを確認

### デプロイ後
- [ ] GitHub Actions 成功確認
- [ ] Databricks Apps 起動確認
- [ ] アプリURL アクセス確認
- [ ] モデル学習 動作確認
- [ ] 価格予測 動作確認
- [ ] ログ確認（エラーなし）

---

## 🎓 ベストプラクティス

### 1. 環境変数の管理（重要）

**✅ 推奨: databricks.yml + app.yaml + valueFrom**
```yaml
# databricks.yml
resources:
  apps:
    my_app:
      resources:
        secrets:
          api_key:
            scope: my-scope
            key: api-key

# app.yaml
env:
  - name: API_KEY
    valueFrom: api_key  # リソース参照
```

**✅ アプリコードでの読み込み**
```python
# 良い例: 環境変数から読み込み
API_KEY = os.getenv("API_KEY")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# Databricks Apps自動設定の環境変数を活用
APP_PORT = int(os.getenv("APP_PORT"))  # 自動設定
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")  # 自動設定
```

**❌ 悪い例: ハードコード**
```python
# 絶対にダメ！
DATABRICKS_TOKEN = "dapi_xxxxxxxx"  # ❌
API_KEY = "secret123"  # ❌
```

**❌ 悪い例: app.yamlで直接設定**
```yaml
# app.yaml
env:
  - name: DATABRICKS_TOKEN
    value: "dapi_xxxxxxxx"  # ❌ 機密情報のハードコード
```

### 2. 自動設定環境変数の活用

```python
import os

# Databricks Apps環境判定
IS_DATABRICKS_APPS = os.getenv("APP_NAME") is not None

if IS_DATABRICKS_APPS:
    # 自動設定された環境変数を使用
    port = int(os.getenv("APP_PORT"))  # 必須
    host = os.getenv("DATABRICKS_HOST")
    workspace_id = os.getenv("DATABRICKS_WORKSPACE_ID")
    app_name = os.getenv("APP_NAME")
else:
    # ローカル開発環境のデフォルト値
    port = 7860
```

### 3. ログの活用

```python
import logging

logger = logging.getLogger(__name__)

# 環境判定をログ出力
if IS_DATABRICKS_APPS:
    logger.info("Running on Databricks Apps")
    logger.info(f"App Name: {os.getenv('APP_NAME')}")
    logger.info(f"Port: {os.getenv('APP_PORT')}")
    logger.info(f"Using data path: {os.getenv('KKK_FILE')}")
```

### 4. エラーハンドリング

```python
try:
    result = train_model(case_period, stores, output_zero, output_up)
except Exception as e:
    logger.error(f"Training failed: {str(e)}")
    return gr.update(value=f"エラー: {str(e)}")
```

### 5. デプロイ頻度

- **develop ブランチ**: 毎日デプロイ可能
- **main ブランチ**: 週1回のリリース推奨
- **hotfix**: 緊急時のみ

---

## 📚 関連ドキュメント

デプロイ後の運用について:

1. **[LOCAL_DEV_GUIDE.md](./LOCAL_DEV_GUIDE.md)** - ローカル開発ガイド
2. **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - 実装計画
3. **[MISSING_UI_PLAN.md](./MISSING_UI_PLAN.md)** - 未実装UI開発計画
4. **[DatabricksAppsSetup.md](./docs/DatabricksAppsSetup.md)** - 初期セットアップ

---

**最終更新**: 2025-10-22
**対象**: DevOps / UI開発者
**環境**: GitHub Actions → Azure Databricks Apps

