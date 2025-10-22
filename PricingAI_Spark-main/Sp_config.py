# Databricks notebook source
# -*- coding: utf-8 -*-
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import pandas as pd
import os 

# Sparkセッションの取得
spark = SparkSession.getActiveSession()
if spark is None:
    spark = SparkSession.builder.appName("PriceOptimization").getOrCreate()

# ignore idpos data in these posno.
banpos = []

# dprice range in prediction
dprice_range = [10, 20, 30]

# # jan, det_val.
# kkk_file = '/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/Data_beisia/kkk_master_20250626.csv'

# # jan, series
# series_file = '/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/Data_beisia/series_mst_20250626.csv'

# jan, det_val.
def load_det(kkk_file):
    """CSVをpandas→Sparkに変換してキャッシュ"""
    pdf_det = pd.read_csv(kkk_file)
    df_det = spark.createDataFrame(pdf_det).cache()
    df_det.count()  # キャッシュを実メモリに載せる
    return df_det

kkk_file = './Data_beisia/kkk_master_20250903.csv'
df_det = load_det(kkk_file)

# jan, series
def load_det2(series_file):
    """CSVをpandas→Sparkに変換してキャッシュ"""
    schema = StructType([
    StructField("jan", StringType(), True),
    StructField("series", StringType(), True),
    ])

    if (not os.path.exists(series_file)) or os.path.getsize(series_file) == 0:
            print(f"{series_file} は空です。空のDataFrameを返します。")
            return spark.createDataFrame([], schema)

    pdf_det = pd.read_csv(series_file)
    for col in ["jan", "series"]:
        if col not in pdf_det.columns:
            pdf_det[col] = None
    df_det = spark.createDataFrame(pdf_det, schema=schema).cache()
    df_det.count()  # キャッシュを実メモリに載せる
    return df_det

series_file = './Data_beisia/series_mst_20250626.csv'
df_series = load_det2(series_file)

# single price in {thd_plen} days before upday, thd_plen > max(feature_len, sample_len).
thd_plen = 75
# single price in {thd_alen} days after upday(include), thd_alen > interval_len + label_len.
thd_alen = 45

interval_len = 7
feature_len = 63
sample_len = 28
label_len = 28

# cnt/pos more than {noise_max_cnt} will be clipped. 
noise_max_cnt = 6
# pscore of uid will be modified linearly if n_salesdays is lower than this.
pscore_modify_ndays = 6
# these lv5 will be divided to 2-parts according to det_val, 
# (750, pscore_multipkg_thd): large_pkg, other: small_pkg.
# pscore_mod_lv5 = {
#     '乳飲料': 750,
#     '飲料': 750,
#     'ヨーグルト': 300,
# }
pscore_mod_lv5 = {
    '乳飲料': 750,
    '飲料': 750,
    '果汁飲料': 750,
    '牛乳': 750,
    '豆乳': 750,
    '乳酸菌':510,
    '発酵乳':750,
    'コーヒー・紅茶・茶':750,
    '健康飲料':750,
    '子供飲料':500,
    }
pscore_multipkg_thd = 1200

# pscore of jan in these plv5s will not be calculated.
pscore_ignore_plv5 = []

# fix params
fix_same_dprice   = 0.000
fix_same_type_lv5 = 0.008
fix_same_type_jan = 0.028

# jan with retainr < {simu_thd_retainr} will be ignored.default:-0.5, middle:-0.75, hard:-0.9
simu_thd_retainr = -0.9
# jan with amtchanger < {simu_thd_amtchanger} will be ignored.default:-0.5, middle:-0.75, hard:-0.9
simu_thd_amtchanger = -0.9

# max price cnt in same series in final result
max_price_cnt = 2

# check
if thd_plen <= max(feature_len, sample_len):
    raise ValueError('invalid thd_plen')
if thd_alen <= interval_len + label_len:
    raise ValueError('invalid thd_alen')

# COMMAND ----------

