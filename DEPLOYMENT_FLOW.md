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

### ステップ2: app.yaml 設定

**PricingAIFrontend-develop 2/app.yaml**:

```yaml
name: pricing-ai-gradio-app

# アプリケーション設定
command:
  - "python"
  - "app.py"

# 環境変数（Secret Scopeから取得）
env:
  # Gradio設定
  - name: GRADIO_SERVER_NAME
    value: "0.0.0.0"
  - name: GRADIO_SERVER_PORT
    value: "8080"
  - name: GRADIO_ANALYTICS_ENABLED
    value: "false"

  # Databricks接続（Secret Scopeから取得）
  - name: DATABRICKS_HOST
    secret:
      scope: pricing-ai-secrets
      key: databricks-host
  - name: DATABRICKS_TOKEN
    secret:
      scope: pricing-ai-secrets
      key: databricks-token

  # Databricks Jobs ID
  - name: TRAINING_JOB_ID
    secret:
      scope: pricing-ai-secrets
      key: training-job-id
  - name: PREDICTION_JOB_ID
    secret:
      scope: pricing-ai-secrets
      key: prediction-job-id

  # データファイルパス
  - name: KKK_FILE
    value: "/dbfs/mnt/data/kkk_master_20250903.csv"
  - name: SERIES_FILE
    value: "/dbfs/mnt/data/series_mst_20250626.csv"
  - name: ITEM_FILE
    value: "/dbfs/mnt/data/item_master.csv"
  - name: DROP_FILE
    value: "/dbfs/mnt/data/drop_items.csv"

  # モデル保存先
  - name: OUTPUT_ZERO
    value: "/dbfs/mnt/models/pricing_ai/model_zero"
  - name: OUTPUT_UP
    value: "/dbfs/mnt/models/pricing_ai/model_up"

# リソース設定
resources:
  instance_type: "m5.xlarge"  # 4 vCPU, 16 GB RAM
  min_instances: 1
  max_instances: 2

# ヘルスチェック
health_check:
  path: "/"
  interval_seconds: 30
  timeout_seconds: 10
  unhealthy_threshold: 3
  healthy_threshold: 2

# ネットワーク設定
network:
  ingress:
    - port: 8080
      protocol: "http"
```

---

### ステップ3: Secret Scope セットアップ

Databricks Workspace で Secret Scope を作成:

```bash
# Databricks CLI でSecret Scope作成
databricks secrets create-scope pricing-ai-secrets

# Secret登録
databricks secrets put-secret pricing-ai-secrets databricks-host \
  --string-value "https://adb-xxxxx.azuredatabricks.net"

databricks secrets put-secret pricing-ai-secrets databricks-token \
  --string-value "dapi_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

databricks secrets put-secret pricing-ai-secrets training-job-id \
  --string-value "123456"

databricks secrets put-secret pricing-ai-secrets prediction-job-id \
  --string-value "789012"
```

**Secret Scope確認**:
```bash
# Secret Scope一覧
databricks secrets list-scopes

# Secret一覧
databricks secrets list-secrets pricing-ai-secrets
```

---

### ステップ4: app.py の Databricks Apps対応

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

# Databricks Apps環境変数
SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "8080"))

# Databricks Apps環境判定
IS_DATABRICKS_APPS = os.getenv("DATABRICKS_RUNTIME_VERSION") is not None

if IS_DATABRICKS_APPS:
    logger.info("Running on Databricks Apps environment")
else:
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
| **ポート** | 7860 | 8080 |
| **サーバー名** | localhost | 0.0.0.0 |
| **環境変数** | .env.local | Secret Scope |
| **データパス** | ./local_test_data/ | /dbfs/mnt/data/ |
| **モデル保存先** | ./local_models/ | /dbfs/mnt/models/ |
| **Databricks API** | Mock Client | 実際のAPI |
| **テストデータ** | ダミーデータ | 実データ |
| **認証** | 不要 | Databricks認証 |

---

## ✅ デプロイチェックリスト

### デプロイ前
- [ ] ローカルテスト完了 (localhost:7860)
- [ ] pytest 全テスト合格
- [ ] ruff Lintチェック合格
- [ ] .env.local がコミットされていない
- [ ] app.yaml 設定確認
- [ ] Secret Scope 設定確認

### デプロイ後
- [ ] GitHub Actions 成功確認
- [ ] Databricks Apps 起動確認
- [ ] アプリURL アクセス確認
- [ ] モデル学習 動作確認
- [ ] 価格予測 動作確認
- [ ] ログ確認（エラーなし）

---

## 🎓 ベストプラクティス

### 1. 環境変数の管理

```python
# 良い例: Secret Scopeを活用
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# 悪い例: ハードコード
DATABRICKS_TOKEN = "dapi_xxxxxxxx"  # ❌ 絶対にダメ！
```

### 2. ログの活用

```python
import logging

logger = logging.getLogger(__name__)

# 環境判定をログ出力
if IS_DATABRICKS_APPS:
    logger.info("Running on Databricks Apps")
    logger.info(f"Using data path: {os.getenv('KKK_FILE')}")
```

### 3. エラーハンドリング

```python
try:
    result = train_model(case_period, stores, output_zero, output_up)
except Exception as e:
    logger.error(f"Training failed: {str(e)}")
    return gr.update(value=f"エラー: {str(e)}")
```

### 4. デプロイ頻度

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

