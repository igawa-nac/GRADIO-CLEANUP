# Databricks notebook source
# MAGIC %run ./Sp_config.py

# COMMAND ----------

# MAGIC %run ./Sp_io.py

# COMMAND ----------

# MAGIC %run ./Sp_utils.py

# COMMAND ----------

# # -*- coding: utf-8 -*-
# from pyspark.sql import functions as F
# from pyspark.sql import Window

# def sample_uid(df_case, label=False, case_period=None, stores=None):
#     """
#     Spark版 sampling base table.

#     Parameters
#     ----------
#     df_case: pyspark.sql.DataFrame
#         columns = ['store_cd','lv4_nm','lv5_nm','jan','pprice','aprice','astart']
#     label: bool
#     case_period: tuple(str, str)
#     stores: list[int]

#     Returns
#     -------
#     df_base: pyspark.sql.DataFrame
#     """

#     # 1. idposをまとめて取得（全store分）
#     df_idpos = fetch_idpos(
#         salesday=case_period,
#         lv3_nm="洋日配",
#         storecd=stores
#     )

#     # カラム名調整
#     df_idpos = df_idpos.withColumnRenamed("storecd", "store_cd")

#     # ノイズ除去
#     df_idpos = (
#         df_idpos
#         .withColumn("price", (F.col("salesamount")/F.col("salescnt")).cast("int"))
#         .withColumn("salescnt", F.when(F.col("salescnt") > noise_max_cnt, noise_max_cnt).otherwise(F.col("salescnt")))
#         .withColumn("salesamount", F.col("price")*F.col("salescnt"))
#     )

#     # 2. sample期間の計算（caseごと）
#     df_case = (
#         df_case
#         .withColumn("sample_start", strdoffset_col(F.col("astart"), -sample_len))
#         .withColumn("sample_end", strdoffset_col(F.col("astart"), -1))
#     )

#     # 3. sample集計
#     df_join_sample = (
#         df_case.alias("c")
#         .join(df_idpos.alias("i"),
#               (F.col("c.store_cd")==F.col("i.store_cd")) &
#               (F.col("c.lv4_nm")==F.col("i.lv4_nm")) &
#               (F.col("c.lv5_nm")==F.col("i.lv5_nm")) &
#               (F.col("c.jan")==F.col("i.jan")),
#               "inner")
#         .filter((F.col("i.salesday")>=F.col("c.sample_start")) & (F.col("i.salesday")<=F.col("c.sample_end")))
#         .groupBy("c.store_cd","c.lv4_nm","c.lv5_nm","c.jan","c.pprice","c.aprice","c.astart","i.uid")
#         .agg(F.sum("i.salesamount").alias("sample_amt_jan"))
#     )

#     df_ret = df_join_sample

#     # 4. label付与
#     if label:
#         df_case_label = (
#             df_case
#             .withColumn("label_start", strdoffset_col(F.col("astart"), interval_len))
#             .withColumn("label_end", strdoffset_col(F.col("label_start"), label_len-1))
#         )

#         # label_jan
#         df_label_jan = (
#             df_case_label.alias("c")
#             .join(df_idpos.alias("i"),
#                   (F.col("c.store_cd")==F.col("i.store_cd")) &
#                   (F.col("c.lv4_nm")==F.col("i.lv4_nm")) &
#                   (F.col("c.lv5_nm")==F.col("i.lv5_nm")) &
#                   (F.col("c.jan")==F.col("i.jan")),
#                   "inner")
#             .filter((F.col("i.salesday")>=F.col("c.label_start")) & (F.col("i.salesday")<=F.col("c.label_end")))
#             .select("c.store_cd","c.lv4_nm","c.lv5_nm","c.jan","i.uid")
#             .distinct()
#             .withColumn("label_jan", F.lit(True))
#         )

#         # label_lv5
#         df_label_lv5 = (
#             df_case_label.alias("c")
#             .join(df_idpos.alias("i"),
#                   (F.col("c.store_cd")==F.col("i.store_cd")) &
#                   (F.col("c.lv4_nm")==F.col("i.lv4_nm")) &
#                   (F.col("c.lv5_nm")==F.col("i.lv5_nm")),
#                   "inner")
#             .filter((F.col("i.salesday")>=F.col("c.label_start")) & (F.col("i.salesday")<=F.col("c.label_end")))
#             .select("c.store_cd","c.lv4_nm","c.lv5_nm","i.uid")
#             .distinct()
#             .withColumn("label_lv5", F.lit(True))
#         )

#         # joinして付与
#         df_ret = (
#             df_ret
#             .join(df_label_jan, ["store_cd","lv4_nm","lv5_nm","jan","uid"], "left")
#             .join(df_label_lv5, ["store_cd","lv4_nm","lv5_nm","uid"], "left")
#             .fillna({"label_jan": False, "label_lv5": False})
#         )

#     return df_ret


# COMMAND ----------

# -*- coding: utf-8 -*-
from pyspark.sql import functions as F
from pyspark.sql import Window

def sample_uid(df_case, label=False, case_period=None, stores=None):
    """
    最適化版Spark sampling base table.
    
    全体期間でidposを一度に取得してからフィルタリングする効率的な実装
    """

    # 1. 全体の期間を計算
    case_stats = df_case.agg(
        F.min("astart").alias("global_min_astart"),
        F.max("astart").alias("global_max_astart")
    ).collect()[0]
    
    global_start = strdoffset(case_stats["global_min_astart"], -sample_len)
    global_end = strdoffset(case_stats["global_max_astart"], interval_len + label_len)
    
    # 2. 全期間・全storeのidposを一度に取得
    df_idpos = fetch_idpos(
        salesday=(global_start, global_end),
        lv3_nm="洋日配",
        storecd=stores
    )
    
    # カラム名調整
    df_idpos = df_idpos.withColumnRenamed("storecd", "store_cd")

    # 3. Pandas版と同じフィルタリング
    df_idpos = df_idpos.filter(
        (F.col("salesamount") > 0) & 
        (F.col("uid").isNotNull())
    )

    # 4. ノイズ除去（整数除算）
    df_idpos = (
        df_idpos
        .withColumn("price", F.floor(F.col("salesamount") / F.col("salescnt")).cast("int"))
        .withColumn("salescnt", F.when(F.col("salescnt") > noise_max_cnt, noise_max_cnt).otherwise(F.col("salescnt")))
        .withColumn("salesamount", F.col("price") * F.col("salescnt"))
    )

    # 5. 各caseごとのstoreの期間範囲でフィルタリング
    df_store_periods = (
        df_case
        .groupBy("store_cd")
        .agg(
            F.min("astart").alias("min_astart"),
            F.max("astart").alias("max_astart")
        )
        .withColumn("idpos_start", strdoffset_col(F.col("min_astart"), -sample_len))
        .withColumn("idpos_end", strdoffset_col(F.col("max_astart"), interval_len+label_len))
    )
    
    # idposをstore期間でフィルタリング
    df_idpos_filtered = (
        df_idpos.alias("i")
        .join(df_store_periods.alias("sp"), F.col("i.store_cd") == F.col("sp.store_cd"), "inner")
        .filter(
            (F.col("i.salesday") >= F.col("sp.idpos_start")) &
            (F.col("i.salesday") <= F.col("sp.idpos_end"))
        )
        .select("i.*")
    )

    # 6. sample期間の計算（caseごと）
    df_case = (
        df_case
        .withColumn("sample_start", strdoffset_col(F.col("astart"), -sample_len))
        .withColumn("sample_end", strdoffset_col(F.col("astart"), -1))
    )

    # 7. sample集計
    df_join_sample = (
        df_case.alias("c")
        .join(df_idpos_filtered.alias("i"),
              (F.col("c.store_cd")==F.col("i.store_cd")) &
              (F.col("c.lv4_nm")==F.col("i.lv4_nm")) &
              (F.col("c.lv5_nm")==F.col("i.lv5_nm")) &
              (F.col("c.jan")==F.col("i.jan")),
              "inner")
        .filter((F.col("i.salesday")>=F.col("c.sample_start")) & (F.col("i.salesday")<=F.col("c.sample_end")))
        .groupBy("c.store_cd","c.lv4_nm","c.lv5_nm","c.jan","c.pprice","c.aprice","c.astart","i.uid")
        .agg(F.sum("i.salesamount").alias("sample_amt_jan"))
    )

    df_ret = df_join_sample

    # 8. label付与
    if label:
        df_case_label = (
            df_case
            .withColumn("label_start", strdoffset_col(F.col("astart"), interval_len))
            .withColumn("label_end", strdoffset_col(F.col("label_start"), label_len-1))
        )

        # label_jan
        df_label_jan = (
            df_case_label.alias("c")
            .join(df_idpos_filtered.alias("i"),
                  (F.col("c.store_cd")==F.col("i.store_cd")) &
                  (F.col("c.lv4_nm")==F.col("i.lv4_nm")) &
                  (F.col("c.lv5_nm")==F.col("i.lv5_nm")) &
                  (F.col("c.jan")==F.col("i.jan")),
                  "inner")
            .filter((F.col("i.salesday")>=F.col("c.label_start")) & (F.col("i.salesday")<=F.col("c.label_end")))
            .select("c.store_cd","c.lv4_nm","c.lv5_nm","c.jan","i.uid")
            .distinct()
            .withColumn("label_jan", F.lit(True))
        )

        # label_lv5
        df_label_lv5 = (
            df_case_label.alias("c")
            .join(df_idpos_filtered.alias("i"),
                  (F.col("c.store_cd")==F.col("i.store_cd")) &
                  (F.col("c.lv4_nm")==F.col("i.lv4_nm")) &
                  (F.col("c.lv5_nm")==F.col("i.lv5_nm")),
                  "inner")
            .filter((F.col("i.salesday")>=F.col("c.label_start")) & (F.col("i.salesday")<=F.col("c.label_end")))
            .select("c.store_cd","c.lv4_nm","c.lv5_nm","i.uid")
            .distinct()
            .withColumn("label_lv5", F.lit(True))
        )

        # joinして付与
        df_ret = (
            df_ret
            .join(df_label_jan, ["store_cd","lv4_nm","lv5_nm","jan","uid"], "left")
            .join(df_label_lv5, ["store_cd","lv4_nm","lv5_nm","uid"], "left")
            .fillna({"label_jan": False, "label_lv5": False})
        )

    return df_ret