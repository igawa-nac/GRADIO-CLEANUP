# ブランチ戦略 - Databricks Apps & Gradio UI開発

## 概要
このドキュメントでは、Databricks AppsとGradio UIを開発する際のブランチ戦略について説明します。Git Flowをベースに、Databricks Apps特有の要件を考慮した戦略を採用します。

## ブランチ構造

```
main (本番環境)
  │
  └── develop (開発環境)
        ├── feature/* (機能開発)
        ├── bugfix/* (バグ修正)
        ├── hotfix/* (緊急修正)
        ├── release/* (リリース準備)
        └── experiment/* (実験的機能)
```

## 主要ブランチ

### 1. main ブランチ
**目的**: 本番環境へのデプロイ用

**特徴**:
- 常に本番環境と同期
- 直接コミット禁止
- release/* または hotfix/* からのみマージ可能
- マージ時は必ずタグを付与

**保護ルール**:
- Pull Requestによるマージのみ許可
- 最低1名以上のレビュー承認必須
- すべてのテスト合格必須
- 管理者のみマージ可能

**Databricks Apps連携**:
```bash
# mainブランチへのマージ後、本番環境へ自動デプロイ
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags
# → Databricks Apps (Production) へ自動デプロイ
```

### 2. develop ブランチ
**目的**: 開発統合ブランチ

**特徴**:
- 開発環境と同期
- feature/* からのマージ先
- 直接コミットは基本的に禁止(ドキュメント更新は例外)
- 定期的に main へマージ

**保護ルール**:
- Pull Requestによるマージ推奨
- 1名以上のレビュー承認推奨
- CI/CDテスト合格必須

**Databricks Apps連携**:
```bash
# developブランチへのマージ後、開発環境へ自動デプロイ
git push origin develop
# → Databricks Apps (Development) へ自動デプロイ
```

## 作業用ブランチ

### 3. feature/* ブランチ
**目的**: 新機能開発

**命名規則**:
```
feature/{issue-number}-{short-description}

例:
feature/FE-001-TrainingForm
feature/API-001-JobsIntegration
feature/ML-001-ModelTraining
```

**作成方法**:
```bash
# developブランチから作成
git checkout develop
git pull origin develop
git checkout -b feature/FE-001-TrainingForm
```

**マージ先**: develop ブランチ

**ライフサイクル**:
1. develop から分岐
2. 機能開発
3. Pull Request作成
4. コードレビュー
5. develop へマージ
6. ブランチ削除

**コミット例**:
```bash
git commit -m "[#FE-001] トレーニングフォームのUI実装"
git commit -m "[#FE-001] バリデーション機能追加"
git commit -m "[#FE-001] ユニットテスト追加"
```

### 4. bugfix/* ブランチ
**目的**: バグ修正

**命名規則**:
```
bugfix/{issue-number}-{short-description}

例:
bugfix/123-FixDatePicker
bugfix/456-FixAPITimeout
```

**作成方法**:
```bash
git checkout develop
git pull origin develop
git checkout -b bugfix/123-FixDatePicker
```

**マージ先**: develop ブランチ

### 5. hotfix/* ブランチ
**目的**: 本番環境の緊急バグ修正

**命名規則**:
```
hotfix/{version}-{short-description}

例:
hotfix/v1.0.1-CriticalBugFix
hotfix/v1.0.2-SecurityPatch
```

**作成方法**:
```bash
# mainブランチから作成
git checkout main
git pull origin main
git checkout -b hotfix/v1.0.1-CriticalBugFix
```

**マージ先**: main および develop の両方

**手順**:
```bash
# 1. hotfixブランチで修正
git commit -m "[HOTFIX] 緊急バグ修正"

# 2. mainへマージ
git checkout main
git merge --no-ff hotfix/v1.0.1-CriticalBugFix
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin main --tags

# 3. developへマージ
git checkout develop
git merge --no-ff hotfix/v1.0.1-CriticalBugFix
git push origin develop

# 4. hotfixブランチ削除
git branch -d hotfix/v1.0.1-CriticalBugFix
```

### 6. release/* ブランチ
**目的**: リリース準備

**命名規則**:
```
release/{version}

例:
release/v1.0.0
release/v1.1.0
```

**作成方法**:
```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0
```

**作業内容**:
- バージョン番号更新
- リリースノート作成
- 最終テスト
- バグ修正(軽微なもののみ)

**マージ先**: main および develop の両方

**手順**:
```bash
# 1. リリース準備
git commit -m "[RELEASE] v1.0.0 準備"

# 2. mainへマージ
git checkout main
git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main --tags

# 3. developへマージ
git checkout develop
git merge --no-ff release/v1.0.0
git push origin develop

# 4. releaseブランチ削除
git branch -d release/v1.0.0
```

### 7. experiment/* ブランチ
**目的**: 実験的機能の開発

**命名規則**:
```
experiment/{description}

例:
experiment/NewMLAlgorithm
experiment/AlternativeUI
```

**特徴**:
- 本番採用が不確定な機能
- POC(Proof of Concept)実装
- developへのマージは慎重に判断

## ブランチ運用ルール

### コミットメッセージ規約

```
[{prefix}] {message}

prefix:
- #FE-XXX: フロントエンド関連
- #API-XXX: API関連
- #ML-XXX: 機械学習関連
- #DATA-XXX: データ関連
- #DOC-XXX: ドキュメント関連
- #TEST-XXX: テスト関連
- HOTFIX: 緊急修正
- RELEASE: リリース関連

例:
[#FE-001] トレーニングフォームのUI実装
[#API-001] Databricks Jobs API統合
[#ML-001] 特徴量エンジニアリング追加
[HOTFIX] 認証エラーの修正
```

### Pull Request作成ルール

#### 1. PRタイトル
```
[{type}] {short-description}

例:
[Feature] トレーニングフォームの実装
[Bugfix] DatePickerのバグ修正
[Hotfix] 認証エラーの緊急修正
```

#### 2. PR説明テンプレート
```markdown
## 関連Issue
Closes #{issue-number}

## 変更内容
- 変更1の説明
- 変更2の説明

## スクリーンショット(該当する場合)
![image](url)

## テスト内容
- [ ] ユニットテスト実施
- [ ] 統合テスト実施
- [ ] 手動テスト実施
- [ ] Databricks Apps動作確認

## チェックリスト
- [ ] コード規約準拠
- [ ] テスト追加/更新
- [ ] ドキュメント更新
- [ ] CHANGELOG更新
- [ ] レビュー依頼完了

## Databricks Apps固有の確認事項
- [ ] シークレット管理は適切か
- [ ] DBU消費は妥当か
- [ ] スケーラビリティ考慮済みか
- [ ] セキュリティ考慮済みか
```

### レビュープロセス

#### レビュー観点
1. **機能性**: 要件を満たしているか
2. **コード品質**: 可読性、保守性
3. **テスト**: 十分なテストカバレッジか
4. **セキュリティ**: 脆弱性はないか
5. **パフォーマンス**: パフォーマンスへの影響
6. **Databricks Apps**: Databricks Apps特有の考慮事項

#### レビュー承認基準
- **feature/bugfix**: 最低1名の承認
- **release**: 最低2名の承認
- **hotfix**: 最低1名の承認(緊急時は事後承認可)

## Databricks Apps環境とブランチのマッピング

| ブランチ | Databricks Apps環境 | 用途 | 自動デプロイ |
|---------|-------------------|------|------------|
| main | Production | 本番環境 | ✓ |
| develop | Development | 開発環境 | ✓ |
| feature/* | - | ローカル開発 | ✗ |
| release/* | Staging | リリーステスト | ✓ |
| hotfix/* | - | 緊急修正 | ✗ |

### 環境別設定ファイル

```
config/
  ├── .env.production      # 本番環境
  ├── .env.development     # 開発環境
  ├── .env.staging         # ステージング環境
  └── .env.local.example   # ローカル開発用テンプレート
```

## CI/CD統合

### GitHub Actions ワークフロー例

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
      - uses: actions/checkout@v2

      - name: Set environment
        run: |
          if [ "${{ github.ref }}" == "refs/heads/main" ]; then
            echo "ENV=production" >> $GITHUB_ENV
          else
            echo "ENV=development" >> $GITHUB_ENV
          fi

      - name: Deploy to Databricks Apps
        run: |
          # Databricks CLIを使用してデプロイ
          databricks apps deploy \
            --app-name pricing-ai-frontend-${{ env.ENV }} \
            --source-dir ./PricingAIFrontend-develop\ 2
```

## トラブルシューティング

### ブランチが古くなった場合
```bash
# developの最新を取得
git checkout develop
git pull origin develop

# featureブランチにマージ
git checkout feature/FE-001-TrainingForm
git merge develop

# コンフリクト解決後
git add .
git commit -m "Merge develop into feature/FE-001-TrainingForm"
git push origin feature/FE-001-TrainingForm
```

### 誤ったブランチでコミットした場合
```bash
# 変更を退避
git stash

# 正しいブランチに切り替え
git checkout correct-branch

# 変更を適用
git stash pop

# コミット
git add .
git commit -m "正しいブランチでのコミット"
```

### コンフリクト解決
```bash
# マージ実行
git merge develop

# コンフリクトファイルを手動編集後
git add <conflicted-files>
git commit -m "Resolve merge conflicts"
```

## ベストプラクティス

### 1. 小さく頻繁にコミット
```bash
# 良い例
git commit -m "[#FE-001] フォーム構造の実装"
git commit -m "[#FE-001] バリデーション追加"
git commit -m "[#FE-001] スタイリング調整"

# 悪い例
git commit -m "[#FE-001] すべての変更"
```

### 2. 定期的にdevelopと同期
```bash
# 1日1回はdevelopの最新を取り込む
git checkout feature/FE-001-TrainingForm
git fetch origin
git merge origin/develop
```

### 3. Pushする前にテスト実行
```bash
# テスト実行
pytest tests/

# Lintチェック
ruff check .

# Pushできる場合のみpush
git push origin feature/FE-001-TrainingForm
```

### 4. ブランチは短命に
- 目安: 1週間以内にマージ
- 長期化する場合: 機能を分割

### 5. ブランチ削除は定期的に
```bash
# マージ済みブランチの確認
git branch --merged

# ローカルブランチ削除
git branch -d feature/FE-001-TrainingForm

# リモートブランチ削除
git push origin --delete feature/FE-001-TrainingForm
```

## まとめ

このブランチ戦略により、以下が実現できます:
- 安全な本番環境の維持
- 並行開発の効率化
- コードレビューの標準化
- Databricks Appsへの自動デプロイ
- トレーサビリティの確保

ブランチ戦略を遵守し、チーム全体で一貫した開発フローを維持してください。
