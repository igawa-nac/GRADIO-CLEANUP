# Databricks notebook source
# MAGIC %run ./Sp_config.py

# COMMAND ----------

# from pyspark.sql import SparkSession, functions as F
# from pyspark.sql.types import *
# from pyspark.sql.window import Window
# import pandas as pd
# import numpy as np

# # dprice_rangeをソート
# dprice_range = sorted(dprice_range)

# def calc_simu_result(df_pred, df_item_mst):
#     """
#     Spark版シミュレーション結果計算
    
#     Parameters
#     ----------
#     df_pred: Spark DataFrame
#         columns = key_cols + ['prob_jan_x', 'prob_lv5_x', ...]
#     df_item_mst: Spark DataFrame
#         columns=['jan', 'name', 'oprice', 'max_dprice']
    
#     Returns
#     -------
#     tuple: (df_item, df_uid)
#     """

#     # null埋め
#     df_pred = df_pred.fillna(0)
#     df_item_mst = df_item_mst.fillna(0)
#     # マージと基本計算
#     df_calc = df_pred.join(df_item_mst, on='jan', how='left')
    
#     # 基本計算をベクトル化
#     df_calc = (df_calc
#                .withColumn('cnt', F.floor(F.col('sample_amt_jan') / F.col('pprice')))
#                #.withColumn('cnt', F.col('sample_amt_jan') / F.col('pprice'))
#                .withColumn('prof_pre', F.col('cnt') * (F.col('pprice') - F.col('oprice'))))
    
#     # 全価格に対する変化計算
#     df_calc = _calculate_changes(df_calc)
    
#     # UID結果とアイテム結果を生成
#     df_uid = _create_uid_result(df_calc)
#     df_item = _create_item_result(df_uid)
    
#     return df_item, df_uid


# def _calculate_changes(df_calc):
#     """
#     Spark版全価格変更に対する変化計算
#     """
#     # 基準値（dp=0）の計算
#     df_calc = (df_calc
#                .withColumn('prof_ch_0', 
#                           (F.col('prob_jan_0') * 0 - (1 - F.col('prob_lv5_0')) * 
#                            (F.col('pprice') - F.col('oprice'))) * F.col('cnt'))
#                .withColumn('amt_ch_0',
#                           (F.col('prob_jan_0') * 0 - (1 - F.col('prob_lv5_0')) * 
#                            F.col('pprice')) * F.col('cnt')))
    
#     # 各価格変更に対する計算
#     for dp in dprice_range:
#         prob_jan_col = f'prob_jan_{dp}'
#         prob_lv5_col = f'prob_lv5_{dp}'
        
#         # 変化の計算
#         df_calc = (df_calc
#                    .withColumn(f'prof_ch_{dp}_temp',
#                               (F.col(prob_jan_col) * dp - (1 - F.col(prob_lv5_col)) * 
#                                (F.col('pprice') - F.col('oprice'))) * F.col('cnt'))
#                    .withColumn(f'amt_ch_{dp}_temp',
#                               (F.col(prob_jan_col) * dp - (1 - F.col(prob_lv5_col)) * 
#                                F.col('pprice')) * F.col('cnt'))
#                    .withColumn(f'prof_ch_{dp}', 
#                               F.col(f'prof_ch_{dp}_temp') - F.col('prof_ch_0'))
#                    .withColumn(f'amt_ch_{dp}',
#                               F.col(f'amt_ch_{dp}_temp') - F.col('amt_ch_0'))
#                    .withColumn(f'prob5_ch_{dp}',
#                               F.col(prob_lv5_col) - F.col('prob_lv5_0'))
#                    .drop(f'prof_ch_{dp}_temp', f'amt_ch_{dp}_temp'))
    
#     return df_calc


# def _create_uid_result(df_calc):
#     """
#     Spark版UID結果生成
#     """
#     spark = SparkSession.getActiveSession()
    
#     # 基本カラム
#     base_cols = ['store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'uid', 
#                  'prof_pre', 'sample_amt_jan', 'pprice', 'max_dprice']
    
#     # 各価格に対するDataFrameを作成
#     uid_dfs = []
    
#     for dp in dprice_range:
#         # 必要なカラムを選択
#         change_cols = [f'prof_ch_{dp}', f'amt_ch_{dp}', f'prob5_ch_{dp}']
#         select_cols = base_cols + change_cols
        
#         df_temp = (df_calc.select(*select_cols)
#                    .withColumnRenamed(f'prof_ch_{dp}', 'prof_ch')
#                    .withColumnRenamed(f'amt_ch_{dp}', 'amt_ch')
#                    .withColumnRenamed(f'prob5_ch_{dp}', 'prob5_ch')
#                    .withColumn('rec_price', F.lit(dp) + F.col('pprice'))
#                    .withColumn('max_price', F.col('pprice') + F.col('max_dprice')))
        
#         uid_dfs.append(df_temp)
    
#     # 全てのDataFrameを結合
#     df_uid = uid_dfs[0]
#     for df in uid_dfs[1:]:
#         df_uid = df_uid.union(df)
    
#     # 比率計算（ゼロ除算対策）
#     df_uid = (df_uid
#               .withColumn('prof_chr',
#                          F.when(F.col('prof_pre') != 0,
#                                F.col('prof_ch') / F.col('prof_pre')).otherwise(0))
#               .withColumn('amt_chr',
#                          F.when(F.col('sample_amt_jan') != 0,
#                                F.col('amt_ch') / F.col('sample_amt_jan')).otherwise(0)))
    
#     return df_uid


# def _create_item_result(df_uid):
#     """
#     Spark版アイテム結果生成
#     """
#     # グループ化して集約
#     group_cols = ['store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'pprice', 'rec_price', 'max_price']
    
#     df_item = (df_uid.groupBy(*group_cols)
#                .agg(
#                    F.sum('prof_ch').alias('prof_ch'),
#                    F.sum('amt_ch').alias('amt_ch'),
#                    F.avg('prob5_ch').alias('prob5_ch'),
#                    F.sum('prof_pre').alias('prof_pre'),
#                    F.sum('sample_amt_jan').alias('sample_amt_jan')
#                ))
    
#     # 比率計算
#     df_item = (df_item
#                .withColumn('prof_chr',
#                           F.when(F.col('prof_pre') != 0,
#                                 F.col('prof_ch') / F.col('prof_pre')).otherwise(0))
#                .withColumn('amt_chr',
#                           F.when(F.col('sample_amt_jan') != 0,
#                                 F.col('amt_ch') / F.col('sample_amt_jan')).otherwise(0)))
    
#     # フィルタリング
#     df_valid = df_item.filter(
#         (F.col('rec_price') <= F.col('max_price')) &
#         (F.col('prof_ch') > 0) &
#         (F.col('amt_chr') >= simu_thd_amtchanger) &
#         (F.col('prob5_ch') >= simu_thd_retainr)
#     )
    
#     # 各JANの最適価格を選択
#     window_spec = Window.partitionBy('jan').orderBy(F.desc('prof_ch'))
#     df_item = (df_valid
#                .withColumn('row_num', F.row_number().over(window_spec))
#                .filter(F.col('row_num') == 1)
#                .drop('row_num'))
    
#     # シリーズ修正
#     df_item = _series_fix(df_item, df_valid, df_series)
    
#     # ランク計算
#     rank_window = Window.partitionBy('lv4_nm', 'lv5_nm').orderBy(F.desc('prof_ch'))
#     #df_item = df_item.withColumn('rank', F.row_number().over(rank_window))
#     df_item = (
#     df_item
#     .withColumn("rank_min", F.rank().over(rank_window))
#     .withColumn("rank_max", F.rank().over(rank_window) + F.count("prof_ch").over(rank_window) - 1)
#     .withColumn("rank", (F.col("rank_min") + F.col("rank_max")) / 2)
#     .drop("rank_min", "rank_max")
#     )
    
#     # 最終カラム選択とソート
#     df_item = (df_item.select(
#         'store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'pprice', 'rec_price',
#         'prof_ch', 'amt_ch', 'prob5_ch', 'prof_chr', 'amt_chr', 'rank'
#     ).orderBy('lv4_nm', 'lv5_nm', 'rank'))
    
#     # UID結果の最終処理
#     df_uid = _finalize_uid_result(df_uid, df_item)
    
#     return df_item, df_uid


# # def _series_fix(df_item, df_valid):
# #     """
# #     Spark版シリーズ修正
# #     """
# #     spark = SparkSession.getActiveSession()
    
# #     # シリーズファイルを読み込み
# #     df_series = spark.read.option("header", "true").option("inferSchema", "true").csv(series_file)
    
# #     # シリーズ情報をマージ
# #     df_item_with_series = df_item.join(df_series, on='jan', how='left')
    
# #     # 価格が多すぎるシリーズを特定
# #     series_price_counts = (df_item_with_series
# #                           .groupBy('series')
# #                           .agg(F.countDistinct('rec_price').alias('price_count'))
# #                           .filter(F.col('price_count') > max_price_cnt))
    
# #     if series_price_counts.count() == 0:
# #         return df_item_with_series.drop('series')
    
# #     # 複雑な修正処理はpandasで実行
# #     df_item_pd = df_item_with_series.toPandas()
# #     df_valid_pd = df_valid.toPandas()
# #     df_series_pd = df_series.toPandas()
    
# #     # pandas版の修正処理を実行
# #     df_result_pd = _series_fix_pandas(df_item_pd, df_valid_pd)
    
# #     # Spark DataFrameに戻す
# #     return spark.createDataFrame(df_result_pd.drop(columns=['series'], errors='ignore'))

# def _series_fix(df_item, df_valid, df_series):
#     """
#     オリジナル pandas 版の series_fix と同等の処理を Spark で実行
#     """
#     spark = SparkSession.getActiveSession()
#     #df_series = spark.read.option("header", "true").option("inferSchema", "true").csv(series_file)

#     # series 付与
#     df_item_with_series = df_item.join(df_series, on="jan", how="left")

#     # pandas に落として補正（オリジナルと同じロジック）
#     df_item_pd = df_item_with_series.toPandas()
#     df_valid_pd = df_valid.toPandas()

#     d_rep = {}
#     for igp, idf in df_item_pd.groupby("series"):
#         if idf["rec_price"].nunique() > max_price_cnt:
#             lprice = sorted(idf["rec_price"].unique())
#             for kt in idf.itertuples():
#                 if kt.rec_price <= lprice[max_price_cnt - 1]:
#                     continue
#                 kprice = df_valid_pd.loc[df_valid_pd["jan"] == kt.jan, "rec_price"].tolist()
#                 for j in range(max_price_cnt - 1, -1, -1):
#                     if lprice[j] in kprice:
#                         d_rep[kt.jan] = lprice[j]
#                         break
#                 else:
#                     d_rep[kt.jan] = -1

#     df_ret = df_item_pd.loc[~df_item_pd["jan"].isin(d_rep)].drop(columns=["series"], errors="ignore")
#     df_append = [
#         df_valid_pd.loc[(df_valid_pd["jan"] == k) & (df_valid_pd["rec_price"] == v)]
#         for k, v in d_rep.items()
#         if v > 0
#     ]
#     if df_append:
#         df_append = pd.concat(df_append)
#         df_ret = pd.concat([df_ret, df_append])

#     return spark.createDataFrame(df_ret)





# def _finalize_uid_result(df_uid, df_item):
#     """
#     Spark版UID結果最終処理
#     """
#     # 最適価格を選択
#     window_spec = Window.partitionBy('jan', 'uid').orderBy(F.desc('prof_ch'))
#     df_uid_final = (df_uid
#                     .withColumn('row_num', F.row_number().over(window_spec))
#                     .filter(F.col('row_num') == 1)
#                     .drop('row_num')
#                     .withColumnRenamed('uid', 'id')
#                     .withColumnRenamed('rec_price', 'id_rec_price'))
    
#     # 負の利益の場合は元価格に戻す
#     df_uid_final = df_uid_final.withColumn(
#         'id_rec_price',
#         F.when(F.col('prof_ch') < 0, F.col('pprice')).otherwise(F.col('id_rec_price'))
#     )
    
#     # アイテム結果とマージ
#     df_uid_final = df_uid_final.join(
#         df_item.select('jan', 'rec_price'),
#         on='jan',
#         how='inner'
#     )
    
#     # 割引価格計算
#     df_uid_final = df_uid_final.withColumn(
#         'disc_price',
#         F.greatest(F.col('rec_price') - F.col('id_rec_price'), F.lit(0))
#     )
    
#     # 最終カラム選択とソート
#     df_uid_final = (df_uid_final.select(
#         'store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'pprice', 'rec_price',
#         'id', 'id_rec_price', 'disc_price'
#     ).orderBy('lv4_nm', 'lv5_nm', 'jan'))
    
#     return df_uid_final


# # 使用例
# def run_simulation(df_pred, df_item_mst):
#     """
#     Sparkシミュレーションの実行
#     """
#     try:
#         df_item, df_uid = calc_simu_result(df_pred, df_item_mst)
        
#         print(f"Item results count: {df_item.count()}")
#         print(f"UID results count: {df_uid.count()}")
        
#         return df_item, df_uid
        
#     except Exception as e:
#         print(f"Simulation error: {e}")
#         raiseseries

# COMMAND ----------

# MAGIC %md
# MAGIC ↓が今のところ一番いいやつ

# COMMAND ----------

# from pyspark.sql import SparkSession, functions as F
# from pyspark.sql.types import *
# from pyspark.sql.window import Window
# import pandas as pd
# import numpy as np

# # dprice_rangeをソート
# dprice_range = sorted(dprice_range)

# def calc_simu_result(df_pred, df_item_mst):
#     """
#     Spark版シミュレーション結果計算
    
#     Parameters
#     ----------
#     df_pred: Spark DataFrame
#         columns = key_cols + ['prob_jan_x', 'prob_lv5_x', ...]
#     df_item_mst: Spark DataFrame
#         columns=['jan', 'name', 'oprice', 'max_dprice']
    
#     Returns
#     -------
#     tuple: (df_item, df_uid)
#     """

#     # null埋め
#     df_pred = df_pred.fillna(0)
#     df_item_mst = df_item_mst.fillna(0)
#     # マージと基本計算
#     df_calc = df_pred.join(df_item_mst, on='jan', how='left')
    
#     # 基本計算をベクトル化
#     df_calc = (df_calc
#                .withColumn('cnt', F.floor(F.col('sample_amt_jan') / F.col('pprice')))
#                #.withColumn('cnt', F.col('sample_amt_jan') / F.col('pprice'))
#                .withColumn('prof_pre', F.col('cnt') * (F.col('pprice') - F.col('oprice'))))
    
#     # 全価格に対する変化計算
#     df_calc = _calculate_changes(df_calc)
    
#     # UID結果とアイテム結果を生成
#     df_uid = _create_uid_result(df_calc)
#     df_item = _create_item_result(df_uid)
    
#     return df_item, df_uid


# def _calculate_changes(df_calc):
#     """
#     Spark版全価格変更に対する変化計算
#     """
#     # 基準値（dp=0）の計算
#     df_calc = (df_calc
#                .withColumn('prof_ch_0', 
#                           (F.col('prob_jan_0') * 0 - (1 - F.col('prob_lv5_0')) * 
#                            (F.col('pprice') - F.col('oprice'))) * F.col('cnt'))
#                .withColumn('amt_ch_0',
#                           (F.col('prob_jan_0') * 0 - (1 - F.col('prob_lv5_0')) * 
#                            F.col('pprice')) * F.col('cnt')))
    
#     # 各価格変更に対する計算
#     for dp in dprice_range:
#         prob_jan_col = f'prob_jan_{dp}'
#         prob_lv5_col = f'prob_lv5_{dp}'
        
#         # 変化の計算
#         df_calc = (df_calc
#                    .withColumn(f'prof_ch_{dp}_temp',
#                               (F.col(prob_jan_col) * dp - (1 - F.col(prob_lv5_col)) * 
#                                (F.col('pprice') - F.col('oprice'))) * F.col('cnt'))
#                    .withColumn(f'amt_ch_{dp}_temp',
#                               (F.col(prob_jan_col) * dp - (1 - F.col(prob_lv5_col)) * 
#                                F.col('pprice')) * F.col('cnt'))
#                    .withColumn(f'prof_ch_{dp}', 
#                               F.col(f'prof_ch_{dp}_temp') - F.col('prof_ch_0'))
#                    .withColumn(f'amt_ch_{dp}',
#                               F.col(f'amt_ch_{dp}_temp') - F.col('amt_ch_0'))
#                    .withColumn(f'prob5_ch_{dp}',
#                               F.col(prob_lv5_col) - F.col('prob_lv5_0'))
#                    .drop(f'prof_ch_{dp}_temp', f'amt_ch_{dp}_temp'))
    
#     return df_calc


# def _create_uid_result(df_calc):
#     """
#     Spark版UID結果生成
#     """
#     spark = SparkSession.getActiveSession()
    
#     # 基本カラム
#     base_cols = ['store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'uid', 
#                  'prof_pre', 'sample_amt_jan', 'pprice', 'max_dprice']
    
#     # 各価格に対するDataFrameを作成
#     uid_dfs = []
    
#     for dp in dprice_range:
#         # 必要なカラムを選択
#         change_cols = [f'prof_ch_{dp}', f'amt_ch_{dp}', f'prob5_ch_{dp}']
#         select_cols = base_cols + change_cols
        
#         df_temp = (df_calc.select(*select_cols)
#                    .withColumnRenamed(f'prof_ch_{dp}', 'prof_ch')
#                    .withColumnRenamed(f'amt_ch_{dp}', 'amt_ch')
#                    .withColumnRenamed(f'prob5_ch_{dp}', 'prob5_ch')
#                    .withColumn('rec_price', F.lit(dp) + F.col('pprice'))
#                    .withColumn('max_price', F.col('pprice') + F.col('max_dprice')))
        
#         uid_dfs.append(df_temp)
    
#     # 全てのDataFrameを結合
#     df_uid = uid_dfs[0]
#     for df in uid_dfs[1:]:
#         df_uid = df_uid.union(df)
    
#     # 比率計算（ゼロ除算対策）
#     df_uid = (df_uid
#               .withColumn('prof_chr',
#                          F.when(F.col('prof_pre') != 0,
#                                F.col('prof_ch') / F.col('prof_pre')).otherwise(0))
#               .withColumn('amt_chr',
#                          F.when(F.col('sample_amt_jan') != 0,
#                                F.col('amt_ch') / F.col('sample_amt_jan')).otherwise(0)))
    
#     return df_uid


# def _create_item_result(df_uid):
#     """
#     Spark版アイテム結果生成
#     """
#     # グループ化して集約
#     group_cols = ['store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'pprice', 'rec_price', 'max_price']
    
#     df_item = (df_uid.groupBy(*group_cols)
#                .agg(
#                    F.sum('prof_ch').alias('prof_ch'),
#                    F.sum('amt_ch').alias('amt_ch'),
#                    F.avg('prob5_ch').alias('prob5_ch'),
#                    F.sum('prof_pre').alias('prof_pre'),
#                    F.sum('sample_amt_jan').alias('sample_amt_jan')
#                ))
    
#     # 比率計算
#     df_item = (df_item
#                .withColumn('prof_chr',
#                           F.when(F.col('prof_pre') != 0,
#                                 F.col('prof_ch') / F.col('prof_pre')).otherwise(0))
#                .withColumn('amt_chr',
#                           F.when(F.col('sample_amt_jan') != 0,
#                                 F.col('amt_ch') / F.col('sample_amt_jan')).otherwise(0)))
    
#     # フィルタリング
#     df_valid = df_item.filter(
#         (F.col('rec_price') <= F.col('max_price')) &
#         (F.col('prof_ch') > 0) &
#         (F.col('amt_chr') >= simu_thd_amtchanger) &
#         (F.col('prob5_ch') >= simu_thd_retainr)
#     )
    
#     # 各JANの最適価格を選択
#     window_spec = Window.partitionBy('jan').orderBy(F.desc('prof_ch'))
#     df_item = (df_valid
#                .withColumn('row_num', F.row_number().over(window_spec))
#                .filter(F.col('row_num') == 1)
#                .drop('row_num'))
    
#     # シリーズ修正
#     df_item = _series_fix(df_item, df_valid, df_series)
    
#     # ランク計算
#     rank_window = Window.partitionBy('lv4_nm', 'lv5_nm').orderBy(F.desc('prof_ch'))
#     #df_item = df_item.withColumn('rank', F.row_number().over(rank_window))
#     df_item = (
#     df_item
#     .withColumn("rank_min", F.rank().over(rank_window))
#     .withColumn("rank_max", F.rank().over(rank_window) + F.count("prof_ch").over(rank_window) - 1)
#     .withColumn("rank", (F.col("rank_min") + F.col("rank_max")) / 2)
#     .drop("rank_min", "rank_max")
#     )
    
#     # 最終カラム選択とソート
#     df_item = (df_item.select(
#         'store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'pprice', 'rec_price',
#         'prof_ch', 'amt_ch', 'prob5_ch', 'prof_chr', 'amt_chr', 'rank'
#     ).orderBy('lv4_nm', 'lv5_nm', 'rank'))
    
#     # UID結果の最終処理
#     df_uid = _finalize_uid_result(df_uid, df_item)
    
#     return df_item, df_uid


# # def _series_fix(df_item, df_valid):
# #     """
# #     Spark版シリーズ修正
# #     """
# #     spark = SparkSession.getActiveSession()
    
# #     # シリーズファイルを読み込み
# #     df_series = spark.read.option("header", "true").option("inferSchema", "true").csv(series_file)
    
# #     # シリーズ情報をマージ
# #     df_item_with_series = df_item.join(df_series, on='jan', how='left')
    
# #     # 価格が多すぎるシリーズを特定
# #     series_price_counts = (df_item_with_series
# #                           .groupBy('series')
# #                           .agg(F.countDistinct('rec_price').alias('price_count'))
# #                           .filter(F.col('price_count') > max_price_cnt))
    
# #     if series_price_counts.count() == 0:
# #         return df_item_with_series.drop('series')
    
# #     # 複雑な修正処理はpandasで実行
# #     df_item_pd = df_item_with_series.toPandas()
# #     df_valid_pd = df_valid.toPandas()
# #     df_series_pd = df_series.toPandas()
    
# #     # pandas版の修正処理を実行
# #     df_result_pd = _series_fix_pandas(df_item_pd, df_valid_pd)
    
# #     # Spark DataFrameに戻す
# #     return spark.createDataFrame(df_result_pd.drop(columns=['series'], errors='ignore'))

# def _series_fix(df_item, df_valid, df_series):
#     """
#     オリジナル pandas 版の series_fix と同等の処理を Spark で実行
#     """
#     spark = SparkSession.getActiveSession()
#     #df_series = spark.read.option("header", "true").option("inferSchema", "true").csv(series_file)

#     # series 付与
#     df_item_with_series = df_item.join(df_series, on="jan", how="left")

#     # pandas に落として補正（オリジナルと同じロジック）
#     df_item_pd = df_item_with_series.toPandas()
#     df_valid_pd = df_valid.toPandas()

#     d_rep = {}
#     for igp, idf in df_item_pd.groupby("series"):
#         if idf["rec_price"].nunique() > max_price_cnt:
#             lprice = sorted(idf["rec_price"].unique())
#             for kt in idf.itertuples():
#                 if kt.rec_price <= lprice[max_price_cnt - 1]:
#                     continue
#                 kprice = df_valid_pd.loc[df_valid_pd["jan"] == kt.jan, "rec_price"].tolist()
#                 for j in range(max_price_cnt - 1, -1, -1):
#                     if lprice[j] in kprice:
#                         d_rep[kt.jan] = lprice[j]
#                         break
#                 else:
#                     d_rep[kt.jan] = -1

#     df_ret = df_item_pd.loc[~df_item_pd["jan"].isin(d_rep)].drop(columns=["series"], errors="ignore")
#     df_append = [
#         df_valid_pd.loc[(df_valid_pd["jan"] == k) & (df_valid_pd["rec_price"] == v)]
#         for k, v in d_rep.items()
#         if v > 0
#     ]
#     if df_append:
#         df_append = pd.concat(df_append)
#         df_ret = pd.concat([df_ret, df_append])

#     return spark.createDataFrame(df_ret)





# def _finalize_uid_result(df_uid, df_item):
#     """
#     Spark版UID結果最終処理
#     """
#     # 最適価格を選択
#     window_spec = Window.partitionBy('jan', 'uid').orderBy(F.desc('prof_ch'))
#     df_uid_final = (df_uid
#                     .withColumn('row_num', F.row_number().over(window_spec))
#                     .filter(F.col('row_num') == 1)
#                     .drop('row_num')
#                     .withColumnRenamed('uid', 'id')
#                     .withColumnRenamed('rec_price', 'id_rec_price'))
    
#     # 負の利益の場合は元価格に戻す
#     df_uid_final = df_uid_final.withColumn(
#         'id_rec_price',
#         F.when(F.col('prof_ch') < 0, F.col('pprice')).otherwise(F.col('id_rec_price'))
#     )
    
#     # アイテム結果とマージ
#     df_uid_final = df_uid_final.join(
#         df_item.select('jan', 'rec_price'),
#         on='jan',
#         how='inner'
#     )
    
#     # 割引価格計算
#     df_uid_final = df_uid_final.withColumn(
#         'disc_price',
#         F.greatest(F.col('rec_price') - F.col('id_rec_price'), F.lit(0))
#     )
    
#     # 最終カラム選択とソート
#     df_uid_final = (df_uid_final.select(
#         'store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'name', 'pprice', 'rec_price',
#         'id', 'id_rec_price', 'disc_price'
#     ).orderBy('lv4_nm', 'lv5_nm', 'jan'))
    
#     return df_uid_final


# # 使用例
# def run_simulation(df_pred, df_item_mst):
#     """
#     Sparkシミュレーションの実行
#     """
#     try:
#         df_item, df_uid = calc_simu_result(df_pred, df_item_mst)
        
#         print(f"Item results count: {df_item.count()}")
#         print(f"UID results count: {df_uid.count()}")
        
#         return df_item, df_uid
        
#     except Exception as e:
#         print(f"Simulation error: {e}")
#         raiseseries

# COMMAND ----------

from pyspark.sql import functions as F, Window

dprice_range = sorted(dprice_range)

def calc_simu_result(df_pred, df_item_mst):
    """Spark簡略版：Pandas版と同等の計算結果"""
    # --- 前処理 ---
    df = df_pred.join(df_item_mst, on='jan', how='left')
    df = df.withColumn('cnt', (F.col('sample_amt_jan') / F.col('pprice')).cast('long'))
    df = df.withColumn('prof_pre', F.col('cnt') * (F.col('pprice') - F.col('oprice')))

    # --- dp=0 ---
    df = df.withColumn('prof_ch_0', (-(1 - F.col('prob_lv5_0')) * (F.col('pprice') - F.col('oprice'))) * F.col('cnt'))
    df = df.withColumn('amt_ch_0', (-(1 - F.col('prob_lv5_0')) * F.col('pprice')) * F.col('cnt'))

    # --- 各dpの計算 ---
    for dp in dprice_range:
        df = df.withColumn(f'prof_ch_{dp}', ((F.col(f'prob_jan_{dp}') * dp -
                                             (1 - F.col(f'prob_lv5_{dp}')) * (F.col('pprice') - F.col('oprice'))) * F.col('cnt'))
                           - F.col('prof_ch_0'))
        df = df.withColumn(f'amt_ch_{dp}', ((F.col(f'prob_jan_{dp}') * dp -
                                            (1 - F.col(f'prob_lv5_{dp}')) * F.col('pprice')) * F.col('cnt'))
                           - F.col('amt_ch_0'))
        df = df.withColumn(f'prob5_ch_{dp}', F.col(f'prob_lv5_{dp}') - F.col('prob_lv5_0'))

    # --- UID単位展開 ---
    base_cols = ['store_cd','lv4_nm','lv5_nm','jan','name','uid','prof_pre','sample_amt_jan','pprice','max_dprice']
    df_uid = None
    for dp in dprice_range:
        dft = df.select(*base_cols,
                        F.col(f'prof_ch_{dp}').alias('prof_ch'),
                        F.col(f'amt_ch_{dp}').alias('amt_ch'),
                        F.col(f'prob5_ch_{dp}').alias('prob5_ch'))
        dft = dft.withColumn('rec_price', F.col('pprice') + F.lit(dp))
        dft = dft.withColumn('max_price', F.col('pprice') + F.col('max_dprice'))
        df_uid = dft if df_uid is None else df_uid.union(dft)

    df_uid = (df_uid
              .withColumn('prof_chr', F.when(F.col('prof_pre') != 0, F.col('prof_ch') / F.col('prof_pre')).otherwise(0))
              .withColumn('amt_chr', F.when(F.col('sample_amt_jan') != 0, F.col('amt_ch') / F.col('sample_amt_jan')).otherwise(0)))

    # --- item集計 ---
    df_item = (df_uid.groupBy('store_cd','lv4_nm','lv5_nm','jan','name','pprice','rec_price','max_price')
                     .agg(F.sum('prof_ch').alias('prof_ch'),
                          F.sum('amt_ch').alias('amt_ch'),
                          F.avg('prob5_ch').alias('prob5_ch'),
                          F.sum('prof_pre').alias('prof_pre'),
                          F.sum('sample_amt_jan').alias('sample_amt_jan'))
                     .withColumn('prof_chr', F.col('prof_ch') / F.col('prof_pre'))
                     .withColumn('amt_chr', F.col('amt_ch') / F.col('sample_amt_jan')))

    # --- 条件フィルタ + best price per jan ---
    df_item = df_item.filter(
        (F.col('rec_price') <= F.col('max_price')) &
        (F.col('prof_ch') > 0) &
        (F.col('amt_chr') >= simu_thd_amtchanger) &
        (F.col('prob5_ch') >= simu_thd_retainr)
    )
    w = Window.partitionBy('jan').orderBy(F.desc('prof_ch'))
    df_item = df_item.withColumn('r', F.row_number().over(w)).filter('r=1').drop('r')

    # --- rank付与 ---
    w2 = Window.partitionBy('lv4_nm', 'lv5_nm').orderBy(F.desc('prof_ch'))
    df_item = df_item.withColumn('rank', F.rank().over(w2))

    # --- uid最終処理 ---
    w3 = Window.partitionBy('jan', 'uid').orderBy(F.desc('prof_ch'))
    df_uid = (df_uid.withColumn('r', F.row_number().over(w3))
                      .filter('r=1').drop('r')
                      .withColumnRenamed('uid','id')
                      .withColumnRenamed('rec_price','id_rec_price')
                      .withColumn('id_rec_price', F.when(F.col('prof_ch')<0,F.col('pprice')).otherwise(F.col('id_rec_price')))
                      .join(df_item.select('jan','rec_price'), on='jan', how='inner')
                      .withColumn('disc_price', F.greatest(F.col('rec_price') - F.col('id_rec_price'), F.lit(0)))
                      .select('store_cd','lv4_nm','lv5_nm','jan','name','pprice','rec_price','id','id_rec_price','disc_price'))

    return df_item, df_uid
