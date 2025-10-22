# Databricks notebook source
# MAGIC %run ./Sp_config.py

# COMMAND ----------

# MAGIC %run ./Sp_io.py

# COMMAND ----------

# MAGIC %run ./Sp_utils.py

# COMMAND ----------

# MAGIC %md
# MAGIC 実行中のコード

# COMMAND ----------

# -*- coding: utf-8 -*-
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window
import pandas as pd
import numpy as np
from functools import reduce


def _fetch_idpos(period, store_cd):
    """
    fetch idpos, select rows and columns, add price column.
    """
    df_idpos = fetch_idpos(
        storecd=store_cd, 
        lv3_nm='洋日配', 
        salesday=period
    )
    
    spark = SparkSession.getActiveSession()
    
    if not hasattr(df_idpos, 'filter'):
        df_idpos = spark.createDataFrame(df_idpos)
    
    # 早期フィルタリングで不要データを削除 + キャッシュ
    df_result = (df_idpos
                 .filter((F.col('salesamount') > 0) & (F.col('salescnt') > 0))
                 .select('salesday', 'lv4_nm', 'lv5_nm', 'jan', 
                        'salescnt', 'salesamount')
                 .withColumn('price', F.round(F.col('salesamount') / F.col('salescnt'), 2))
                 .cache())
    
    return df_result


def _make_day_jan_price_pos(df_idpos):
    """
    Returns Spark DataFrame(columns=['salesday', 'jan', 'price', 'pos']).
    """
    result = (df_idpos
             .groupBy('salesday', 'jan', 'price')
             .count()
             .withColumnRenamed('count', 'pos')
             .cache())
    
    return result


def _parse_priceperiod_jan(df_jan):
    """
    parse priceperiod of one jan using Spark operations.
    
    Parameters
    ----------
    df_jan: Spark DataFrame(columns=['salesday', 'jan', 'price', 'pos']).
    
    Returns
    -------
    Spark DataFrame(columns=['jan', 'start', 'end', 'price', 'pos']).
    """
    window_spec = Window.partitionBy('jan').orderBy('salesday')
    
    df_with_changes = (df_jan
        .withColumn('prev_price', F.lag('price').over(window_spec))
        .withColumn('price_changed', 
                   F.when(F.col('price') != F.coalesce(F.col('prev_price'), F.col('price')), 1)
                   .otherwise(0))
        .withColumn('group_id', F.sum('price_changed').over(window_spec)))
    
    result = (df_with_changes
             .groupBy('jan', 'group_id', 'price')
             .agg(
                 F.min('salesday').alias('start'),
                 F.max('salesday').alias('end'),
                 F.sum('pos').alias('pos')
             )
             .filter(F.col('pos') > 0)
             .select('jan', 'start', 'end', 'price', 'pos'))
    
    return result


def _make_price_period(df_price):
    """
    最大の性能問題を解決: collectとfor文を排除
    Returns Spark DataFrame(columns=['jan', 'start', 'end', 'price', 'pos', 'plen']).
    """
    spark = SparkSession.getActiveSession()
    
    # collectを完全に排除し、全JANを一度に処理
    df_priceperiod = _parse_priceperiod_jan(df_price)
    
    if df_priceperiod.count() == 0:
        schema = StructType([
            StructField('jan', StringType(), True),
            StructField('start', DateType(), True),
            StructField('end', DateType(), True),
            StructField('price', DoubleType(), True),
            StructField('pos', LongType(), True),
            StructField('plen', IntegerType(), True)
        ])
        return spark.createDataFrame([], schema)
    
    # 期間長計算
    df_priceperiod = (df_priceperiod
                     .withColumn('plen', F.datediff(F.col('end'), F.col('start')) + 1)
                     .cache())
    
    return df_priceperiod


def _make_case_up(df_pricep):
    """
    Spark版: 価格上昇ケースの作成（最適化）
    """
    spark = SparkSession.getActiveSession()
    
    try:
        thd_plen_val = thd_plen
        thd_alen_val = thd_alen
    except NameError:
        thd_plen_val = 75
        thd_alen_val = 45
    
    # 早期フィルタリングで処理対象を絞る
    df_filtered_early = df_pricep.filter(F.col('plen') >= thd_plen_val)
    
    window_spec = Window.partitionBy('jan').orderBy('start')
    
    df_with_next = (df_filtered_early
        .withColumn('next_start', F.lead('start').over(window_spec))
        .withColumn('next_end', F.lead('end').over(window_spec))
        .withColumn('next_price', F.lead('price').over(window_spec))
        .withColumn('next_pos', F.lead('pos').over(window_spec))
        .withColumn('next_plen', F.lead('plen').over(window_spec)))
    
    df_filtered = (df_with_next
        .filter(F.col('next_start').isNotNull())
        .withColumn('time_gap', F.datediff(F.col('next_start'), F.col('end')))
        .filter(
            (F.col('price') != F.col('next_price')) &
            (F.col('price') < F.col('next_price')) &
            (F.col('time_gap') <= 3) &
            (F.col('next_plen') >= thd_alen_val)
        ))
    
    df_case = (df_filtered
        .select(
            F.col('jan').alias('jan'),
            F.col('start').alias('pstart'),
            F.col('end').alias('pend'),
            F.col('next_start').alias('astart'),
            F.col('next_end').alias('aend'),
            F.col('price').alias('pprice'),
            F.col('next_price').alias('aprice'),
            F.col('pos').alias('ppos'),
            F.col('next_pos').alias('apos'),
            F.col('plen').alias('pplen'),
            F.col('next_plen').alias('aplen')
        ))
    
    return df_case


# def _make_case_zero(df_pricep):
#     """
#     Spark版: 価格据え置きケースの作成（最適化）
#     """
#     spark = SparkSession.getActiveSession()
    
#     try:
#         thd_plen_val = thd_plen
#         thd_alen_val = thd_alen
#     except NameError:
#         thd_plen_val = 75
#         thd_alen_val = 45
    
#     le = thd_plen_val + thd_alen_val
    
#     df_valid = df_pricep.filter(F.datediff(F.col('end'), F.col('start')) >= le + 6)
    
#     df_case = (df_valid
#         .withColumn('type', F.lit('same'))
#         .withColumn('astart', F.date_add(F.col('start'), 7 + thd_plen_val))
#         .withColumn('pprice', F.col('price'))
#         .withColumn('aprice', F.col('price'))
#         .select('jan', 'type', 'astart', 'pprice', 'aprice'))
    
#     return df_case

# 10/10変更し実行済み、14日に出力を確認
def _make_case_zero(df_pricep):
    """
    Spark版: 価格据え置きケースの作成（Pandas版と同等の複数ケース生成）
    """
    spark = SparkSession.getActiveSession()

    try:
        thd_plen_val = thd_plen
        thd_alen_val = thd_alen
    except NameError:
        thd_plen_val = 75
        thd_alen_val = 45

    # Pandas版と同様に必要な期間長を設定
    le = thd_plen_val + thd_alen_val
    step = 42  # Pandas版の _roll_cases_in_one_case() と同じ周期

    # 一定期間以上続いた価格のみ対象
    df_valid = df_pricep.filter(F.datediff(F.col('end'), F.col('start')) >= le + 6)

    # 期間内でstep日ごとにcur日を生成（start+7日からendまで）
    df_case = (
        df_valid
        .withColumn(
            "cur_dates",
            F.sequence(
                F.date_add(F.col("start"), 7),   # 価格変化直後の7日間をスキップ
                F.col("end"),
                F.expr(f"interval {step} days")  # 42日ごとに1ケース
            )
        )
        # 各curに対して仮想的な値上げ開始日（astart = cur + thd_plen）
        .withColumn(
            "astart_array",
            F.expr(f"transform(cur_dates, x -> date_add(x, {thd_plen_val}))")
        )
        # 複数a_startを1行ずつに展開
        .withColumn("astart", F.explode("astart_array"))
        # 期間外（end超過）のものは除外
        .filter(F.col("astart") <= F.col("end"))
        # 他の列を整形
        .withColumn("type", F.lit("same"))
        .withColumn("pprice", F.col("price"))
        .withColumn("aprice", F.col("price"))
        .select("jan", "type", "astart", "pprice", "aprice")
    )

    return df_case



def get_casemaster(case_period, store_cd, case_type):
    """
    get casemaster from idpos for training.
    完全Spark版（大幅最適化）
    
    Parameters
    ----------
    case_period: tuple(str, str), yyyy-mm-dd.
        period of cases.
    store_cd: int.
    case_type: str.
        {'up', 'zero'}.
    
    Returns
    -------
    Spark DataFrame(columns=['store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'pprice', 'aprice', 'astart'])
    """
    spark = SparkSession.getActiveSession()
    
    try:
        thd_plen_val = thd_plen
        thd_alen_val = thd_alen
    except NameError:
        thd_plen_val = 75
        thd_alen_val = 45
    
    period_idpos = (
        strdoffset(case_period[0], -thd_plen_val-10),
        strdoffset(case_period[1], thd_alen_val+10)
    )
    
    # パーティション数を調整してパフォーマンス向上
    df_idpos = _fetch_idpos(period_idpos, store_cd)
    
    # 必要な列のみを早期に選択してメモリ使用量を削減
    df_lvmst = (df_idpos
               .select('lv4_nm', 'lv5_nm', 'jan')
               .distinct()
               .cache())
    
    df_price = _make_day_jan_price_pos(df_idpos)
    df_pricep = _make_price_period(df_price)
    
    if case_type=='up':
        _make_case = _make_case_up
    elif case_type=='zero':
        _make_case = _make_case_zero
    else:
        raise ValueError(f"Invalid case_type: {case_type}")
    
    df_tmp = _make_case(df_pricep)

    # count()をfirst()に変更して性能向上
    if df_tmp.first() is None:
        schema = StructType([
            StructField('store_cd', IntegerType(), True),
            StructField('lv4_nm', StringType(), True),
            StructField('lv5_nm', StringType(), True),
            StructField('jan', StringType(), True),
            StructField('pprice', DoubleType(), True),
            StructField('aprice', DoubleType(), True),
            StructField('astart', StringType(), True)
        ])
        return spark.createDataFrame([], schema)

    # broadcast joinを使用して小さいテーブルをブロードキャスト
    df_case = (df_tmp
               .join(F.broadcast(df_lvmst), on='jan', how='left')
               .withColumn('store_cd', F.lit(store_cd)))

    df_case = df_case.withColumn(
        'astart', 
        F.date_format(F.col('astart'), 'yyyy-MM-dd')
    )
    
    df_case = df_case.select(
        'store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'pprice', 'aprice', 'astart'
    )
    
    return df_case


def make_casemaster(store_cd, jans, upday, dprice):
    """
    完全Spark版（最適化）
    """
    spark = SparkSession.getActiveSession()
    
    try:
        thd_plen_val = thd_plen
    except NameError:
        thd_plen_val = 75
    
    period_idpos = (
        strdoffset(upday, -thd_plen_val),
        strdoffset(upday, -1)
    )
    
    df_idpos = _fetch_idpos(period_idpos, store_cd)
    
    # broadcast変数は不要な場合が多い（isinで十分効率的）
    df_filtered = df_idpos.filter(F.col('jan').isin(jans))
    
    # 集約処理を最適化
    jan_price_counts = (df_filtered
                       .groupBy('jan')
                       .agg(F.countDistinct('price').alias('price_count'))
                       .cache())
    
    single_price_jans = (jan_price_counts
                        .filter(F.col('price_count') == 1)
                        .select('jan'))
    
    # broadcast joinで性能向上
    df_case = (df_filtered
               .join(F.broadcast(single_price_jans), on='jan', how='inner')
               .select('lv4_nm', 'lv5_nm', 'jan', 'price')
               .distinct()
               .withColumn('pprice', F.col('price'))
               .withColumn('aprice', F.col('price') + dprice)
               .withColumn('store_cd', F.lit(store_cd))
               .withColumn('astart', F.lit(upday))
               .drop('price'))
    
    return df_case

# COMMAND ----------

# # -*- coding: utf-8 -*-
# from pyspark.sql import SparkSession, functions as F
# from pyspark.sql.types import *
# from pyspark.sql.window import Window

# def _fetch_idpos(period, store_cd):
#     """
#     fetch idpos, select rows and columns, add price column.
#     Returns Spark DataFrame
#     """
#     df_idpos = fetch_idpos(storecd=store_cd, lv3_nm='洋日配', salesday=period)
#     spark = SparkSession.getActiveSession()
    
#     # pandas DataFrameならSparkに変換
#     if not hasattr(df_idpos, 'filter'):
#         df_idpos = spark.createDataFrame(df_idpos)
    
#     df_result = (
#         df_idpos
#         .filter((F.col('salesamount') > 0) & (F.col('salescnt') > 0))
#         .select('salesday', 'lv4_nm', 'lv5_nm', 'jan', 'salescnt', 'salesamount')
#         .withColumn('price', F.round(F.col('salesamount') / F.col('salescnt'), 2))
#         .cache()
#     )
#     return df_result

# def _make_day_jan_price_pos(df_idpos):
#     """
#     Returns Spark DataFrame(columns=['salesday', 'jan', 'price', 'pos']).
#     """
#     return df_idpos.groupBy('salesday', 'jan', 'price')\
#                    .agg(F.count('*').alias('pos'))\
#                    .cache()

# def _parse_priceperiod_jan(df_jan):
#     """
#     parse price period of one jan in Spark.
#     """
#     window_spec = Window.partitionBy('jan').orderBy('salesday')
#     df_with_lag = (
#         df_jan
#         .withColumn('prev_price', F.lag('price').over(window_spec))
#         .withColumn('price_change', F.when(F.col('price') != F.coalesce(F.col('prev_price'), F.col('price')), 1).otherwise(0))
#         .withColumn('group_id', F.sum('price_change').over(window_spec))
#     )
    
#     df_period = (
#         df_with_lag.groupBy('jan', 'group_id', 'price')
#         .agg(
#             F.min('salesday').alias('start'),
#             F.max('salesday').alias('end'),
#             F.sum('pos').alias('pos')
#         )
#         .filter(F.col('pos') > 0)
#         .withColumn('plen', F.datediff(F.col('end'), F.col('start')) + 1)
#         .select('jan', 'start', 'end', 'price', 'pos', 'plen')
#     )
#     return df_period
    
# def _make_case_up(df_pricep):
#     """
#     Spark版: 価格上昇ケースの作成（最適化）
#     """
#     spark = SparkSession.getActiveSession()
    
#     try:
#         thd_plen_val = thd_plen
#         thd_alen_val = thd_alen
#     except NameError:
#         thd_plen_val = 75
#         thd_alen_val = 45
    
#     # 早期フィルタリングで処理対象を絞る
#     df_filtered_early = df_pricep.filter(F.col('plen') >= thd_plen_val)
    
#     window_spec = Window.partitionBy('jan').orderBy('start')
    
#     df_with_next = (df_filtered_early
#         .withColumn('next_start', F.lead('start').over(window_spec))
#         .withColumn('next_end', F.lead('end').over(window_spec))
#         .withColumn('next_price', F.lead('price').over(window_spec))
#         .withColumn('next_pos', F.lead('pos').over(window_spec))
#         .withColumn('next_plen', F.lead('plen').over(window_spec)))
    
#     df_filtered = (df_with_next
#         .filter(F.col('next_start').isNotNull())
#         .withColumn('time_gap', F.datediff(F.col('next_start'), F.col('end')))
#         .filter(
#             (F.col('price') != F.col('next_price')) &
#             (F.col('price') < F.col('next_price')) &
#             (F.col('time_gap') <= 3) &
#             (F.col('next_plen') >= thd_alen_val)
#         ))
    
#     df_case = (df_filtered
#         .select(
#             F.col('jan').alias('jan'),
#             F.col('start').alias('pstart'),
#             F.col('end').alias('pend'),
#             F.col('next_start').alias('astart'),
#             F.col('next_end').alias('aend'),
#             F.col('price').alias('pprice'),
#             F.col('next_price').alias('aprice'),
#             F.col('pos').alias('ppos'),
#             F.col('next_pos').alias('apos'),
#             F.col('plen').alias('pplen'),
#             F.col('next_plen').alias('aplen')
#         ))
    
#     return df_case

# # def _make_case_up(df_pricep):
# #     """
# #     Spark version: generate upward price cases.
# #     """
# #     window_spec = Window.partitionBy('jan').orderBy('start')
    
# #     df_next = (
# #         df_pricep
# #         .withColumn('next_start', F.lead('start').over(window_spec))
# #         .withColumn('next_end', F.lead('end').over(window_spec))
# #         .withColumn('next_price', F.lead('price').over(window_spec))
# #         .withColumn('next_pos', F.lead('pos').over(window_spec))
# #         .withColumn('next_plen', F.lead('plen').over(window_spec))
# #     )
    
# #     df_case = (
# #         df_next
# #         .filter(F.col('next_start').isNotNull())
# #         .filter(
# #             (F.col('price') < F.col('next_price')) &
# #             (F.datediff(F.col('next_start'), F.col('end')) <= thd_gap) &
# #             (F.col('plen') >= thd_plen) &
# #             (F.col('next_plen') >= thd_alen)
# #         )
# #         .select(
# #             'jan',
# #             F.col('start').alias('pstart'),
# #             F.col('end').alias('pend'),
# #             F.col('next_start').alias('astart'),
# #             F.col('next_end').alias('aend'),
# #             F.col('price').alias('pprice'),
# #             F.col('next_price').alias('aprice'),
# #             F.col('pos').alias('ppos'),
# #             F.col('next_pos').alias('apos'),
# #             F.col('plen').alias('pplen'),
# #             F.col('next_plen').alias('aplen')
# #         )
# #     )
# #     return df_case

# def _make_case_zero(df_pricep):
#     """
#     Spark version: generate price-same cases.
#     """
#     df_case = (
#         df_pricep
#         .filter(F.col('plen') >= (thd_plen + thd_alen))
#         .withColumn('type', F.lit('same'))
#         .withColumn('astart', F.date_add(F.col('start'), thd_plen + 7))
#         .withColumn('pprice', F.col('price'))
#         .withColumn('aprice', F.col('price'))
#         .select('jan', 'type', 'astart', 'pprice', 'aprice')
#     )
#     return df_case

# def get_casemaster(case_period, store_cd, case_type):
#     """
#     Fully Spark optimized get_casemaster (same output count as pandas)
#     """
#     spark = SparkSession.getActiveSession()
    
#     period_idpos = (
#         strdoffset(case_period[0], -thd_plen-10),
#         strdoffset(case_period[1], thd_alen+10)
#     )
    
#     df_idpos = _fetch_idpos(period_idpos, store_cd)
#     df_lvmst = df_idpos.select('lv4_nm', 'lv5_nm', 'jan').distinct().cache()
    
#     df_price = _make_day_jan_price_pos(df_idpos)
#     df_pricep = _parse_priceperiod_jan(df_price)
    
#     if case_type == 'up':
#         df_tmp = _make_case_up(df_pricep)
#     elif case_type == 'zero':
#         df_tmp = _make_case_zero(df_pricep)
#     else:
#         raise ValueError(f"Invalid case_type: {case_type}")
    
#     if df_tmp.rdd.isEmpty():
#         return spark.createDataFrame([], df_lvmst.schema)
    
#     df_case = (
#         df_tmp.join(F.broadcast(df_lvmst), on='jan', how='left')
#         .withColumn('store_cd', F.lit(store_cd))
#         .withColumn('astart', F.date_format(F.col('astart'), 'yyyy-MM-dd'))
#         .select('store_cd', 'lv4_nm', 'lv5_nm', 'jan', 'pprice', 'aprice', 'astart')
#     )
#     return df_case

# def make_casemaster(store_cd, jans, upday, dprice):
#     """
#     Fully Spark optimized make_casemaster (same output count as pandas)
#     """
#     spark = SparkSession.getActiveSession()
    
#     period_idpos = (strdoffset(upday, -thd_plen), strdoffset(upday, -1))
#     df_idpos = _fetch_idpos(period_idpos, store_cd)
    
#     df_filtered = df_idpos.filter(F.col('jan').isin(jans))
#     jan_price_counts = df_filtered.groupBy('jan').agg(F.countDistinct('price').alias('price_count'))
#     single_price_jans = jan_price_counts.filter(F.col('price_count')==1).select('jan')
    
#     df_case = (
#         df_filtered.join(F.broadcast(single_price_jans), on='jan', how='inner')
#         .select('lv4_nm', 'lv5_nm', 'jan', 'price')
#         .distinct()
#         .withColumn('pprice', F.col('price'))
#         .withColumn('aprice', F.col('price') + dprice)
#         .withColumn('store_cd', F.lit(store_cd))
#         .withColumn('astart', F.lit(upday))
#         .drop('price')
#     )
#     return df_case
