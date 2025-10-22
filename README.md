# GRADIO-CLEANUP

## 概要

このリポジトリは、Azure DatabricksのDatabricks Appsを使用してGradio UIで構築されたPricingAI (価格予測AI) システムを含んでいます。

Spark MLベースの機械学習バックエンドと、Gradioベースのフロントエンドを統合し、直感的な価格予測UIを提供します。

## 📁 プロジェクト構成

```
GRADIO-CLEANUP/
├── PricingAIFrontend-develop 2/    # Gradio UIフロントエンド
│   ├── app.py                       # メインアプリケーション
│   ├── components/                  # UIコンポーネント
│   │   ├── forms/                   # フォームコンポーネント
│   │   ├── layouts/                 # レイアウトコンポーネント
│   │   ├── inputs/                  # 入力コンポーネント
│   │   └── tables/                  # テーブルコンポーネント
│   ├── lib/                         # ライブラリとユーティリティ
│   │   ├── api/                     # API クライアント
│   │   ├── utils/                   # ユーティリティ関数
│   │   └── data_processing/         # データ処理
│   ├── docs/                        # ドキュメント
│   │   ├── api/                     # API仕様
│   │   └── development/             # 開発ガイド ⭐
│   ├── data/                        # データファイル
│   ├── requirements.txt             # Python依存関係
│   └── settings.py                  # 設定管理
│
├── PricingAI_Spark-main/           # Spark ML バックエンド
│   ├── Sp_interface.py             # ML関数インターフェース
│   ├── Sp_algo.py                  # アルゴリズム実装
│   ├── Sp_feat.py                  # 特徴量エンジニアリング
│   ├── Sp_train_and_predict.py     # トレーニング・予測
│   └── ...                         # その他のMLモジュール
│
├── STRATEGY.md                     # 📘 総合開発戦略ガイド
└── README.md                       # このファイル
```

## 🚀 クイックスタート

### 前提条件
- Python 3.10 以上
- Azure Databricks Workspace へのアクセス
- Git

### ローカル開発環境のセットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/GRADIO-CLEANUP.git
cd GRADIO-CLEANUP

# 2. 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 依存関係のインストール
cd "PricingAIFrontend-develop 2"
pip install -r requirements.txt

# 4. 環境変数の設定
cp .env.example .env.local
# .env.local を編集して、必要な環境変数を設定

# 5. アプリケーションの起動
python app.py
```

アプリケーションは http://localhost:7860 で起動します。

## 📚 ドキュメント

### 🎯 総合戦略ガイド
**[STRATEGY.md](./STRATEGY.md)** - すべてのドキュメントへの入り口

このドキュメントから、以下のすべての専門ドキュメントにアクセスできます。

### 実装計画ドキュメント ⭐ NEW

| ドキュメント | 説明 | 使用タイミング |
|------------|------|--------------|
| **[実装計画](./IMPLEMENTATION_PLAN.md)** | **既存UI開発者向け実装ガイド** | **今すぐ着手すべき内容を確認** |
| **[未実装UI開発計画](./MISSING_UI_PLAN.md)** | **未実装UIの詳細開発計画** | **新規UI開発時** |

### 詳細ドキュメント (PricingAIFrontend-develop 2/docs/development/)

| ドキュメント | 説明 | 使用タイミング |
|------------|------|--------------|
| [Issue戦略](./PricingAIFrontend-develop%202/docs/development/DatabricksAppsIssueStrategy.md) | Issue管理のベストプラクティス | 新機能開発、バグ修正時 |
| [ブランチ戦略](./PricingAIFrontend-develop%202/docs/development/BranchStrategy.md) | Git Flowベースのブランチ管理 | 開発開始時、マージ時 |
| [整合性ガイド](./PricingAIFrontend-develop%202/docs/development/FrontendBackendConsistency.md) | フロント・バック整合性確保 | API設計時、特徴量変更時 |
| [Databricks Apps設定](./PricingAIFrontend-develop%202/docs/development/DatabricksAppsSetup.md) | Databricks Appsデプロイガイド | 環境構築時、デプロイ時 |

### その他のドキュメント

- [使用方法](./PricingAIFrontend-develop%202/docs/development/usage.md) - アプリケーションの使い方
- [シークレット管理](./PricingAIFrontend-develop%202/docs/development/UseSecret.md) - 環境変数とシークレット
- [API一覧](./PricingAIFrontend-develop%202/docs/api/APIList.md) - Databricks Jobs API仕様
- [Jobs接続](./PricingAIFrontend-develop%202/docs/development/JobsConnection.md) - Gradio⇔Databricks Jobs連携
- [コード規約](./PricingAIFrontend-develop%202/docs/development/frontend.rules.md) - フロントエンドコード規約

## 🏗️ アーキテクチャ

```
┌──────────────────────┐
│   Gradio Frontend    │  ← ユーザーインターフェース
│   (Python/Gradio)    │
└──────────┬───────────┘
           │
           │ Databricks Jobs API
           │ (REST)
           ▼
┌──────────────────────┐
│  Databricks Jobs     │  ← ワークフローオーケストレーション
│  (Notebooks)         │
└──────────┬───────────┘
           │
           │ Function Call
           ▼
┌──────────────────────┐
│   Spark ML Backend   │  ← 機械学習エンジン
│   (PySpark)          │
└──────────────────────┘
```

## 🔑 主要機能

### フロントエンド (Gradio UI)
- ✅ **トレーニングフォーム**: モデル学習の開始
- ✅ **予測フォーム**: 価格予測の実行
- ✅ **結果表示テーブル**: 予測結果の可視化とエクスポート
- ✅ **リアルタイム進捗確認**: ジョブ実行状況のモニタリング

### バックエンド (Spark ML)
- ✅ **価格予測モデル**: RandomForestベースの予測
- ✅ **特徴量エンジニアリング**: 15種類以上の特徴量
- ✅ **バッチ処理**: 複数店舗の並列予測
- ✅ **モデル管理**: トレーニング済みモデルの保存・読込

## 🛠️ 技術スタック

### フロントエンド
- **UI フレームワーク**: Gradio 5.44.1
- **言語**: Python 3.10+
- **HTTP クライアント**: requests
- **データ処理**: pandas, numpy

### バックエンド
- **ML フレームワーク**: Apache Spark ML
- **言語**: Python (PySpark)
- **モデル**: RandomForestClassifier
- **データ処理**: PySpark DataFrame

### インフラ
- **クラウド**: Azure Databricks
- **デプロイ**: Databricks Apps
- **CI/CD**: GitHub Actions
- **シークレット管理**: Databricks Secret Scope

## 🚦 開発ワークフロー

### 1. 新機能開発の流れ

```bash
# 1. Issue作成 (GitHub)
#    - 機能の説明
#    - 受け入れ基準
#    - 優先度設定

# 2. ブランチ作成
git checkout develop
git pull origin develop
git checkout -b feature/FE-001-NewFeature

# 3. 開発
#    - コード実装
#    - テスト追加
#    - ドキュメント更新

# 4. コミット
git add .
git commit -m "[#FE-001] 新機能の実装"

# 5. プッシュとPR作成
git push origin feature/FE-001-NewFeature
#    GitHub上でPull Requestを作成

# 6. レビュー・マージ
#    - コードレビュー
#    - CI/CDパイプライン確認
#    - developへマージ
```

詳細は [ブランチ戦略](./PricingAIFrontend-develop%202/docs/development/BranchStrategy.md) を参照。

### 2. デプロイフロー

```bash
# 開発環境: developブランチへのpushで自動デプロイ
git push origin develop
# → Databricks Apps (Development) へ自動デプロイ

# 本番環境: mainブランチへのマージで自動デプロイ
git checkout main
git merge develop
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main --tags
# → Databricks Apps (Production) へ自動デプロイ
```

詳細は [Databricks Apps設定](./PricingAIFrontend-develop%202/docs/development/DatabricksAppsSetup.md) を参照。

## 📊 重要な設計決定

### フロント・バック整合性
- **パラメータ命名**: 統一された命名規則
- **日付フォーマット**: YYYY-MM-DD 形式
- **特徴量リスト**: バックエンドと同期
- **バージョン管理**: セマンティックバージョニング

詳細は [整合性ガイド](./PricingAIFrontend-develop%202/docs/development/FrontendBackendConsistency.md) を参照。

### セキュリティ
- すべてのシークレットは Databricks Secret Scope で管理
- アクセストークンは定期的にローテーション
- 入力バリデーションの徹底
- API レート制限の実装

## 🧪 テスト

```bash
# ユニットテスト
pytest tests/unit/

# 統合テスト
pytest tests/integration/

# E2Eテスト
pytest tests/e2e/

# カバレッジ確認
pytest --cov=. --cov-report=html
```

## 📈 モニタリング

### ログ確認
```bash
# Databricks Apps のログ
databricks apps logs --app-name pricing-ai-frontend-production --tail 100

# リアルタイムログ
databricks apps logs --app-name pricing-ai-frontend-production --follow
```

### メトリクス
- レスポンス時間
- エラー率
- DBU 消費量
- モデル精度

## 🤝 貢献

### Issue作成
新機能やバグ報告は、[Issue](https://github.com/your-org/GRADIO-CLEANUP/issues) を作成してください。

Issue テンプレートは [Issue戦略](./PricingAIFrontend-develop%202/docs/development/DatabricksAppsIssueStrategy.md) を参照。

### Pull Request
Pull Request の作成前に、以下を確認してください:
- [ ] コード規約準拠
- [ ] テスト追加
- [ ] ドキュメント更新
- [ ] CI/CD パイプライン合格

PR テンプレートは [ブランチ戦略](./PricingAIFrontend-develop%202/docs/development/BranchStrategy.md) を参照。

## 📞 サポート

### 内部リソース
- **ドキュメント**: [STRATEGY.md](./STRATEGY.md)
- **サンプルコード**: `PricingAIFrontend-develop 2/components/`

### 外部リソース
- [Gradio 公式ドキュメント](https://www.gradio.app/docs)
- [Databricks Apps ドキュメント](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [Azure Databricks](https://learn.microsoft.com/ja-jp/azure/databricks/)

## 📄 ライセンス

[ライセンス情報をここに記載]

## 🎉 謝辞

PricingAI開発チームの皆様に感謝します。

---

**最終更新**: 2025-10-22
**バージョン**: 1.0.0
**メンテナー**: PricingAI Development Team
