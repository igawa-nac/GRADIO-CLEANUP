# Databricks notebook source
# MAGIC %run ./Sp_case.py

# COMMAND ----------

# MAGIC %run ./Sp_config.py

# COMMAND ----------

# MAGIC %run ./Sp_prep.py

# COMMAND ----------

# MAGIC %run ./Sp_feat.py

# COMMAND ----------

# MAGIC %run ./Sp_algo.py

# COMMAND ----------

# MAGIC %run ./Sp_fin.py

# COMMAND ----------

import time
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import joblib

# SparkSessionの初期化（必要に応じて）
# spark = SparkSession.builder.appName("ModelTraining").getOrCreate()

# jan_feats = ['pprice', 'aprice', 'dprice', 'dprice_pct',
#              'pscore_item', 'unitp_item',
#              'pscore_ucate', 'unitp_uid', 'pscore_ucate_dis050',
#              'r_jan', 'f_jan', 'm_jan', 
#              'rscore_jan', 'fscore_jan', 'mscore_jan', 'rfm_score_jan', 'rfm_score2_jan',
#              'jan_loy_m', 'jan_loy_f', 'jan_loy',
#              'kani_score', 'kani_score_dis025']

# jan_feats = ['pprice', 'aprice', 'dprice', 'dprice_pct',
#              'pscore_item', 'unitp_item',
#              'pscore_ucate', 'unitp_uid', 'pscore_ucate_dis050',
#              'r_jan', 'f_jan', 'm_jan', 
#              'rscore_jan', 'fscore_jan', 'mscore_jan', 'rfm_score_jan', 'rfm_score2_jan',
#              'jan_loy_m', 'jan_loy_f', 'jan_loy',
#              'kani_score', 'kani_score_dis025']

jan_feats = [
    "dprice","dprice_pct","rscore","fscore","mscore","rfm_score","rfm_score2",
    "jan_loy_m","jan_loy_f","jan_loy",
    "pscore_item","pscore_ucate","pscore_ucate_dis050",
    "kani_score","kani_score_dis025"
]

jan_label = 'label_jan'

# lv5_feats = ['pprice', 'aprice', 'dprice', 'dprice_pct',
#              'unitp_cate',
#              'pscore_ucate', 'unitp_uid', 'pscore_ucate_dis050',
#              'r_lv5', 'f_lv5', 'm_lv5', 
#              'rscore_lv5', 'fscore_lv5', 'mscore_lv5', 'rfm_score_lv5', 'rfm_score2_lv5',
#              'jan_loy_m', 'jan_loy_f', 'jan_loy',
#              'kani_score', 'kani_score_dis025']

lv5_feats = [
    "pprice", "aprice", "dprice", "dprice_pct",
    "unitp_cate",
    "pscore_ucate", "unitp_uid", "pscore_ucate_dis050",
    "f_lv5", "m_lv5",    
    "jan_loy_m", "jan_loy_f", "jan_loy",
    "kani_score", "kani_score_dis025"
]


lv5_label = 'label_lv5'

key_cols = ['store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'astart', 'pprice', 'uid', 'sample_amt_jan']


def train_model(case_period, stores, output_zero, output_up, verbose=False):
    """
    train a series of models (Spark版)
    """
    t0 = time.perf_counter()
    
    # ケースマスターの作成（Spark DataFrameとして）
    df_case0_list = [get_casemaster(case_period, istore, 'zero') for istore in stores]
    df_case1_list = [get_casemaster(case_period, istore, 'up') for istore in stores]
    
    # DataFrameをUNION
    df_case0 = df_case0_list[0]
    for df in df_case0_list[1:]:
        df_case0 = df_case0.union(df)
    
    df_case1 = df_case1_list[0]
    for df in df_case1_list[1:]:
        df_case1 = df_case1.union(df)
    
    if verbose: 
        print(f'case done. ({time.perf_counter() - t0:.2f} sec)')
        
    t0 = time.perf_counter()
    df_base0 = sample_uid(df_case0, label=True, case_period=case_period, stores=stores)
    df_base1 = sample_uid(df_case1, label=True, case_period=case_period, stores=stores)

    df_det0 = df_det.join(df_base0.select("jan","lv5_nm").distinct(), on="jan", how="left")
    df_det1 = df_det.join(df_base1.select("jan","lv5_nm").distinct(), on="jan", how="left")

    # df_base0 を Pandas に変換
    df_base0_pd = df_base0.toPandas()

    # df_base1 も同様
    df_base1_pd = df_base1.toPandas()

    df_base0_pd.to_csv(f'/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/df_base0.csv', index=False, encoding="utf-8-sig")
    df_base1_pd.to_csv(f'/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/df_base1.csv', index=False, encoding="utf-8-sig")
    if verbose: 
        print(f'sample done. ({time.perf_counter() - t0:.2f} sec)')
        

    # store ごとの期間を計算
    case_stats0 = df_base0.agg(
        F.min("astart").alias("min_astart"),
        F.max("astart").alias("max_astart")
    ).collect()[0]

    idpos_period0 = (
        strdoffset(case_stats0["min_astart"], -feature_len),
        case_stats0["max_astart"]
    )


    # idpos を事前取得
    df_idpos0 = fetch_idpos(
        salesday=idpos_period0,
        lv3_nm='洋日配',
        storecd=[row["store_cd"] for row in df_base0.select("store_cd").distinct().collect()]
    )


    # store ごとの期間を計算
    case_stats1 = df_base1.agg(
        F.min("astart").alias("min_astart"),
        F.max("astart").alias("max_astart")
    ).collect()[0]

    idpos_period1 = (
        strdoffset(case_stats1["min_astart"], -feature_len),
        case_stats1["max_astart"]
    )
    
    # idpos を事前取得
    df_idpos1 = fetch_idpos(
        salesday=idpos_period1,
        lv3_nm='洋日配',
        storecd=[row["store_cd"] for row in df_base1.select("store_cd").distinct().collect()]
    )


    t0 = time.perf_counter()
    #df_feat1 = add_features(df_base0, df_det)
    df_feat0 = add_features(df_base0, df_idpos0, df_det0)
    #df_feat1 = add_features(df_base1, df_det)
    df_feat1 = add_features(df_base1, df_idpos1, df_det1)

    # True/False → 1/0 に変換
    df_feat0 = df_feat0.withColumn("label_jan", F.col("label_jan").cast("integer"))
    df_feat1 = df_feat1.withColumn("label_jan", F.col("label_jan").cast("integer"))

    # 同じく lv5 のラベルも boolean なら数値化
    df_feat0 = df_feat0.withColumn("label_lv5", F.col("label_lv5").cast("integer"))
    df_feat1 = df_feat1.withColumn("label_lv5", F.col("label_lv5").cast("integer"))

    #--------------------デバッグ-----------------------
    # # 全件数
    # total_count = df_feat0.count()

    # # カラムごとの null 数と null 割合
    # null_stats = df_feat0.select([
    #     F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df_feat0.columns
    # ]).collect()[0].asDict()

    # # 表形式に整形
    # stats_df = spark.createDataFrame([
    #     (col, total_count, null_stats[col], null_stats[col] / total_count)
    #     for col in df_feat0.columns
    # ], ["column", "total_rows", "null_count", "null_ratio"])

    # stats_df.show(truncate=False)




    #     # 全件数
    # total_count1 = df_feat1.count()

    # # カラムごとの null 数と null 割合
    # null_stats1 = df_feat1.select([
    #     F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df_feat1.columns
    # ]).collect()[0].asDict()

    # # 表形式に整形
    # stats_df1 = spark.createDataFrame([
    #     (col, total_count1, null_stats1[col], null_stats1[col] / total_count1)
    #     for col in df_feat1.columns
    # ], ["column", "total_rows", "null_count", "null_ratio"])

    # stats_df1.show(truncate=False)
   #-------------------------------------------------

    df_feat0 = df_feat0.fillna(0)  # すべての null を 0 にする
    df_feat1 = df_feat1.fillna(0)  # すべての null を 0 にする


    if verbose: 
        print(f'feat done. ({time.perf_counter() - t0:.2f} sec)')
    
    t0 = time.perf_counter()
    
    # Spark MLのRandomForestClassifierを使用
    mdl0 = RandomForestClassifierPrice()
    mdl0.fit_jan(df_feat0, jan_feats, jan_label)
    mdl0.fit_lv5(df_feat0, lv5_feats, lv5_label)
    
    # モデルの保存（Spark MLモデルの場合）
    mdl0.save_model(output_zero)
    
    mdl1 = RandomForestClassifierPrice()
    mdl1.fit_jan(df_feat1, jan_feats, jan_label, [10, 20, 30, 40, 50], 16)
    mdl1.fit_lv5(df_feat1, lv5_feats, lv5_label, [10, 20, 30, 40, 50], 16)
    
    mdl1.save_model(output_up)
    
    if verbose: 
        print(f'model done. ({time.perf_counter() - t0:.2f} sec)')
        
    return


def predict_result(store_cd, upday, model_zero, model_up, item_file, drop_file, verbose=False):
    """
    predict neage result (Spark版)
    """
    t0 = time.perf_counter()
    
    # CSVファイルをSparkで読み込み
    df_item_mst = spark.read.csv(item_file, header=True, inferSchema=True)
    df_drop = spark.read.csv(drop_file, header=True, inferSchema=True)
    
    # アンチジョインでドロップアイテムを除外
    df_item_mst = df_item_mst.join(df_drop, on='jan', how='left_anti')
    
    if verbose: 
        print(f'master done. ({time.perf_counter() - t0:.2f} sec)')
    
    t0 = time.perf_counter()
    
    # JANリストを取得（collect()を使用）
    jan_list = df_item_mst.select('jan').rdd.flatMap(lambda x: x).collect()
    df_case = make_casemaster(store_cd, jan_list, upday, 0)
    
    if verbose: 
        print(f'case done. ({time.perf_counter() - t0:.2f} sec)')
        
    t0 = time.perf_counter()
    df_base = sample_uid(df_case, label=False)
    if verbose: 
        print(f'sample done. ({time.perf_counter() - t0:.2f} sec)')
        
    t0 = time.perf_counter()
    
    # 価格変更用のDataFrameを作成
    def _createdf(df_base, dprice):
        return df_base.withColumn('aprice', F.col('aprice') + F.lit(dprice))
    
    l_dp = [0] + dprice_range
    l_df = [_createdf(df_base, x) for x in l_dp]
    
    if verbose: 
        print(f'dprice split done. ({time.perf_counter() - t0:.2f} sec)')
        
    t0 = time.perf_counter()
    # jan, det_val.
    def load_det(kkk_file):
        """CSVをpandas→Sparkに変換してキャッシュ"""
        pdf_det = pd.read_csv(kkk_file)
        df_det = spark.createDataFrame(pdf_det).cache()
        df_det.count()  # キャッシュを実メモリに載せる
        return df_det

    kkk_file = './Data_beisia/kkk_master_20250626.csv'
    df_det = load_det(kkk_file)

    df_det = df_det.join(df_base.select("jan","lv5_nm").distinct(), on="jan", how="left")

        # store ごとの期間を計算
    case_stats = df_base.agg(
        F.min("astart").alias("min_astart"),
        F.max("astart").alias("max_astart")
    ).collect()[0]

    idpos_period = (
        strdoffset(case_stats["min_astart"], -feature_len),
        case_stats["max_astart"]
    )
    
    # idpos を事前取得
    df_idpos = fetch_idpos(
        salesday=idpos_period,
        lv3_nm='洋日配',
        storecd=[row["store_cd"] for row in df_base.select("store_cd").distinct().collect()]
    )


    l_df = [add_features(x, df_idpos, df_det) for x in l_df]
    if verbose: 
        print(f'feat done. ({time.perf_counter() - t0:.2f} sec)')
    
    t0 = time.perf_counter()
    
    # モデルの読み込み
    mdl0 = RandomForestClassifierPrice.load_model(model_zero)
    mdl1 = RandomForestClassifierPrice.load_model(model_up)
    
    # 予測結果のベースDataFrameを作成
    df_pred = l_df[0].select(*key_cols)
    
    # 予測実行
    df_pred_jan_0 = mdl0.predict_jan(l_df[0], jan_feats)
    df_pred_lv5_0 = mdl0.predict_lv5(l_df[0], lv5_feats)
    
    # 予測結果をjoin
    df_pred = df_pred.join(
        df_pred_jan_0.select(*key_cols, F.col('prediction').alias('prob_jan_0')), 
        on=key_cols, how='inner'
    ).join(
        df_pred_lv5_0.select(*key_cols, F.col('prediction').alias('prob_lv5_0')), 
        on=key_cols, how='inner'
    )
    
    # 各価格変更に対する予測
    for i in range(1, len(l_dp)):
        df_pred_jan_i = mdl1.predict_jan(l_df[i], jan_feats)
        df_pred_lv5_i = mdl1.predict_lv5(l_df[i], lv5_feats)
        
        df_pred = df_pred.join(
            df_pred_jan_i.select(*key_cols, F.col('prediction').alias(f'prob_jan_{l_dp[i]}')), 
            on=key_cols, how='inner'
        ).join(
            df_pred_lv5_i.select(*key_cols, F.col('prediction').alias(f'prob_lv5_{l_dp[i]}')), 
            on=key_cols, how='inner'
        )
    
    df_pred = fix_prob(df_pred)
    
    if verbose: 
        print(f'predict done. ({time.perf_counter() - t0:.2f} sec)')
    
    t0 = time.perf_counter()
    df_item, df_uid = calc_simu_result(df_pred, df_item_mst)
    if verbose: 
        print(f'calc done. ({time.perf_counter() - t0:.2f} sec)')
    
    return df_item, df_uid


class RandomForestClassifierPrice:
    """
    Spark ML用のRandomForestClassifierラッパークラス
    """
    def __init__(self):
        self.jan_model = None
        self.lv5_model = None
        self.jan_assembler = None
        self.lv5_assembler = None
    
    def fit_jan(self, df, features, label, param_grid=None, cv_folds=None):
        """
        JAN用モデルの学習
        """
        # 特徴量ベクトルの作成
        self.jan_assembler = VectorAssembler(
            inputCols=features,
            outputCol="features",
            handleInvalid="keep"
        )
        
        # RandomForestClassifierの作成
        rf = RandomForestClassifier(
            featuresCol="features",
            labelCol=label,
            predictionCol="prediction",
            probabilityCol="probability"
        )
        
        # パイプラインの作成
        pipeline = Pipeline(stages=[self.jan_assembler, rf])
        
        # モデルの学習
        self.jan_model = pipeline.fit(df)
    
    def fit_lv5(self, df, features, label, param_grid=None, cv_folds=None):
        """
        LV5用モデルの学習
        """
        # 特徴量ベクトルの作成
        self.lv5_assembler = VectorAssembler(
            inputCols=features,
            outputCol="features",
            handleInvalid="keep"
        )
        
        # RandomForestClassifierの作成
        rf = RandomForestClassifier(
            featuresCol="features",
            labelCol=label,
            predictionCol="prediction",
            probabilityCol="probability"
        )
        
        # パイプラインの作成
        pipeline = Pipeline(stages=[self.lv5_assembler, rf])
        
        # モデルの学習
        self.lv5_model = pipeline.fit(df)
    
    def predict_jan(self, df, features):
        """
        JAN用予測
        """
        return self.jan_model.transform(df)
    
    def predict_lv5(self, df, features):
        """
        LV5用予測
        """
        return self.lv5_model.transform(df)
    
    def save_model(self, path):
        """
        モデルの保存
        """
        if self.jan_model:
            self.jan_model.write().overwrite().save(f"{path}_jan")
        if self.lv5_model:
            self.lv5_model.write().overwrite().save(f"{path}_lv5")
    
    @classmethod
    def load_model(cls, path):
        """
        モデルの読み込み
        """
        from pyspark.ml import PipelineModel
        
        instance = cls()
        try:
            instance.jan_model = PipelineModel.load(f"{path}_jan")
            instance.lv5_model = PipelineModel.load(f"{path}_lv5")
        except Exception:
            # 従来のjoblibファイルの場合の処理
            instance = joblib.load(path)
        
        return instance


def fix_prob(df_pred):
    """
    確率の修正（Spark版）
    """
    # 確率値の範囲を0-1に制限
    prob_cols = [col for col in df_pred.columns if col.startswith('prob_')]
    
    for col in prob_cols:
        df_pred = df_pred.withColumn(
            col,
            F.when(F.col(col) < 0, 0)
             .when(F.col(col) > 1, 1)
             .otherwise(F.col(col))
        )
    
    return df_pred


def batch_predict_result(store_list, upday, model_zero, model_up, item_file, drop_file, batch_size=10, verbose=False):
    """
    複数店舗のバッチ予測処理
    """
    results = []
    
    for i in range(0, len(store_list), batch_size):
        batch_stores = store_list[i:i+batch_size]
        
        batch_results = []
        for store_cd in batch_stores:
            df_item, df_uid = predict_result(
                store_cd, upday, model_zero, model_up, 
                item_file, drop_file, verbose
            )
            batch_results.append((df_item, df_uid))
        
        # バッチ結果をUNION
        if batch_results:
            all_items = batch_results[0][0]
            all_uids = batch_results[0][1]
            
            for item_result, uid_result in batch_results[1:]:
                all_items = all_items.union(item_result)
                all_uids = all_uids.union(uid_result)
            
            results.append((all_items, all_uids))
    
    return results
