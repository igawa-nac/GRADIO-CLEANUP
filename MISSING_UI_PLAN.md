# 未実装UI開発計画 - PricingAI Gradio UI

## 📊 現状分析結果

### ✅ 既に実装されているUI

| コンポーネント | 機能 | カバーするパラメータ |
|------------|------|------------------|
| **TrainingForm** | モデル学習 | case_period (開始日・終了日), stores |
| **PredictionForm** | 予測実行 | store_cd, upday |
| **SelectableTable** | 結果表示 | - |

### ❌ 未実装のパラメータ（PricingAI_Spark-mainとの整合性確認結果）

#### A. **必須ファイルパス** (現在ハードコード)
Sp_config.py, Sp_interface.pyで使用:

| パラメータ | 現在の値 | 用途 | 必要性 |
|-----------|---------|------|-------|
| `kkk_file` | `'./Data_beisia/kkk_master_20250903.csv'` | 商品詳細マスター | **必須** |
| `series_file` | `'./Data_beisia/series_mst_20250626.csv'` | シリーズマスター | **必須** |
| `item_file` | - | 予測対象商品マスター | **必須** |
| `drop_file` | - | 除外商品リスト | **必須** |
| `output_zero` | - | ゼロモデル保存パス | **必須** |
| `output_up` | - | アップモデル保存パス | **必須** |

#### B. **予測範囲設定**

| パラメータ | 現在の値 | 用途 | 必要性 |
|-----------|---------|------|-------|
| `dprice_range` | `[10, 20, 30]` | 予測する値上げ額の範囲 | **高** |

#### C. **期間パラメータ**

| パラメータ | 現在の値 | 用途 | 必要性 |
|-----------|---------|------|-------|
| `thd_plen` | `75` | 単一価格の前期間日数 | 中 |
| `thd_alen` | `45` | 単一価格の後期間日数 | 中 |
| `interval_len` | `7` | インターバル長 | 低 |
| `feature_len` | `63` | 特徴量計算期間 | 低 |
| `sample_len` | `28` | サンプル期間 | 低 |
| `label_len` | `28` | ラベル期間 | 低 |

#### D. **シミュレーション閾値**

| パラメータ | 現在の値 | 用途 | 必要性 |
|-----------|---------|------|-------|
| `simu_thd_retainr` | `-0.9` | リテンション率閾値 | **高** |
| `simu_thd_amtchanger` | `-0.9` | 売上変化率閾値 | **高** |
| `max_price_cnt` | `2` | 同一シリーズ最大価格数 | 中 |

#### E. **ノイズ・スコア調整**

| パラメータ | 現在の値 | 用途 | 必要性 |
|-----------|---------|------|-------|
| `noise_max_cnt` | `6` | ノイズ最大カウント | 低 |
| `pscore_modify_ndays` | `6` | スコア修正日数 | 低 |
| `pscore_multipkg_thd` | `1200` | 複数パッケージ閾値 | 低 |
| `pscore_mod_lv5` | `{...}` | カテゴリ別閾値辞書 | 低 |

#### F. **モデルハイパーパラメータ (RandomForest)**

**JAN用モデル**:
- `n_estimators`: 80
- `min_samples_split`: 90
- `min_samples_leaf`: 40
- `random_state`: 100
- `n_jobs`: 4

**LV5用モデル**:
- `n_estimators`: 80
- `min_samples_split`: 160
- `min_samples_leaf`: 70
- `random_state`: 100
- `n_jobs`: 4

必要性: 中

#### G. **固定パラメータ**

| パラメータ | 現在の値 | 用途 | 必要性 |
|-----------|---------|------|-------|
| `fix_same_dprice` | `0.000` | 同一値引き額補正 | 低 |
| `fix_same_type_lv5` | `0.008` | 同一タイプLV5補正 | 低 |
| `fix_same_type_jan` | `0.028` | 同一タイプJAN補正 | 低 |

---

## 🎯 未実装UI開発計画（優先度順）

### Phase 1: 必須パラメータUI (P0) - 最優先

#### 1.1 **ファイル管理UI** (FileManagementForm)

**目的**: データファイルとモデル保存先の指定

**実装内容**:
```python
# components/forms/FileManagementForm.py
import gradio as gr
from settings import *

def FileManagementForm():
    gr.Markdown("## ファイル設定")

    with gr.Accordion("データファイル", open=True):
        kkk_file_input = gr.Textbox(
            label="商品詳細マスターファイル (kkk_file)",
            value="/dbfs/mnt/data/kkk_master_20250903.csv",
            placeholder="/dbfs/mnt/data/kkk_master_YYYYMMDD.csv"
        )

        series_file_input = gr.Textbox(
            label="シリーズマスターファイル (series_file)",
            value="/dbfs/mnt/data/series_mst_20250626.csv",
            placeholder="/dbfs/mnt/data/series_mst_YYYYMMDD.csv"
        )

        item_file_input = gr.Textbox(
            label="商品マスターファイル (item_file) - 予測用",
            value="/dbfs/mnt/data/item_master.csv",
            placeholder="/dbfs/mnt/data/item_master.csv"
        )

        drop_file_input = gr.Textbox(
            label="除外商品ファイル (drop_file) - 予測用",
            value="/dbfs/mnt/data/drop_items.csv",
            placeholder="/dbfs/mnt/data/drop_items.csv"
        )

    with gr.Accordion("モデル保存先", open=True):
        output_zero_input = gr.Textbox(
            label="ゼロモデル保存パス (output_zero)",
            value="/dbfs/mnt/models/pricing_ai/model_zero",
            placeholder="/dbfs/mnt/models/pricing_ai/model_zero"
        )

        output_up_input = gr.Textbox(
            label="アップモデル保存パス (output_up)",
            value="/dbfs/mnt/models/pricing_ai/model_up",
            placeholder="/dbfs/mnt/models/pricing_ai/model_up"
        )

    # ファイル存在確認ボタン（オプション）
    validate_btn = gr.Button("ファイル存在確認")
    validation_output = gr.Textbox(
        label="確認結果",
        lines=3,
        interactive=False
    )

    validate_btn.click(
        fn=validate_files,
        inputs=[kkk_file_input, series_file_input, item_file_input, drop_file_input],
        outputs=validation_output
    )

    return {
        "kkk_file": kkk_file_input,
        "series_file": series_file_input,
        "item_file": item_file_input,
        "drop_file": drop_file_input,
        "output_zero": output_zero_input,
        "output_up": output_up_input
    }


def validate_files(kkk_file, series_file, item_file, drop_file):
    """ファイル存在確認"""
    import os

    files = {
        "商品詳細マスター": kkk_file,
        "シリーズマスター": series_file,
        "商品マスター": item_file,
        "除外商品": drop_file
    }

    results = []
    for name, path in files.items():
        if path and os.path.exists(path):
            results.append(f"✅ {name}: 存在")
        elif path:
            results.append(f"❌ {name}: 存在しません")
        else:
            results.append(f"⚠️ {name}: 未指定")

    return "\n".join(results)
```

**所要時間**: 2-3時間

**チェックリスト**:
- [ ] FileManagementForm.py 作成
- [ ] validate_files() 関数実装
- [ ] app.pyに統合
- [ ] TrainingForm, PredictionFormとの連携確認

---

### Phase 2: 高優先パラメータUI (P1)

#### 2.1 **予測設定UI** (PredictionSettingsForm)

**目的**: 予測価格範囲とシミュレーション閾値の設定

**実装内容**:
```python
# components/forms/PredictionSettingsForm.py
import gradio as gr

def PredictionSettingsForm():
    gr.Markdown("## 予測設定")

    with gr.Accordion("価格範囲設定", open=True):
        gr.Markdown("値上げ額の範囲を設定してください（カンマ区切り）")
        dprice_range_input = gr.Textbox(
            label="値上げ額範囲 (dprice_range)",
            value="10,20,30",
            placeholder="10,20,30"
        )
        gr.Markdown("*例: 10,20,30 → 10円、20円、30円の値上げを予測*")

    with gr.Accordion("シミュレーション閾値", open=False):
        simu_thd_retainr_input = gr.Slider(
            minimum=-1.0,
            maximum=0.0,
            value=-0.9,
            step=0.05,
            label="リテンション率閾値 (simu_thd_retainr)",
            info="顧客維持率の最小値 (推奨: -0.9 ~ -0.5)"
        )

        simu_thd_amtchanger_input = gr.Slider(
            minimum=-1.0,
            maximum=0.0,
            value=-0.9,
            step=0.05,
            label="売上変化率閾値 (simu_thd_amtchanger)",
            info="売上変化率の最小値 (推奨: -0.9 ~ -0.5)"
        )

        max_price_cnt_input = gr.Number(
            value=2,
            label="同一シリーズ最大価格数 (max_price_cnt)",
            minimum=1,
            maximum=5,
            step=1,
            info="同一シリーズで設定できる価格の最大数"
        )

    return {
        "dprice_range": dprice_range_input,
        "simu_thd_retainr": simu_thd_retainr_input,
        "simu_thd_amtchanger": simu_thd_amtchanger_input,
        "max_price_cnt": max_price_cnt_input
    }
```

**所要時間**: 1-2時間

**チェックリスト**:
- [ ] PredictionSettingsForm.py 作成
- [ ] dprice_rangeの文字列→リスト変換関数実装
- [ ] バリデーション機能追加
- [ ] app.pyに統合

---

### Phase 3: 中優先パラメータUI (P2)

#### 3.1 **高度な設定UI** (AdvancedSettingsForm)

**目的**: 期間パラメータとモデルハイパーパラメータの調整

**実装内容**:
```python
# components/forms/AdvancedSettingsForm.py
import gradio as gr

def AdvancedSettingsForm():
    gr.Markdown("## 高度な設定")

    with gr.Accordion("期間パラメータ", open=False):
        thd_plen_input = gr.Number(
            value=75,
            label="前期間日数 (thd_plen)",
            minimum=30,
            maximum=120,
            step=1,
            info="単一価格の前期間日数"
        )

        thd_alen_input = gr.Number(
            value=45,
            label="後期間日数 (thd_alen)",
            minimum=20,
            maximum=90,
            step=1,
            info="単一価格の後期間日数"
        )

        feature_len_input = gr.Number(
            value=63,
            label="特徴量計算期間 (feature_len)",
            minimum=28,
            maximum=90,
            step=7
        )

        sample_len_input = gr.Number(
            value=28,
            label="サンプル期間 (sample_len)",
            minimum=14,
            maximum=56,
            step=7
        )

    with gr.Accordion("モデルハイパーパラメータ", open=False):
        gr.Markdown("### JANモデル")

        jan_n_estimators_input = gr.Slider(
            minimum=50,
            maximum=200,
            value=80,
            step=10,
            label="決定木数 (n_estimators)"
        )

        jan_min_samples_split_input = gr.Slider(
            minimum=20,
            maximum=200,
            value=90,
            step=10,
            label="分割最小サンプル数 (min_samples_split)"
        )

        jan_min_samples_leaf_input = gr.Slider(
            minimum=10,
            maximum=100,
            value=40,
            step=5,
            label="葉の最小サンプル数 (min_samples_leaf)"
        )

        gr.Markdown("### LV5モデル")

        lv5_n_estimators_input = gr.Slider(
            minimum=50,
            maximum=200,
            value=80,
            step=10,
            label="決定木数 (n_estimators)"
        )

        lv5_min_samples_split_input = gr.Slider(
            minimum=50,
            maximum=300,
            value=160,
            step=10,
            label="分割最小サンプル数 (min_samples_split)"
        )

        lv5_min_samples_leaf_input = gr.Slider(
            minimum=20,
            maximum=150,
            value=70,
            step=5,
            label="葉の最小サンプル数 (min_samples_leaf)"
        )

    return {
        "thd_plen": thd_plen_input,
        "thd_alen": thd_alen_input,
        "feature_len": feature_len_input,
        "sample_len": sample_len_input,
        "jan_params": {
            "n_estimators": jan_n_estimators_input,
            "min_samples_split": jan_min_samples_split_input,
            "min_samples_leaf": jan_min_samples_leaf_input
        },
        "lv5_params": {
            "n_estimators": lv5_n_estimators_input,
            "min_samples_split": lv5_min_samples_split_input,
            "min_samples_leaf": lv5_min_samples_leaf_input
        }
    }
```

**所要時間**: 2-3時間

**チェックリスト**:
- [ ] AdvancedSettingsForm.py 作成
- [ ] パラメータバリデーション実装
- [ ] デフォルト値リセット機能追加
- [ ] app.pyに統合

---

### Phase 4: UI統合とデータフロー

#### 4.1 **設定管理システム**

**実装内容**:
```python
# lib/config/config_manager.py
import json
import os

class ConfigManager:
    """設定の保存・読み込み管理"""

    def __init__(self, config_file="config/ui_config.json"):
        self.config_file = config_file

    def save_config(self, config_dict):
        """
        設定を保存

        Parameters:
        -----------
        config_dict : dict
            保存する設定
        """
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

    def load_config(self):
        """
        設定を読み込み

        Returns:
        --------
        dict
            読み込んだ設定
        """
        if not os.path.exists(self.config_file):
            return self.get_default_config()

        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def get_default_config():
        """デフォルト設定を取得"""
        return {
            "files": {
                "kkk_file": "/dbfs/mnt/data/kkk_master_20250903.csv",
                "series_file": "/dbfs/mnt/data/series_mst_20250626.csv",
                "item_file": "/dbfs/mnt/data/item_master.csv",
                "drop_file": "/dbfs/mnt/data/drop_items.csv",
                "output_zero": "/dbfs/mnt/models/pricing_ai/model_zero",
                "output_up": "/dbfs/mnt/models/pricing_ai/model_up"
            },
            "prediction": {
                "dprice_range": [10, 20, 30],
                "simu_thd_retainr": -0.9,
                "simu_thd_amtchanger": -0.9,
                "max_price_cnt": 2
            },
            "advanced": {
                "thd_plen": 75,
                "thd_alen": 45,
                "feature_len": 63,
                "sample_len": 28,
                "jan_params": {
                    "n_estimators": 80,
                    "min_samples_split": 90,
                    "min_samples_leaf": 40
                },
                "lv5_params": {
                    "n_estimators": 80,
                    "min_samples_split": 160,
                    "min_samples_leaf": 70
                }
            }
        }
```

**所要時間**: 1-2時間

#### 4.2 **app.py の更新**

**実装内容**:
```python
# app.py (更新版)
from components.layouts.MainLayout import MainLayout
from components.tables.SelectableTable import SelectableTable
from components.forms.PredictionForm import PredictionForm
from components.forms.TrainingForm import TrainingForm
from components.forms.FileManagementForm import FileManagementForm
from components.forms.PredictionSettingsForm import PredictionSettingsForm
from components.forms.AdvancedSettingsForm import AdvancedSettingsForm
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
    gr.Markdown("# PricingAI - 価格予測システム")

    with gr.Tabs():
        with gr.Tab("基本設定"):
            file_components = FileManagementForm()

        with gr.Tab("学習"):
            TrainingForm()

        with gr.Tab("予測"):
            PredictionForm()

        with gr.Tab("予測設定"):
            prediction_components = PredictionSettingsForm()

        with gr.Tab("高度な設定"):
            advanced_components = AdvancedSettingsForm()

        with gr.Tab("結果表示"):
            SelectableTable(checkbox_demo_data)

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

**所要時間**: 1-2時間

---

## 📅 実装スケジュール

| Phase | 内容 | 所要時間 | 優先度 |
|-------|------|---------|-------|
| **Phase 1** | ファイル管理UI | 2-3時間 | P0 (必須) |
| **Phase 2** | 予測設定UI | 1-2時間 | P1 (高) |
| **Phase 3** | 高度な設定UI | 2-3時間 | P2 (中) |
| **Phase 4** | UI統合 | 2-3時間 | P2 (中) |
| **合計** | - | **7-11時間** | - |

### 推奨実装順序

**Week 1**: Phase 1 (必須パラメータ)
- Day 1-2: FileManagementForm実装
- Day 3: TrainingForm/PredictionFormとの統合

**Week 2**: Phase 2 (高優先パラメータ)
- Day 1: PredictionSettingsForm実装
- Day 2: バリデーションとテスト

**Week 3**: Phase 3-4 (中優先パラメータと統合)
- Day 1-2: AdvancedSettingsForm実装
- Day 3: ConfigManager実装と全体統合
- Day 4: テストとバグ修正

---

## 🎯 実装後の最終UI構成

```
PricingAI Gradio UI
├── Tab 1: 基本設定
│   ├── データファイル設定
│   │   ├── kkk_file (商品詳細マスター)
│   │   ├── series_file (シリーズマスター)
│   │   ├── item_file (商品マスター)
│   │   └── drop_file (除外商品)
│   └── モデル保存先
│       ├── output_zero
│       └── output_up
│
├── Tab 2: 学習
│   ├── 取得期間
│   └── 対象店舗
│
├── Tab 3: 予測
│   ├── 対象店舗
│   └── 予測日
│
├── Tab 4: 予測設定 ← 🆕
│   ├── 値上げ額範囲 (dprice_range)
│   └── シミュレーション閾値
│
├── Tab 5: 高度な設定 ← 🆕
│   ├── 期間パラメータ
│   └── モデルハイパーパラメータ
│
└── Tab 6: 結果表示
    └── 予測結果テーブル
```

---

## 📋 チェックリスト

### Phase 1: ファイル管理UI
- [ ] `components/forms/FileManagementForm.py` 作成
- [ ] ファイル存在確認機能実装
- [ ] デフォルト値設定
- [ ] app.pyに統合
- [ ] 動作確認

### Phase 2: 予測設定UI
- [ ] `components/forms/PredictionSettingsForm.py` 作成
- [ ] dprice_range入力バリデーション
- [ ] スライダーUI実装
- [ ] app.pyに統合
- [ ] 動作確認

### Phase 3: 高度な設定UI
- [ ] `components/forms/AdvancedSettingsForm.py` 作成
- [ ] 期間パラメータUI実装
- [ ] モデルハイパーパラメータUI実装
- [ ] app.pyに統合
- [ ] 動作確認

### Phase 4: UI統合
- [ ] `lib/config/config_manager.py` 作成
- [ ] 設定保存・読み込み機能
- [ ] TrainingForm/PredictionFormとの連携
- [ ] Databricks Notebookへのパラメータ渡し
- [ ] E2Eテスト

---

## 💡 実装のポイント

### 1. Gradioのタブ構成
既存の1画面構成から、タブベースの構成に変更することで、UIを整理し、使いやすくします。

### 2. デフォルト値の管理
すべてのパラメータにデフォルト値を設定し、初心者でもすぐに使えるようにします。

### 3. バリデーション
入力値のバリデーションを徹底し、エラーメッセージをわかりやすく表示します。

### 4. 設定の永続化
ConfigManagerで設定を保存し、次回起動時に前回の設定を復元します。

### 5. Databricks Notebookとの連携
すべてのパラメータをJSON形式で Databricks Notebook に渡せるようにします。

```python
# Databricks Notebookへの渡し方
notebook_params = {
    # ファイルパス
    "kkk_file": kkk_file,
    "series_file": series_file,
    # 予測設定
    "dprice_range": ",".join(map(str, dprice_range)),
    "simu_thd_retainr": str(simu_thd_retainr),
    # その他...
}
```

---

## 🚀 今すぐ着手すべき最優先タスク

### ステップ1: FileManagementForm作成 (2時間)
```bash
# 1. ファイル作成
touch "PricingAIFrontend-develop 2/components/forms/FileManagementForm.py"

# 2. 上記のコード例をコピー

# 3. app.pyに統合
```

### ステップ2: 動作確認 (30分)
```bash
python app.py
# ブラウザでhttp://localhost:7860にアクセス
```

### ステップ3: PredictionSettingsForm作成 (1時間)
```bash
touch "PricingAIFrontend-develop 2/components/forms/PredictionSettingsForm.py"
```

これで**必須パラメータと高優先パラメータのUIが完成**し、PricingAI_Spark-mainのすべての変数を Gradio UI から設定できるようになります！

---

すべての詳細仕様とサンプルコードを含めた開発計画書を作成しました。この計画に従えば、7-11時間で完全なUI実装が可能です。
