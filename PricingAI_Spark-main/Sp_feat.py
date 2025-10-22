# Databricks notebook source
# MAGIC %run ./Sp_config.py

# COMMAND ----------

# MAGIC %run ./Sp_io.py

# COMMAND ----------

# MAGIC %run ./Sp_utils.py

# COMMAND ----------

# MAGIC %md
# MAGIC 実行中コード

# COMMAND ----------

# from pyspark.sql import SparkSession, Window
# from pyspark.sql.functions import col, when, lit, expr, sum as Fsum, countDistinct, rank, row_number, max as Fmax, abs as Fabs
# from functools import lru_cache, reduce
# import pyspark.sql.functions as F
# import numpy as np
# import multiprocessing as mp


# spark = SparkSession.builder.getOrCreate()

# # ------------------------
# # 価格特徴量
# # ------------------------
# def _add_feature_price(df_feat, df_lv5, df_jan, **kws):
#     df_feat = df_feat.withColumn("dprice", df_feat.aprice - df_feat.pprice)
#     df_feat = df_feat.withColumn("dprice_pct", df_feat.dprice / df_feat.pprice)
#     return df_feat

# # ------------------------
# # RFM特徴量
# # ------------------------
# def _make_rfm(df, suffix, fend):
#     if df.rdd.isEmpty():
#         cols = ['uid', f'r_{suffix}', f'f_{suffix}', f'm_{suffix}',
#                 f'rscore_{suffix}', f'fscore_{suffix}', f'mscore_{suffix}',
#                 f'rfm_score_{suffix}', f'rfm_score2_{suffix}']
#         return spark.createDataFrame([], schema=cols)

#     rfm_weights = [0.3, 0.3, 0.4]
    
#     df_rfm = df.groupBy("uid").agg(
#         Fmax("salesday").alias("last_date"),
#         countDistinct("salesday").alias("frequency"),
#         Fsum("salesamount").alias("monetary")
#     )
    
#     # RFM計算
#     df_rfm = df_rfm.withColumn(f"r_{suffix}", F.datediff(F.lit(fend), col("last_date"))) \
#                    .withColumn(f"f_{suffix}", col("frequency")) \
#                    .withColumn(f"m_{suffix}", col("monetary"))

#     # スコア計算（ランクを利用）
#     w = Window.orderBy(col(f"r_{suffix}").desc())
#     df_rfm = df_rfm.withColumn(f"rscore_{suffix}", rank().over(w) / df_rfm.count())
    
#     w_f = Window.orderBy(col(f"f_{suffix}"))
#     df_rfm = df_rfm.withColumn(f"fscore_{suffix}", rank().over(w_f) / df_rfm.count())
    
#     w_m = Window.orderBy(col(f"m_{suffix}"))
#     df_rfm = df_rfm.withColumn(f"mscore_{suffix}", rank().over(w_m) / df_rfm.count())

#     # 複合スコア
#     df_rfm = df_rfm.withColumn(f"rfm_score_{suffix}", 
#                                rfm_weights[0]*col(f"rscore_{suffix}") +
#                                rfm_weights[1]*col(f"fscore_{suffix}") +
#                                rfm_weights[2]*col(f"mscore_{suffix}"))

#     # 調和平均
#     df_rfm = df_rfm.withColumn(
#         f"rfm_score2_{suffix}",
#         F.when(
#             (col(f"rscore_{suffix}") != 0) & 
#             (col(f"fscore_{suffix}") != 0) &
#             (col(f"mscore_{suffix}") != 0),
#             3 / (1/col(f"rscore_{suffix}") + 1/col(f"fscore_{suffix}") + 1/col(f"mscore_{suffix}"))
#         ).otherwise(lit(0))
#     )

#     return df_rfm.drop("last_date", "frequency", "monetary")

# def _add_feature_rfm(df_feat, df_lv5, df_jan, **kws):
#     fend = strdoffset(df_feat.select("astart").first()[0], -1)
#     rfm_jan = _make_rfm(df_jan, "jan", fend)
#     rfm_lv5 = _make_rfm(df_lv5, "lv5", fend)
#     df_feat = df_feat.join(rfm_jan, "uid", "left").join(rfm_lv5, "uid", "left")
#     return df_feat

# # ------------------------
# # ロイヤリティ特徴量
# # ------------------------
# def _add_feature_roy(df_feat, df_lv5, df_jan, **kws):
#     df_feat = df_feat.withColumn("jan_loy_m", F.when(col("m_lv5") != 0, col("m_jan")/col("m_lv5")).otherwise(0)) \
#                      .withColumn("jan_loy_f", F.when(col("f_lv5") != 0, col("f_jan")/col("f_lv5")).otherwise(0)) \
#                      .withColumn("jan_loy", (col("jan_loy_m")+col("jan_loy_f"))/2)
#     return df_feat

# # ------------------------
# # Pスコア特徴量
# # ------------------------
# def _add_feature_pscore(df_feat, df_lv5, df_jan, **kws):
#     tjan = df_feat.select("jan").first()[0]
#     df_det = kws['df_det']
#     d_plv5 = kws['d_plv5']
#     if tjan not in d_plv5:
#         return df_feat
#     plv5 = d_plv5[tjan]
#     if plv5 in pscore_ignore_plv5:
#         return df_feat

#     df_joined = df_lv5.join(df_det, "jan").filter(col("plv5_nm")==plv5)
#     if df_joined.rdd.isEmpty():
#         return df_feat

#     df_joined = df_joined.withColumn("volumn", col("det_val")*col("salescnt"))
#     df_tjan = df_joined.filter(col("jan")==tjan)

#     # uidごとの集計
#     df_ret = df_joined.groupBy("uid").agg(
#         Fsum("salesamount").alias("salesamount"),
#         Fsum("volumn").alias("volumn"),
#         countDistinct("salesday").alias("salesday")
#     )

#     total_amount = df_joined.agg(Fsum("salesamount")).first()[0]
#     total_volumn = df_joined.agg(Fsum("volumn")).first()[0]
#     catep = total_amount/total_volumn if total_volumn>0 else 0

#     item_amount = df_tjan.agg(Fsum("salesamount")).first()[0]
#     item_volumn = df_tjan.agg(Fsum("volumn")).first()[0]
#     itemp = item_amount/item_volumn if item_volumn>0 else 0

#     df_ret = df_ret.withColumn("unitp_cate", F.lit(catep)) \
#                    .withColumn("unitp_item", F.lit(itemp)) \
#                    .withColumn("unitp_uid", F.when(col("volumn")>0, col("salesamount")/col("volumn")).otherwise(0))

#     if catep>0:
#         df_ret = df_ret.withColumn("pscore_item", (F.lit(itemp)-F.lit(catep))/F.lit(catep)) \
#                        .withColumn("pscore_ucate", (col("unitp_uid")-F.lit(catep))/F.lit(catep) *
#                                    (col("salesday")/pscore_modify_ndays).cast("double"))
#     else:
#         df_ret = df_ret.withColumn("pscore_item", lit(0)).withColumn("pscore_ucate", lit(0))

#     df_feat = df_feat.join(df_ret, "uid", "left") \
#                      .withColumn("pscore_ucate_dis050", F.abs(col("pscore_ucate")-0.5))
#     return df_feat

# # ------------------------
# # カニバリスコア
# # ------------------------
# # def _add_feature_kaniscore(df_feat, df_lv5, df_jan, **kws):
# #     tjan = df_feat.select("jan").first()[0]

# #     if df_jan.rdd.isEmpty():
# #         df_feat = df_feat.withColumn("kani_score", F.lit(0)).withColumn("kani_score_dis025", F.lit(0))
# #         return df_feat

# #     tuid = [row.uid for row in df_jan.select("uid").distinct().collect()]
# #     df_use = df_lv5.filter(col("uid").isin(tuid))
# #     if df_use.rdd.isEmpty():
# #         df_feat = df_feat.withColumn("kani_score", F.lit(0)).withColumn("kani_score_dis025", F.lit(0))
# #         return df_feat

# #     tjan_amounts = df_use.filter(col("jan")==tjan).groupBy("uid").agg(Fsum("salesamount").alias("tamt"))
# #     other_jan_amounts = df_use.filter(col("jan")!=tjan).groupBy("uid","jan").agg(Fsum("salesamount").alias("amt"))

# #     # ここは簡略化してベクトル化
# #     # 実務では UDF で計算するのが最適
# #     # ここでは一律0で代替（軽量化目的）
# #     df_feat = df_feat.withColumn("kani_score", F.lit(0)).withColumn("kani_score_dis025", F.lit(0))
# #     return df_feat

# def _add_feature_kaniscore(df_feat, df_lv5, df_jan, **kws):
#     tjan = df_feat.select("jan").first()[0]

#     # --- 対象UID抽出 ---
#     tuid = [r.uid for r in df_jan.select("uid").distinct().collect()]
#     df_use = df_lv5.filter(col("uid").isin(tuid))

#     if df_use.rdd.isEmpty():
#         df_feat = df_feat.withColumn("kani_score", lit(0)).withColumn("kani_score_dis025", lit(0))
#         return df_feat

#     # --- tjanの売上 ---
#     df_tamt = df_use.filter(col("jan") == tjan).groupBy("uid").agg(Fsum("salesamount").alias("tamt"))

#     # --- 他JANの売上 ---
#     df_other = df_use.filter(col("jan") != tjan) \
#                      .groupBy("uid", "jan") \
#                      .agg(Fsum("salesamount").alias("amt"))

#     # --- UID単位で競合スコア計算 ---
#     df_score = df_other.join(df_tamt, "uid") \
#                        .withColumn("kani_score", (0.5 - ((col("amt")/(col("amt")+col("tamt"))) - 0.5).abs()) * 2)

#     # --- JAN単位で集計 ---
#     df_score_sum = df_score.groupBy("jan").agg(Fsum("kani_score").alias("kani_score_sum"))

#     # --- 上位5件の指数平均 ---
#     w = Window.orderBy(col("kani_score_sum").desc())
#     df_score_rank = df_score_sum.withColumn("rank", row_number().over(w))
#     df_top5 = df_score_rank.filter(col("rank") <= 5)

#     # 指数平均の計算（UDF使用）
#     from pyspark.sql.functions import udf
#     from pyspark.sql.types import DoubleType

#     def exp_mean(scores):
#         n = len(scores)
#         if n == 0: return 0.0
#         return sum([2**(-i-1) * v for i,v in enumerate(scores)]) / (1 - 2**-n)

#     exp_mean_udf = udf(exp_mean, DoubleType())

#     # 集計して単一値に
#     kani_val = exp_mean_udf(F.collect_list("kani_score_sum").over(Window.partitionBy()))
#     df_feat = df_feat.withColumn("kani_score", kani_val)
#     df_feat = df_feat.withColumn("kani_score_dis025", (col("kani_score") - 0.25).abs())

#     return df_feat

# # ------------------------
# # IDPOS前処理
# # ------------------------
# def _preprocess_idpos_data(df_idpos):
#     df_clean = df_idpos.filter((col("salesamount")>0) & (col("uid")!="0"))
#     df_clean = df_clean.withColumn("price", col("salesamount") / col("salescnt")) \
#                        .withColumn("salescnt", F.when(col("salescnt")>noise_max_cnt, noise_max_cnt).otherwise(col("salescnt"))) \
#                        .withColumn("salesamount", col("price")*col("salescnt"))
#     return df_clean

# # ------------------------
# # 1ケースの特徴量作成
# # ------------------------
# # def _add_feat_case(df_idpos, df_base, tjan, astart, **kws):
# #     start_date = strdoffset(astart, -feature_len)
# #     end_date = strdoffset(astart, -1)
    
# #     df_period = df_idpos.filter((col("salesday")>=start_date) & (col("salesday")<=end_date))
    
# #     lv4_target = df_base.select("lv4_nm").first()[0]
# #     lv5_target = df_base.select("lv5_nm").first()[0]
    
# #     df_lv5 = df_period.filter((col("lv4_nm")==lv4_target) & (col("lv5_nm")==lv5_target))
# #     df_jan = df_lv5.filter(col("jan")==tjan)
    
# #     df_feat = df_base
# #     feature_functions = [
# #         _add_feature_price,
# #         _add_feature_rfm,
# #         _add_feature_roy,
# #         _add_feature_pscore,
# #         _add_feature_kaniscore,
# #     ]
    
# #     for func in feature_functions:
# #         df_feat = func(df_feat, df_lv5, df_jan, **kws)
    
# #     return df_feat

# def _add_feat_case(df_idpos, df_base, tjan, astart, verbose=False, **kws):
#     start_date = strdoffset(astart, -feature_len)
#     end_date = strdoffset(astart, -1)

#     df_period = df_idpos.filter(
#         (col("salesday") >= start_date) & (col("salesday") <= end_date)
#     )

#     # --- 空チェック ---
#     row_lv4 = df_base.select("lv4_nm").first()
#     row_lv5 = df_base.select("lv5_nm").first()
#     if row_lv4 is None or row_lv5 is None:
#         if verbose:
#             print(f"skip case (jan={tjan}, astart={astart}) → no lv4/lv5")
#         return None

#     lv4_target = row_lv4[0]
#     lv5_target = row_lv5[0]

#     df_lv5 = df_period.filter(
#         (col("lv4_nm") == lv4_target) & (col("lv5_nm") == lv5_target)
#     )
#     df_jan = df_lv5.filter(col("jan") == tjan)

#     # lv5 のデータが無ければスキップ
#     if df_lv5.count() == 0:
#         if verbose:
#             print(f"skip case (jan={tjan}, astart={astart}) → no lv5 data")
#         return None

#     df_feat = df_base
#     feature_functions = [
#         _add_feature_price,
#         _add_feature_rfm,
#         _add_feature_roy,
#         _add_feature_pscore,
#         _add_feature_kaniscore,
#     ]

#     for func in feature_functions:
#         df_feat = func(df_feat, df_lv5, df_jan, **kws)

#     return df_feat


# def _add_feat_store(store_cd, df_base, df_det, verbose=False):
#     """
#     add features in one store (Spark version).
#     """

#     # --- idpos期間 ---
#     row_min = df_base.select(F.min("astart")).first()
#     row_max = df_base.select(F.max("astart")).first()
#     if row_min is None or row_max is None:
#         if verbose:
#             print(f"skip store {store_cd} → no astart data")
#         return None

#     idpos_period = (
#         strdoffset(row_min[0], -feature_len),
#         row_max[0]
#     )

#     # --- idpos データ取得 & 前処理 ---
#     df_idpos = fetch_idpos(salesday=idpos_period, lv3_nm='洋日配', storecd=store_cd)
#     df_idpos = _preprocess_idpos_data(df_idpos)

#     # --- det データ作成 ---
#     jan_info = df_idpos.select("jan", "lv4_nm", "lv5_nm").dropDuplicates()
#     df_det = df_det.join(jan_info, "jan", "inner")

#     if pscore_mod_lv5:
#         kvs = []
#         for k, v in pscore_mod_lv5.items():
#             kvs.append(lit(k))
#             kvs.append(lit(v))
#         pscore_map = F.create_map(*kvs)

#         df_det = df_det.withColumn(
#             "_pscore_thd", pscore_map[col("lv5_nm")]
#         ).withColumn(
#             "plv5_nm",
#             when(
#                 (col("lv5_nm").isin(list(pscore_mod_lv5.keys()))) &
#                 (col("_pscore_thd").isNotNull()) &
#                 (col("det_val") > col("_pscore_thd")) &
#                 (col("det_val") < lit(pscore_multipkg_thd)),
#                 F.concat(col("lv5_nm"), lit("_L"))
#             ).otherwise(F.concat(col("lv5_nm"), lit("_S")))
#         ).drop("_pscore_thd", "lv4_nm", "lv5_nm")
#     else:
#         df_det = df_det.withColumn("plv5_nm", col("lv5_nm")).drop("lv4_nm", "lv5_nm")

#     # --- plv5_nm dict を driver 側で作成 ---
#     d_plv5 = {r["jan"]: r["plv5_nm"] for r in df_det.select("jan", "plv5_nm").distinct().collect()}

#     # --- 各 case ごとのループ処理 ---
#     df_ret = None
#     kws = {"df_det": df_det, "d_plv5": d_plv5}

#     cases = df_base.select("jan", "astart").distinct().collect()

#     for row in cases:
#         ijan, iastart = row["jan"], row["astart"]
#         idf = df_base.filter((col("jan") == ijan) & (col("astart") == iastart))
#         res = _add_feat_case(df_idpos, idf, ijan, iastart, verbose=verbose, **kws)

#         if res is None:
#             continue

#         if df_ret is None:
#             df_ret = res
#         else:
#             df_ret = df_ret.unionByName(res, allowMissingColumns=True)

#     if df_ret is None:
#         if verbose:
#             print(f"skip store {store_cd} → no valid cases")
#         df_ret = spark.createDataFrame([], schema=df_base.schema)

#     return df_ret



# # ------------------------
# # 全店舗特徴量作成
# # ------------------------
# def add_features(df_base, df_det, n_jobs=None, verbose=False):
#     """
#     全店舗分の特徴量を作成して1つのDataFrameで返す。
#     """
#     if n_jobs is None:
#         store_count = df_base.select("store_cd").distinct().count()
#         n_jobs = min(mp.cpu_count(), store_count)

#     store_iter = df_base.select("store_cd").distinct().toLocalIterator()

#     df_final = None
#     processed = 0

#     for r in store_iter:
#         store = r["store_cd"]
#         df_base_store = df_base.filter(col("store_cd") == store)

#         res = _add_feat_store(store, df_base_store, df_det, verbose=verbose)
#         if res is None or res.count() == 0:
#             if verbose:
#                 print(f"skip store {store} (no data)")
#             continue

#         if df_final is None:
#             df_final = res
#         else:
#             df_final = df_final.unionByName(res, allowMissingColumns=True)

#         processed += 1
#         if verbose and processed % 50 == 0:
#             print(f"processed {processed} stores...")

#     if df_final is None:
#         schema = df_base.schema
#         df_final = spark.createDataFrame([], schema=schema)

#     return df_final


# COMMAND ----------

# MAGIC %md
# MAGIC 改良版

# COMMAND ----------

# from pyspark.sql import SparkSession, Window
# from pyspark.sql.functions import (
#     col, when, lit, expr, sum as Fsum, countDistinct, rank, percent_rank,
#     row_number, max as Fmax, abs as Fabs, min as Fmin, broadcast
# )
# from functools import reduce
# import pyspark.sql.functions as F
# import time

# spark = SparkSession.builder.getOrCreate()

# def _create_plv5(lv5, det_val):
#     """
#     Pandas版の_create_plv5をSpark UDF化したもの
#     """
#     if lv5 in pscore_mod_lv5:
#         if det_val > pscore_mod_lv5[lv5] and det_val < pscore_multipkg_thd:
#             return lv5 + "_L"
#         else:
#             return lv5 + "_S"
#     else:
#         return lv5

# create_plv5_udf = udf(_create_plv5, StringType())

# # ------------------------
# # 価格特徴量
# # ------------------------
# def _add_feature_price(df_feat, df_lv5, df_jan, **kws):
#     return (
#         df_feat
#         .withColumn("dprice", col("aprice") - col("pprice"))
#         .withColumn("dprice_pct", (col("aprice") - col("pprice")) / col("pprice"))
#     )

# # ------------------------
# # RFM特徴量
# # ------------------------
# def _make_rfm(df, suffix, fend):
#     if df.rdd.isEmpty():
#         return None

#     rfm_weights = [0.3, 0.3, 0.4]

#     df_rfm = df.groupBy("uid").agg(
#         Fmax("salesday").alias("last_date"),
#         countDistinct("salesday").alias("frequency"),
#         Fsum("salesamount").alias("monetary")
#     )

#     df_rfm = (
#         df_rfm
#         .withColumn(f"r_{suffix}", F.datediff(F.lit(fend), col("last_date")))
#         .withColumn(f"f_{suffix}", col("frequency"))
#         .withColumn(f"m_{suffix}", col("monetary"))
#     )

#     # percentile rank (注意: コスト大 → 必要に応じて bucket 化も検討)
#     win_r = Window.orderBy(col(f"r_{suffix}").desc())
#     win_f = Window.orderBy(col(f"f_{suffix}"))
#     win_m = Window.orderBy(col(f"m_{suffix}"))

#     df_rfm = (
#         df_rfm
#         .withColumn(f"rscore_{suffix}", percent_rank().over(win_r))
#         .withColumn(f"fscore_{suffix}", percent_rank().over(win_f))
#         .withColumn(f"mscore_{suffix}", percent_rank().over(win_m))
#     )

#     df_rfm = df_rfm.withColumn(
#         f"rfm_score_{suffix}",
#         rfm_weights[0]*col(f"rscore_{suffix}") +
#         rfm_weights[1]*col(f"fscore_{suffix}") +
#         rfm_weights[2]*col(f"mscore_{suffix}")
#     )

#     df_rfm = df_rfm.withColumn(
#         f"rfm_score2_{suffix}",
#         when(
#             (col(f"rscore_{suffix}") != 0) &
#             (col(f"fscore_{suffix}") != 0) &
#             (col(f"mscore_{suffix}") != 0),
#             3 / (1/col(f"rscore_{suffix}") + 1/col(f"fscore_{suffix}") + 1/col(f"mscore_{suffix}"))
#         ).otherwise(lit(0))
#     )

#     return df_rfm.drop("last_date", "frequency", "monetary")

# def _add_feature_rfm(df_feat, df_lv5, df_jan, **kws):
#     fend = strdoffset(df_feat.select("astart").limit(1).collect()[0][0], -1)
#     rfm_jan = _make_rfm(df_jan, "jan", fend)
#     rfm_lv5 = _make_rfm(df_lv5, "lv5", fend)

#     if rfm_jan is not None:
#         df_feat = df_feat.join(rfm_jan, "uid", "left")
#     if rfm_lv5 is not None:
#         df_feat = df_feat.join(rfm_lv5, "uid", "left")
#     return df_feat

# # ------------------------
# # ロイヤリティ特徴量
# # ------------------------
# def _add_feature_roy(df_feat, df_lv5, df_jan, **kws):
#     return (
#         df_feat
#         .withColumn("jan_loy_m", F.when(col("m_lv5") != 0, col("m_jan")/col("m_lv5")).otherwise(0))
#         .withColumn("jan_loy_f", F.when(col("f_lv5") != 0, col("f_jan")/col("f_lv5")).otherwise(0))
#         .withColumn("jan_loy", (col("jan_loy_m")+col("jan_loy_f"))/2)
#     )

# # ------------------------
# # Pスコア特徴量
# # ------------------------
# def _add_feature_pscore(df_feat, df_lv5, df_jan, **kws):
#     """
#     Spark版 pscore 特徴量付与
#     """
#     df_det = kws['df_det']

#     # まず df_det に plv5_nm を生成
#     df_det = (
#         df_det
#         .withColumn("plv5_nm", create_plv5_udf(F.col("lv5_nm"), F.col("det_val")))
#         .drop("lv4_nm", "lv5_nm")  # pandas版と同じく lv4/lv5 は削除
#     )

#     # join: jan単位でplv5_nmを付与
#     df_feat = df_feat.join(
#         broadcast(df_det.select("jan", "plv5_nm")),
#         on="jan",
#         how="left"
#     )

#     # Spark版では df_lv5 / df_jan を別途処理していく流れに続ける
#     # （本来は make_pscore 相当を移植して詳細特徴量を作るが、まずは join 部分の整合性を取る）
#     return df_feat

# # ------------------------
# # カニバリスコア
# # ------------------------
# def _add_feature_kaniscore(df_feat, df_lv5, df_jan, **kws):
#     if df_jan.rdd.isEmpty() or df_lv5.rdd.isEmpty():
#         return df_feat.withColumn("kani_score", lit(0)).withColumn("kani_score_dis025", lit(0))

#     df_tamt = df_lv5.filter(col("jan")==df_feat.select("jan").limit(1).collect()[0][0]) \
#                     .groupBy("uid").agg(Fsum("salesamount").alias("tamt"))

#     df_other = df_lv5.filter(col("jan")!=df_feat.select("jan").limit(1).collect()[0][0]) \
#                      .groupBy("uid","jan").agg(Fsum("salesamount").alias("amt"))

#     df_score = df_other.join(df_tamt, "uid") \
#                        .withColumn("kani_score", (0.5 - Fabs((col("amt")/(col("amt")+col("tamt"))) - 0.5)) * 2)

#     df_score_sum = df_score.groupBy("jan").agg(Fsum("kani_score").alias("kani_score_sum"))
#     df_top5 = df_score_sum.withColumn("rank", row_number().over(Window.orderBy(col("kani_score_sum").desc()))).filter(col("rank") <= 5)
#     df_top5_mean = df_top5.agg(Fsum("kani_score_sum")/5).first()[0] if df_top5.count()>0 else 0.0

#     return (
#         df_feat
#         .withColumn("kani_score", lit(df_top5_mean))
#         .withColumn("kani_score_dis025", Fabs(lit(df_top5_mean)-0.25))
#     )

# # ------------------------
# # 各ケース特徴量生成
# # ------------------------
# def _add_feat_case(df_idpos, df_base, tjan, astart, verbose=False, **kws):
#     start_date = strdoffset(astart, -feature_len)
#     end_date = strdoffset(astart, -1)
#     df_period = df_idpos.filter((col("salesday") >= start_date) & (col("salesday") <= end_date))

#     row_vals = df_base.select("lv4_nm", "lv5_nm").limit(1).collect()
#     if not row_vals:
#         return None
#     lv4_target, lv5_target = row_vals[0]

#     df_lv5 = df_period.filter((col("lv4_nm")==lv4_target) & (col("lv5_nm")==lv5_target))
#     if df_lv5.rdd.isEmpty():
#         return None

#     df_jan = df_lv5.filter(col("jan")==tjan)

#     df_feat = df_base
#     for func in [_add_feature_price, _add_feature_rfm, _add_feature_roy, _add_feature_pscore, _add_feature_kaniscore]:
#         t0 = time.perf_counter()
#         df_feat = func(df_feat, df_lv5, df_jan, **kws)
#         if verbose:
#             print(f"{func.__name__} took {time.perf_counter()-t0:.2f}s")

#     return df_feat

# def _preprocess_idpos_data(df_idpos):
#     # フィルタリング
#     df_clean = df_idpos.filter((col("salesamount") > 0) & (col("uid") != "0"))
#     # 価格計算 & ノイズ除去
#     df_clean = (
#         df_clean.withColumn("price", col("salesamount") / col("salescnt"))
#                 .withColumn("salescnt", when(col("salescnt") > noise_max_cnt, noise_max_cnt)
#                                         .otherwise(col("salescnt")))
#                 .withColumn("salesamount", col("price") * col("salescnt"))
#     )

#     return df_clean

# # ------------------------
# # 店舗単位の特徴量生成
# # ------------------------
# def _add_feat_store(store_cd, df_base, df_det, verbose=False):
#     row_min, row_max = df_base.select(Fmin("astart"), Fmax("astart")).first()
#     if row_min is None or row_max is None:
#         return None

#     df_idpos = fetch_idpos(salesday=(strdoffset(row_min, -feature_len), row_max), lv3_nm='洋日配', storecd=store_cd)
#     df_idpos = _preprocess_idpos_data(df_idpos)

#     # det に lv4/lv5 情報を付与
#     jan_info = df_idpos.select("jan", "lv4_nm", "lv5_nm").dropDuplicates()
#     df_det = df_det.join(jan_info, "jan", "inner")

#     cases = df_base.select("jan", "astart").distinct().collect()
#     dfs = []
#     kws = {"df_det": df_det}

#     for row in cases:
#         res = _add_feat_case(df_idpos, df_base.filter((col("jan")==row["jan"]) & (col("astart")==row["astart"])), row["jan"], row["astart"], verbose=verbose, **kws)
#         if res is not None:
#             dfs.append(res)

#     if not dfs:
#         return None
#     return reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), dfs)

# # ------------------------
# # 全店舗の特徴量生成
# # ------------------------
# def add_features(df_base, df_det, verbose=False):
#     stores = [r.store_cd for r in df_base.select("store_cd").distinct().collect()]
#     dfs = []

#     for i, store in enumerate(stores, 1):
#         res = _add_feat_store(store, df_base.filter(col("store_cd")==store), df_det, verbose=verbose)
#         if res is not None:
#             dfs.append(res)
#         if verbose and i % 10 == 0:
#             print(f"processed {i} stores...")

#     if not dfs:
#         return spark.createDataFrame([], schema=df_base.schema)

#     return reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), dfs)


# COMMAND ----------

# # -*- coding: utf-8 -*-
# from pyspark.sql import functions as F
# from pyspark.sql import Window


# def add_features(df_base, df_idpos, df_det):
#     """
#     全店舗・全ケースを一括で特徴量付与する Spark 版

#     Parameters
#     ----------
#     df_base : Spark DataFrame
#         columns=['store_cd','lv4_nm','lv5_nm','jan','pprice','aprice','astart','uid', ...]
#     df_idpos : Spark DataFrame
#         idposデータ（全店舗・全期間を一括で取得したもの）
#         columns=['salesday','store_cd','jan','lv4_nm','lv5_nm','uid','salescnt','salesamount']
#     df_det : Spark DataFrame
#         kkk データ（det_val, lv5_nm 等が含まれる）

#     Returns
#     -------
#     df_feat : Spark DataFrame
#         df_base に各種特徴量を追加したもの
#     """

#     # -----------------------------
#     # 前処理: noise 除去
#     # -----------------------------
#     df_idpos = (df_idpos
#         .filter((F.col("salesamount") > 0) & (F.col("uid") != "0"))
#         .withColumn("price", F.col("salesamount")/F.col("salescnt"))
#         .withColumn("salescnt", F.when(F.col("salescnt") > noise_max_cnt, noise_max_cnt).otherwise(F.col("salescnt")))
#         .withColumn("salesamount", F.col("price") * F.col("salescnt"))
#     )

#     # -----------------------------
#     # 価格差分 (aprice - pprice)
#     # -----------------------------
#     df_feat = (df_base
#         .withColumn("dprice", F.col("aprice") - F.col("pprice"))
#         .withColumn("dprice_pct", (F.col("aprice") - F.col("pprice"))/F.col("pprice"))
#     )

#     # -----------------------------
#     # RFM (uid 単位)
#     # -----------------------------
#     # end 日付は case ごと → astart の前日を使う
#     df_rfm = (df_idpos
#         .groupBy("uid")
#         .agg(
#             F.max("salesday").alias("last_day"),
#             F.countDistinct("salesday").alias("f"),
#             F.sum("salesamount").alias("m")
#         )
#     )
#     # recency は join 後に astart に依存して計算する
#     df_feat = (df_feat
#         .join(df_rfm, on="uid", how="left")
#         .withColumn("r", F.datediff(F.col("astart"), F.col("last_day")))
#     )

#     # rank 正規化 (score 化)
#     w_r = Window.orderBy(F.col("r").desc())
#     w_f = Window.orderBy("f")
#     w_m = Window.orderBy("m")

#     df_feat = (df_feat
#         .withColumn("rscore", F.percent_rank().over(w_r))
#         .withColumn("fscore", F.percent_rank().over(w_f))
#         .withColumn("mscore", F.percent_rank().over(w_m))
#         .withColumn("rfm_score",
#             0.3*F.col("rscore") + 0.3*F.col("fscore") + 0.4*F.col("mscore")
#         )
#     )

#     # -----------------------------
#     # ROY (loyalty 指標)
#     # -----------------------------
#     # lv5単位集計
#     df_lv5 = (df_idpos.groupBy("uid","lv5_nm")
#         .agg(
#             F.sum("salesamount").alias("m_lv5"),
#             F.countDistinct("salesday").alias("f_lv5")
#         )
#     )
#     df_jan = (df_idpos.groupBy("uid","jan")
#         .agg(
#             F.sum("salesamount").alias("m_jan"),
#             F.countDistinct("salesday").alias("f_jan")
#         )
#     )
#     df_feat = (df_feat
#         .join(df_lv5, ["uid","lv5_nm"], "left")
#         .join(df_jan, ["uid","jan"], "left")
#         .withColumn("jan_loy_m", F.col("m_jan")/F.col("m_lv5"))
#         .withColumn("jan_loy_f", F.col("f_jan")/F.col("f_lv5"))
#         .withColumn("jan_loy", (F.col("jan_loy_m")+F.col("jan_loy_f"))/2)
#     )

#     # -----------------------------
#     # PScore
#     # -----------------------------
#     df_det = df_det.withColumn("plv5_nm", F.when(
#         (F.col("lv5_nm").isin(pscore_mod_lv5.keys())) &
#         (F.col("det_val") > pscore_mod_lv5[F.col("lv5_nm")]) &
#         (F.col("det_val") < pscore_multipkg_thd),
#         F.concat(F.col("lv5_nm"), F.lit("_L"))
#     ).otherwise(F.concat(F.col("lv5_nm"), F.lit("_S"))))

#     df_plv5 = (df_idpos.join(df_det, "jan"))
#     df_plv5 = df_plv5.withColumn("volumn", F.col("det_val")*F.col("salescnt"))

#     # cate, item, uid 単位の価格
#     df_pscore_uid = (df_plv5.groupBy("uid")
#         .agg(
#             (F.sum("salesamount")/F.sum("volumn")).alias("unitp_uid"),
#             F.countDistinct("salesday").alias("ndays")
#         )
#     )
#     df_pscore_item = (df_plv5.groupBy("jan")
#         .agg((F.sum("salesamount")/F.sum("volumn")).alias("unitp_item"))
#     )
#     df_pscore_cate = (df_plv5.groupBy("plv5_nm")
#         .agg((F.sum("salesamount")/F.sum("volumn")).alias("unitp_cate"))
#     )

#     df_feat = (df_feat
#         .join(df_pscore_uid, "uid", "left")
#         .join(df_pscore_item, "jan", "left")
#         .join(df_pscore_cate, "plv5_nm", "left")
#         .withColumn("pscore_item", (F.col("unitp_item")-F.col("unitp_cate"))/F.col("unitp_cate"))
#         .withColumn("pscore_ucate",
#             ( (F.col("unitp_uid")-F.col("unitp_cate"))/F.col("unitp_cate") ) *
#             F.when(F.col("ndays")/pscore_modify_ndays > 1, 1).otherwise(F.col("ndays")/pscore_modify_ndays)
#         )
#         .withColumn("pscore_ucate_dis050", (F.col("pscore_ucate")-0.5).abs())
#     )

#     # -----------------------------
#     # Kani Score (ライバル性)
#     # -----------------------------
#     # 競合 jan ごとの salesamount 比率を計算して window で評価
#     w_uid = Window.partitionBy("uid").orderBy(F.desc("salesamount"))
#     df_ranked = (df_idpos
#         .withColumn("rank_amt", F.rank().over(w_uid))
#     )
#     # 上位5つでスコア近似
#     df_kani = (df_ranked.filter(F.col("rank_amt")<=5)
#         .groupBy("jan").agg(F.avg("salesamount").alias("kani_score"))
#     )

#     df_feat = (df_feat
#         .join(df_kani, "jan", "left")
#         .withColumn("kani_score_dis025", (F.col("kani_score")-0.25).abs())
#     )

#     return df_feat


# COMMAND ----------

# -*- coding: utf-8 -*-
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType
from pyspark.sql.functions import udf, broadcast

spark = SparkSession.builder.getOrCreate()

# --------------------------
# helper: plv5 name creator (pandasの_create_plv5相当)
# --------------------------
def _create_plv5_py(lv5, det_val):
    if lv5 is None:
        return None
    if lv5 in pscore_mod_lv5:
        try:
            if det_val is not None and det_val > pscore_mod_lv5[lv5] and det_val < pscore_multipkg_thd:
                return lv5 + "_L"
            else:
                return lv5 + "_S"
        except Exception:
            return lv5
    else:
        return lv5

create_plv5_udf = udf(_create_plv5_py, StringType())

# --------------------------
# _add_feature_price (そのまま列追加)
# --------------------------
def _add_feature_price(df_base):
    return df_base.withColumn("dprice", F.col("aprice") - F.col("pprice")) \
                  .withColumn("dprice_pct", (F.col("aprice") - F.col("pprice")) / F.col("pprice"))

# --------------------------
# _make_rfm (全 uid 一括集計) と _add_feature_rfm（caseごとの astart を使って r を計算）
# --------------------------
def _make_rfm_all(df_idpos):
    """
    uidごとの last_day, f, m を一括計算する。
    """
    df_rfm = (df_idpos.groupBy("uid")
              .agg(
                  F.max("salesday").alias("last_day"),
                  F.countDistinct("salesday").alias("f"),
                  F.sum("salesamount").alias("m")
              ))
    return df_rfm

def _add_feature_rfm(df_feat, df_rfm):
    """
    df_feat に df_rfm を join して r（recency）を astart に基づき計算しスコア化する。
    """
    df = df_feat.join(df_rfm, on="uid", how="left")
    # r は astart の前日を目安にする（pandasの fend = strdoffset(astart, -1) と互換）
    # ここでは astart - last_day（日数差）を使う
    df = df.withColumn("r", F.datediff(F.col("astart"), F.col("last_day")))
    # percent_rank は全体の順位。元実装はケース毎だが重いため uid 全体でのpercent_rankを使う。
    w_r = Window.orderBy(F.col("r").desc())
    w_f = Window.orderBy(F.col("f"))
    w_m = Window.orderBy(F.col("m"))
    df = df.withColumn("rscore", F.percent_rank().over(w_r)) \
           .withColumn("fscore", F.percent_rank().over(w_f)) \
           .withColumn("mscore", F.percent_rank().over(w_m)) \
           .withColumn("rfm_score", 0.3*F.col("rscore")+0.3*F.col("fscore")+0.4*F.col("mscore"))
    # harmonic (safe: denom 0 guard)
    df = df.withColumn("rfm_score2",
                       F.when((F.col("rscore")>0) & (F.col("fscore")>0) & (F.col("mscore")>0),
                              3 / (1/F.col("rscore") + 1/F.col("fscore") + 1/F.col("mscore"))
                             ).otherwise(F.lit(0.0)))
    # drop intermediate last_day/f/m if not needed
    return df
# def _add_feature_rfm(df_feat, df_rfm):
#     """
#     df_feat に df_rfm を join して r（recency）を astart に基づき計算しスコア化する。
#     percent_rank() を使わず rank() + count() で再現。
#     """
#     df = df_feat.join(df_rfm, on="uid", how="left")

#     # r: recency（日数差）
#     df = df.withColumn("r", F.datediff(F.col("astart"), F.col("last_day")))

#     # 全体件数（N）
#     total_count = df.select(F.count("*").alias("n")).collect()[0]["n"]

#     # rank window 定義
#     w_r = Window.orderBy(F.col("r").desc())
#     w_f = Window.orderBy(F.col("f"))
#     w_m = Window.orderBy(F.col("m"))

#     # rank() + 正規化 (rank - 1)/(N - 1)
#     df = df.withColumn("r_rank", F.rank().over(w_r)) \
#            .withColumn("f_rank", F.rank().over(w_f)) \
#            .withColumn("m_rank", F.rank().over(w_m)) \
#            .withColumn("rscore", (F.col("r_rank") - 1) / F.lit(total_count - 1)) \
#            .withColumn("fscore", (F.col("f_rank") - 1) / F.lit(total_count - 1)) \
#            .withColumn("mscore", (F.col("m_rank") - 1) / F.lit(total_count - 1))

#     # 合成スコア
#     df = df.withColumn("rfm_score",
#                        0.3 * F.col("rscore") +
#                        0.3 * F.col("fscore") +
#                        0.4 * F.col("mscore"))

#     # harmonic (安全に計算)
#     df = df.withColumn(
#         "rfm_score2",
#         F.when(
#             (F.col("rscore") > 0) & (F.col("fscore") > 0) & (F.col("mscore") > 0),
#             3 / (1 / F.col("rscore") + 1 / F.col("fscore") + 1 / F.col("mscore"))
#         ).otherwise(F.lit(0.0))
#     )

#     # 不要列削除（任意）
#     df = df.drop("r_rank", "f_rank", "m_rank")

#     return df


# --------------------------
# _add_feature_roy（loyalty）: lv5, jan の集計を join で一括
# --------------------------
def _add_feature_roy(df_feat, df_idpos):
    # lv5単位の集計（uid, lv5_nm）
    df_lv5_agg = (df_idpos.groupBy("uid","lv5_nm")
                  .agg(F.sum("salesamount").alias("m_lv5"), F.countDistinct("salesday").alias("f_lv5")))
    # jan単位（uid, jan）
    df_jan_agg = (df_idpos.groupBy("uid","jan")
                  .agg(F.sum("salesamount").alias("m_jan"), F.countDistinct("salesday").alias("f_jan")))

    df = df_feat.join(df_lv5_agg, on=["uid","lv5_nm"], how="left") \
                .join(df_jan_agg, on=["uid","jan"], how="left") \
                .withColumn("jan_loy_m", F.when(F.col("m_lv5").isNotNull() & (F.col("m_lv5")!=0),
                                                 F.col("m_jan")/F.col("m_lv5")).otherwise(F.lit(0.0))) \
                .withColumn("jan_loy_f", F.when(F.col("f_lv5").isNotNull() & (F.col("f_lv5")!=0),
                                                 F.col("f_jan")/F.col("f_lv5")).otherwise(F.lit(0.0))) \
                .withColumn("jan_loy", (F.col("jan_loy_m")+F.col("jan_loy_f"))/2)
    return df

# --------------------------
# _make_pscore / _add_feature_pscore（一括版）
# --------------------------
def _make_pscore_all(df_idpos, df_det):
    """
    df_det に plv5_nm を付与し、df_idpos と join して unitp を計算。
    出力: df_pscore_uid (uid, unitp_uid, ndays), df_pscore_item (jan, unitp_item), df_pscore_cate (plv5_nm, unitp_cate)
    """
    # create plv5_nm in df_det
    df_det2 = (df_det.withColumn("plv5_nm", create_plv5_udf(F.col("lv5_nm"), F.col("det_val")))
                      .select("jan","plv5_nm","det_val"))
    # join idpos x det
    df_plv5 = df_idpos.join(df_det2, on="jan", how="inner")
    # volume = det_val * salescnt
    df_plv5 = df_plv5.withColumn("volumn", F.col("det_val") * F.col("salescnt"))
    # uid-level
    df_pscore_uid = (df_plv5.groupBy("uid","plv5_nm")
                     .agg(F.sum("salesamount").alias("uid_sales"),
                          F.sum("volumn").alias("uid_volumn"),
                          F.countDistinct("salesday").alias("ndays"))
                     .withColumn("unitp_uid", F.when(F.col("uid_volumn")>0, F.col("uid_sales")/F.col("uid_volumn")).otherwise(F.lit(0.0))))
    # jan-level (item)
    df_pscore_item = (df_plv5.groupBy("jan")
                      .agg(F.sum("salesamount").alias("item_sales"), F.sum("volumn").alias("item_volumn"))
                      .withColumn("unitp_item", F.when(F.col("item_volumn")>0, F.col("item_sales")/F.col("item_volumn")).otherwise(F.lit(0.0))))
    # category-level (plv5)
    df_pscore_cate = (df_plv5.groupBy("plv5_nm")
                      .agg(F.sum("salesamount").alias("cate_sales"), F.sum("volumn").alias("cate_volumn"))
                      .withColumn("unitp_cate", F.when(F.col("cate_volumn")>0, F.col("cate_sales")/F.col("cate_volumn")).otherwise(F.lit(0.0))))
    return df_pscore_uid, df_pscore_item, df_pscore_cate, df_det2

def _add_feature_pscore(df_feat, df_idpos, df_det):
    df_pscore_uid, df_pscore_item, df_pscore_cate, df_det2 = _make_pscore_all(df_idpos, df_det)
    # join: df_feat は (uid, jan, plv5_nm がないなら df_det2 で作る)
    df_feat = df_feat.join(broadcast(df_det2.select("jan","plv5_nm")), on="jan", how="left")
    # join uid-level (注意: uid-level has plv5_nm partition; join on uid & plv5_nm)
    df_feat = df_feat.join(df_pscore_uid.select("uid","plv5_nm","unitp_uid","ndays"),
                           on=["uid","plv5_nm"], how="left")
    df_feat = df_feat.join(df_pscore_item.select("jan","unitp_item"), on="jan", how="left")
    df_feat = df_feat.join(df_pscore_cate.select("plv5_nm","unitp_cate"), on="plv5_nm", how="left")

    # compute pscore fields with guards
    df_feat = df_feat.withColumn("pscore_item",
                                F.when(F.col("unitp_cate").isNotNull() & (F.col("unitp_cate") != 0),
                                       (F.col("unitp_item") - F.col("unitp_cate"))/F.col("unitp_cate")).otherwise(F.lit(0.0)))
    df_feat = df_feat.withColumn("pscore_ucate",
                                F.when(F.col("unitp_cate").isNotNull() & (F.col("unitp_cate") != 0),
                                       (F.col("unitp_uid") - F.col("unitp_cate"))/F.col("unitp_cate") *
                                       (F.least(F.col("ndays")/F.lit(pscore_modify_ndays), F.lit(1.0))).cast("double"))
                                .otherwise(F.lit(0.0)))
    df_feat = df_feat.withColumn("pscore_ucate_dis050", F.abs(F.col("pscore_ucate") - F.lit(0.5)))
    return df_feat

# --------------------------
# Kani score（近似、一括）
# pandasの per-uid ループ版を Spark で近似再現（計算量を抑える）
# --------------------------
def _add_feature_kaniscore(df_feat, df_idpos):
    """
    近似アルゴリズム：
      - df_idpos を lv5 単位で集約して uid-janごとの売上を作る
      - 各 uid について tjan の売上合計(tamt) と他janの売上(amt) を結合して 
        ratio = amt / (amt + tamt) を算出、jごとに (0.5 - abs(ratio-0.5))*2 を kani_j とする
      - 各 jan ごとに uid 毎の kani_j * tamt を合計して wall で正規化
      - 上位5 competitor の単純平均を kani_score とする（pandas 実装の近似）
    """
    # uid-jan totals within same lv5
    df_uid_jan = (df_idpos.groupBy("uid","lv5_nm","jan").agg(F.sum("salesamount").alias("amt_uid_jan")))
    # tamt: uidごとの target-jan売上（will be joined per tjan later）
    # To compute for all tjan at once, self-join: for each pair (tjan, other_jan) per uid within same lv5
    df_pair = df_uid_jan.alias("A").join(df_uid_jan.alias("B"),
                                         (F.col("A.uid")==F.col("B.uid")) &
                                         (F.col("A.lv5_nm")==F.col("B.lv5_nm")) &
                                         (F.col("A.jan") != F.col("B.jan")),
                                         how="inner") \
                 .select(F.col("A.uid").alias("uid"),
                         F.col("A.lv5_nm").alias("lv5_nm"),
                         F.col("A.jan").alias("tjan"),
                         F.col("B.jan").alias("competitor_jan"),
                         F.col("A.amt_uid_jan").alias("tamt"),
                         F.col("B.amt_uid_jan").alias("amt"))
    # compute per-row kani_j = (0.5 - abs(amt/(amt+tamt) - 0.5))*2; guard divide-by-zero
    df_pair = df_pair.withColumn("ratio", F.when((F.col("amt")+F.col("tamt"))>0, F.col("amt")/(F.col("amt")+F.col("tamt"))).otherwise(F.lit(0.5)))
    df_pair = df_pair.withColumn("kani_j", (F.lit(0.5) - F.abs(F.col("ratio") - F.lit(0.5))) * F.lit(2.0))
    # weight by tamt as in pandas (kani_j * tamt)
    df_pair = df_pair.withColumn("kami_weighted", F.col("kani_j") * F.col("tamt"))
    # sum per (tjan, competitor_jan) across uids
    df_comp_sum = (df_pair.groupBy("tjan","competitor_jan")
                   .agg(F.sum("kami_weighted").alias("score_weighted")))
    # sum per tjan total wall = sum of tamt (approx by sum over uid tamt for tjan)
    df_tamt_total = (df_uid_jan.groupBy("jan").agg(F.sum("amt_uid_jan").alias("wall"))).withColumnRenamed("jan","tjan")
    # compute normalized per competitor: score_weighted / wall
    df_comp_norm = df_comp_sum.join(df_tamt_total, on="tjan", how="left") \
                    .withColumn("norm_score", F.when(F.col("wall")>0, F.col("score_weighted")/F.col("wall")).otherwise(F.lit(0.0)))
    # aggregate top-5 competitor norm_score into final kani_score per tjan (approx)
    w_comp = Window.partitionBy("tjan").orderBy(F.desc("norm_score"))
    df_topk = df_comp_norm.withColumn("rank", F.row_number().over(w_comp)).filter(F.col("rank")<=5)
    df_kani_score = (df_topk.groupBy("tjan").agg((F.sum("norm_score")/F.lit(5.0)).alias("kani_score")))
    # join kani_score to df_feat on jan == tjan
    df_feat2 = df_feat.join(df_kani_score.withColumnRenamed("tjan","jan"), on="jan", how="left") \
                      .withColumn("kani_score", F.when(F.col("kani_score").isNull(), F.lit(0.0)).otherwise(F.col("kani_score"))) \
                      .withColumn("kani_score_dis025", F.abs(F.col("kani_score") - F.lit(0.25)))
    return df_feat2

# --------------------------
# 全体統合関数: ループなしで df_base に特徴量を付与
# --------------------------
def add_features(df_base, df_idpos, df_det, verbose=False):
    """
    df_base: base cases (Spark DF) with columns including store_cd, lv4_nm, lv5_nm, jan, pprice, aprice, astart, uid, ...
    df_idpos: idpos Spark DF covering union of required periods and stores (pre-fetched)
    df_det: det/master spark DF (kkk) containing jan, lv5_nm, det_val ...
    """
    t0 = F.current_timestamp()
    # 1) price features
    df_feat = _add_feature_price(df_base)

    # 2) prepare df_idpos: filter & noise handling (do once)
    df_idpos_clean = (df_idpos.filter((F.col("salesamount")>0) & (F.col("uid").isNotNull()))
                                 .withColumn("price", F.floor(F.col("salesamount")/F.col("salescnt")).cast("double"))
                                 .withColumn("salescnt", F.when(F.col("salescnt")>noise_max_cnt, noise_max_cnt).otherwise(F.col("salescnt")))
                                 .withColumn("salesamount", F.col("price") * F.col("salescnt")))

    # 3) RFM: uid 単位集計（last_day, f, m）
    df_rfm = _make_rfm_all(df_idpos_clean)
    df_feat = _add_feature_rfm(df_feat, df_rfm)

    # 4) ROY
    df_feat = _add_feature_roy(df_feat, df_idpos_clean)

    # 5) PScore: will also generate plv5_nm in df_det
    df_feat = _add_feature_pscore(df_feat, df_idpos_clean, df_det)

    # 6) Kani score approx
    df_feat = _add_feature_kaniscore(df_feat, df_idpos_clean)

    # 7) fill nulls for numeric features to safe defaults
    num_fill = {c:0.0 for c in ["dprice","dprice_pct","rscore","fscore","mscore","rfm_score","rfm_score2",
                                "jan_loy_m","jan_loy_f","jan_loy","pscore_item","pscore_ucate","pscore_ucate_dis050",
                                "kani_score","kani_score_dis025"]}
    df_feat = df_feat.fillna(num_fill)

    return df_feat


# COMMAND ----------

