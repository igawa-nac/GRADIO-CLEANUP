# ローカル開発ガイド - Databricks Apps Gradio UI

## 🎯 開発フロー概要

```
┌─────────────────────────────────────────────────────────────┐
│                  ローカル開発環境 (Venv)                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │  1. コード実装                                       │     │
│  │  2. localhost:7860 でUI確認                         │     │
│  │  3. テスト実行                                       │     │
│  └────────────────────────────────────────────────────┘     │
└───────────────────────────┬─────────────────────────────────┘
                           │
                           │ Git Commit & Push
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      GitHub                                  │
│  - develop ブランチへ push                                   │
│  - GitHub Actions (CI/CD) 実行                              │
└───────────────────────────┬─────────────────────────────────┘
                           │
                           │ 自動デプロイ
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            Azure Databricks Apps (本番環境)                  │
│  - 自動的にアプリがデプロイ                                   │
│  - 実データで動作確認                                        │
└─────────────────────────────────────────────────────────────┘
```

## 📋 前提条件

### 必要なソフトウェア
- Python 3.10 以上
- Git
- VSCode (推奨)

### Azure Databricks アクセス
- Databricks Workspace URL
- Databricks アクセストークン (開発・テスト用)

---

## 🚀 ローカル開発環境セットアップ

### ステップ1: リポジトリのクローン

```bash
# 1. リポジトリをクローン
git clone https://github.com/igawa-nac/GRADIO-CLEANUP.git
cd GRADIO-CLEANUP

# 2. 開発ブランチに切り替え
git checkout develop
git pull origin develop
```

### ステップ2: Venv環境の作成

```bash
# 1. Venv作成
python -m venv venv

# 2. Venv有効化
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# 3. 依存関係インストール
cd "PricingAIFrontend-develop 2"
pip install -r requirements.txt
```

### ステップ3: ローカル用環境変数設定

```bash
# .env.local を作成（.gitignoreで除外されているので安全）
cp .env.example .env.local
```

**.env.local の設定例**（ローカル開発用）:
```bash
# ===== ローカル開発用設定 =====

# Gradio設定
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_ANALYTICS_ENABLED=False

# ===== Databricks接続（テスト用） =====
# ※実際の接続テストをする場合のみ設定
DATABRICKS_HOST=https://adb-xxxxx.azuredatabricks.net
DATABRICKS_TOKEN=dapi_your_dev_token_here

# Databricks Jobs ID（開発環境）
TRAINING_JOB_ID=
PREDICTION_JOB_ID=

# ===== ローカルテスト用ダミーパス =====
# ※実際にはDatabricks上のファイルを使用
# ローカルではダミーデータでUI確認のみ

# データファイル（ローカルテスト用）
KKK_FILE=./local_test_data/kkk_master_dummy.csv
SERIES_FILE=./local_test_data/series_mst_dummy.csv
ITEM_FILE=./local_test_data/item_master_dummy.csv
DROP_FILE=./local_test_data/drop_items_dummy.csv

# モデル保存先（ローカルテスト用）
OUTPUT_ZERO=./local_models/model_zero
OUTPUT_UP=./local_models/model_up
```

### ステップ4: ローカルテスト用ダミーデータ作成

```bash
# ローカルテスト用ディレクトリ作成
mkdir -p "PricingAIFrontend-develop 2/local_test_data"
mkdir -p "PricingAIFrontend-develop 2/local_models"
```

**ダミーデータ作成スクリプト** (`scripts/create_dummy_data.py`):
```python
import pandas as pd
import os

# ディレクトリ作成
os.makedirs("local_test_data", exist_ok=True)

# 1. kkk_master_dummy.csv
df_kkk = pd.DataFrame({
    'jan': ['4901234567890', '4901234567891', '4901234567892'],
    'det_val': [750, 500, 1000]
})
df_kkk.to_csv('local_test_data/kkk_master_dummy.csv', index=False)

# 2. series_mst_dummy.csv
df_series = pd.DataFrame({
    'jan': ['4901234567890', '4901234567891'],
    'series': ['A', 'A']
})
df_series.to_csv('local_test_data/series_mst_dummy.csv', index=False)

# 3. item_master_dummy.csv
df_item = pd.DataFrame({
    'jan': ['4901234567890', '4901234567891', '4901234567892'],
    'name': ['商品A', '商品B', '商品C'],
    'oprice': [100, 150, 200],
    'max_dprice': [50, 50, 50]
})
df_item.to_csv('local_test_data/item_master_dummy.csv', index=False)

# 4. drop_items_dummy.csv
df_drop = pd.DataFrame({
    'jan': []
})
df_drop.to_csv('local_test_data/drop_items_dummy.csv', index=False)

print("✅ ローカルテスト用ダミーデータを作成しました")
```

実行:
```bash
cd "PricingAIFrontend-develop 2"
python ../scripts/create_dummy_data.py
```

---

## 🔧 ローカルでの開発とテスト

### UI実装の基本フロー

#### 1. 新しいコンポーネント実装

例: FileManagementForm を作成

```bash
# 1. ファイル作成
touch components/forms/FileManagementForm.py

# 2. VSCodeで開いて実装
code components/forms/FileManagementForm.py
```

**実装時の注意点**:
- ローカルとDatabricks Appsの両方で動作するように実装
- ファイルパスは環境変数から取得
- バリデーションを徹底

#### 2. ローカルでのUI確認

```bash
# Venvが有効化されていることを確認
# (venv) が表示されているはず

# アプリ起動
cd "PricingAIFrontend-develop 2"
python app.py
```

ブラウザで http://localhost:7860 にアクセス

**確認項目**:
- [ ] UIが正しく表示されるか
- [ ] 入力フィールドが正常に動作するか
- [ ] バリデーションが機能するか
- [ ] エラーメッセージが適切か
- [ ] デフォルト値が設定されているか

#### 3. ローカルでのテスト実行

```bash
# ユニットテスト
pytest tests/unit/

# 特定のテストファイルのみ
pytest tests/unit/test_file_management_form.py

# カバレッジ付き
pytest --cov=components --cov-report=html
```

#### 4. Lintチェック

```bash
# Ruff でコードチェック
ruff check .

# 自動修正
ruff check --fix .
```

---

## 📝 コード実装時の注意事項

### 環境変数の使用

**良い例** - 環境変数を使用:
```python
import os

# ローカルとDatabricks Appsで異なるパスを使い分け
kkk_file = os.getenv("KKK_FILE", "/dbfs/mnt/data/kkk_master_20250903.csv")
```

**悪い例** - ハードコード:
```python
# ❌ これはダメ！環境によってパスが違う
kkk_file = "/dbfs/mnt/data/kkk_master_20250903.csv"
```

### ファイルパスの設定

```python
# settings.py に追加
import os
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local")

# ファイルパス設定
KKK_FILE = os.getenv("KKK_FILE", "/dbfs/mnt/data/kkk_master_20250903.csv")
SERIES_FILE = os.getenv("SERIES_FILE", "/dbfs/mnt/data/series_mst_20250626.csv")
ITEM_FILE = os.getenv("ITEM_FILE", "/dbfs/mnt/data/item_master.csv")
DROP_FILE = os.getenv("DROP_FILE", "/dbfs/mnt/data/drop_items.csv")
```

### Databricks API呼び出しのモック

ローカルテストではDatabricks APIを実際に呼び出さない:

```python
# lib/api/apiClient.py

def get_databricks_client():
    """Databricks Jobs APIクライアントを取得"""

    # ローカル開発モードの判定
    is_local = os.getenv("GRADIO_SERVER_PORT") == "7860"

    if is_local and not os.getenv("DATABRICKS_TOKEN"):
        logger.warning("ローカル開発モード: Databricks API呼び出しをスキップ")
        return MockDatabricksClient()

    return DatabricksJobsClient()


class MockDatabricksClient:
    """ローカルテスト用モッククライアント"""

    def run_job(self, job_id, notebook_params):
        logger.info(f"[MOCK] Job {job_id} を実行: {notebook_params}")
        return {"run_id": 12345}

    def get_run_status(self, run_id):
        return {
            "state": {"life_cycle_state": "TERMINATED"},
            "tasks": [{"run_id": 67890}]
        }
```

---

## 🔄 開発ワークフロー

### 日常的な開発フロー

```bash
# === 1. 開発開始 ===
cd GRADIO-CLEANUP
git checkout develop
git pull origin develop

# 機能ブランチ作成
git checkout -b feature/FE-001-FileManagementForm

# Venv有効化
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate  # Windows

# === 2. コード実装 ===
cd "PricingAIFrontend-develop 2"
code .  # VSCodeで開く

# (コード実装...)

# === 3. ローカルテスト ===
python app.py
# → http://localhost:7860 でUI確認

# テスト実行
pytest tests/

# Lintチェック
ruff check .

# === 4. Git commit ===
git add .
git commit -m "[#FE-001] FileManagementForm実装"
git push origin feature/FE-001-FileManagementForm

# === 5. Pull Request作成 ===
# GitHubでPR作成 → develop へマージ

# === 6. Databricks Apps 自動デプロイ ===
# develop へのマージで自動的にDatabricks Appsにデプロイされる
```

---

## 🐛 トラブルシューティング

### 問題1: モジュールが見つからない

```bash
エラー: ModuleNotFoundError: No module named 'gradio'

解決策:
# Venvが有効化されているか確認
which python
# → venv/bin/python が表示されるはず

# 依存関係を再インストール
pip install -r requirements.txt
```

### 問題2: ポートが既に使用されている

```bash
エラー: OSError: [Errno 48] Address already in use

解決策:
# 既存のプロセスを終了
lsof -i :7860
kill -9 <PID>

# または、別のポートを使用
GRADIO_SERVER_PORT=7861 python app.py
```

### 問題3: 環境変数が読み込まれない

```bash
解決策:
# .env.local の存在確認
ls -la .env.local

# settings.py で読み込み確認
python -c "from settings import *; print(KKK_FILE)"
```

---

## ✅ ローカル開発チェックリスト

### コード実装前
- [ ] Venv作成・有効化済み
- [ ] 依存関係インストール済み
- [ ] .env.local 設定済み
- [ ] ダミーデータ準備済み

### コード実装中
- [ ] 環境変数を使用（ハードコードしない）
- [ ] ローカル/Databricks Apps両対応
- [ ] バリデーション実装
- [ ] エラーハンドリング実装

### ローカルテスト
- [ ] localhost:7860でUI表示確認
- [ ] すべての入力フィールド動作確認
- [ ] エラーメッセージ表示確認
- [ ] pytest テスト合格
- [ ] ruff Lintチェック合格

### Git commit前
- [ ] 不要なファイルが含まれていないか確認
- [ ] .env.local がコミットされていないか確認
- [ ] コミットメッセージが明確か

### PR作成前
- [ ] develop ブランチの最新を取り込み済み
- [ ] コンフリクト解消済み
- [ ] PR説明が明確か

---

## 🎓 ベストプラクティス

### 1. 小さく頻繁にコミット
```bash
# 良い例
git commit -m "[#FE-001] FileManagementForm UIレイアウト実装"
git commit -m "[#FE-001] ファイル存在確認機能追加"
git commit -m "[#FE-001] バリデーション実装"

# 悪い例
git commit -m "[#FE-001] すべて完了"
```

### 2. ローカルで十分にテスト
Databricks Appsにデプロイする前に、ローカルで徹底的にテスト:
- UI動作確認
- エラーケース確認
- 境界値テスト

### 3. 環境の違いを意識
| 項目 | ローカル | Databricks Apps |
|------|---------|----------------|
| ファイルパス | 相対パス or ./local_test_data/ | /dbfs/mnt/data/ |
| 環境変数 | .env.local | Secret Scope |
| データ | ダミーデータ | 実データ |
| ポート | 7860 | 8080 |

### 4. .gitignore の確認
以下がignoreされていることを確認:
```gitignore
.env.local
local_test_data/
local_models/
venv/
__pycache__/
*.pyc
```

---

## 📚 次のステップ

ローカル開発が完了したら:

1. **[DEPLOYMENT_FLOW.md](./DEPLOYMENT_FLOW.md)** - Databricks Appsへのデプロイフロー
2. **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - 実装計画
3. **[MISSING_UI_PLAN.md](./MISSING_UI_PLAN.md)** - 未実装UI開発計画

---

**最終更新**: 2025-10-22
**対象**: UI開発者
**環境**: ローカル開発 (Venv) → Databricks Apps デプロイ
