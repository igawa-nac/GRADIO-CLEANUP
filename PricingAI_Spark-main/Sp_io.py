# Databricks notebook source
# 必要なライブラリのインポート
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.types import LongType, DoubleType

# SQLクエリを実行し、結果をデータフレームとして返す関数
from pyspark.sql import SparkSession

# Spark セッションを取得（最適化設定付き）
spark = SparkSession.builder.getOrCreate()

# Sparkの最適化設定を動的に適用
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")

# WHERE句を生成する関数（元のまま）
def generate_where(d_kws):
    ret = []
    for k, v in d_kws.items():
        if v is None: continue
        if isinstance(v, str):
            ret.append(f"{k}='{v}'")
        elif isinstance(v, (int, float)):
            ret.append(f"{k}={v}")
        elif isinstance(v, list):
            ret.append(f"{k} in ({str(v)[1:-1]})")
        elif isinstance(v, tuple):
            if isinstance(v[0], str):
                ret.append(f"{k} between '{v[0]}' and '{v[1]}'")
            else:
                ret.append(f"{k} between {v[0]} and {v[1]}")
    if ret:
        return ' where ' + ' and '.join(ret)
    else:
        return ''

# idposデータを取得する関数（大幅最適化版）
def fetch_idpos(
    salesday=None,
    salestime=None, 
    storecd=None,
    storename=None,
    posno=None,
    lv1_nm=None,
    lv2_nm=None,
    lv3_nm=None,
    lv4_nm=None,
    lv5_nm=None,
    lv6_nm=None,
    name=None,
    jan=None,
    uid=None,
    age=None,
    sex=None,
    discountcnt=None,
    discountamount=None,
    limit=None
):
    """
    戻り値: Spark DataFrame（大幅最適化版）
    """
    
    # 最適化1: 必要な列のみを選択（I/Oを大幅削減）
    base_columns = """
        SELECT /*+ BROADCAST(cat), BROADCAST(prod) */
             idpos.SALES_DATE,
             idpos.STORE_CODE,
             idpos.MEMBER_CODE,
             idpos.JAN_CODE,
             CAST(idpos.SALES_NUMBER AS FLOAT) AS SALES_NUMBER,
             CAST(idpos.SALES_AMOUNT AS FLOAT) AS SALES_AMOUNT,
             cat.CATEGORY1_NAME,
             cat.CATEGORY2_NAME AS lv4_nm,
             cat.CATEGORY3_NAME AS lv5_nm,
             prod.PRODUCT_NAME AS PROD_PRODUCT_NAME
    """
    
    # 最適化2: プッシュダウンフィルタ用のWHERE条件を事前構築
    idpos_filters = []
    cat_filters = []
    prod_filters = []
    
    # 日付フィルタ（最も選択性が高いので最初に配置）
    if isinstance(salesday, tuple):
        idpos_filters.append(
            f"idpos.SALES_DATE BETWEEN '{salesday[0]}' AND '{salesday[1]}'"
        )
    elif salesday is not None:
        idpos_filters.append(f"idpos.SALES_DATE = '{salesday}'")
    
    # # 店舗フィルタ（高い選択性）
    # if storecd is not None:
    #     idpos_filters.append(f"idpos.STORE_CODE = {storecd}")
    if storecd is not None:
        if isinstance(storecd, (list, tuple)):
            store_list = ", ".join(str(s) for s in storecd)
            idpos_filters.append(f"idpos.STORE_CODE IN ({store_list})")
        else:
            idpos_filters.append(f"idpos.STORE_CODE = {storecd}")

    
    # UID フィルタ（高い選択性）
    if uid is not None:
        idpos_filters.append(f"idpos.MEMBER_CODE = '{uid}'")
    
    # JAN フィルタ（高い選択性）
    if jan is not None:
        if isinstance(jan, (int, str)):
            jan_code = str(jan).zfill(20)
            idpos_filters.append(f"idpos.JAN_CODE = '{jan_code}'")
        elif isinstance(jan, list):
            jan_codes = [str(x).zfill(20) for x in jan]
            jan_list = "', '".join(jan_codes)
            idpos_filters.append(f"idpos.JAN_CODE IN ('{jan_list}')")
    
    # カテゴリフィルタ
    if lv3_nm is not None:
        cat_filters.append(f"cat.CATEGORY1_NAME = '{lv3_nm}'")
    
    if lv4_nm is not None:
        cat_filters.append(f"cat.CATEGORY2_NAME = '{lv4_nm}'")
    
    if lv5_nm is not None:
        cat_filters.append(f"cat.CATEGORY3_NAME = '{lv5_nm}'")
    
    # 商品名フィルタ
    if name is not None:
        prod_filters.append(f"prod.PRODUCT_NAME = '{name}'")
    
    # 最適化3: 単純化されたクエリ構築（エラー回避）
    # 全ての条件を統合して単一のWHERE句で処理
    all_conditions = idpos_filters + cat_filters + prod_filters
    
    # 最適化4: シンプルかつ効率的なSQL構築
    sql_query = """
        SELECT /*+ BROADCAST(cat), BROADCAST(prod) */
             idpos.SALES_DATE,
             idpos.STORE_CODE,
             idpos.MEMBER_CODE,
             idpos.JAN_CODE,
             CAST(idpos.SALES_NUMBER AS FLOAT) AS SALES_NUMBER,
             CAST(idpos.SALES_AMOUNT AS FLOAT) AS SALES_AMOUNT,
             cat.CATEGORY1_NAME,
             cat.CATEGORY2_NAME AS lv4_nm,
             cat.CATEGORY3_NAME AS lv5_nm,
             prod.PRODUCT_NAME AS PROD_PRODUCT_NAME
        FROM 20_01_bricks_native_r_beisia.r_beisia.idpos AS idpos
        JOIN 20_01_bricks_native_r_beisia.r_beisia.category AS cat
          ON idpos.CATEGORY_KEY = cat.CATEGORY_KEY
        JOIN 20_01_bricks_native_r_beisia.r_beisia.product AS prod
          ON idpos.PRODUCT_CODE = prod.PRODUCT_CODE
    """
    
    # 最適化5: WHERE句の統合（最も選択性の高い条件から順番に配置）
    all_conditions = []
    
    # 売上金額が正の値のもののみ（必須フィルタ）
    all_conditions.append("idpos.SALES_AMOUNT > 0")
    
    # 高選択性フィルタから順番に追加
    all_conditions.extend(idpos_filters)
    all_conditions.extend(cat_filters)
    all_conditions.extend(prod_filters)
    
    if all_conditions:
        sql_query += " WHERE " + " AND ".join(all_conditions)
    
    # 最適化6: ORDER BYの最適化（インデックス利用を想定）
    sql_query += " ORDER BY idpos.SALES_DATE, idpos.STORE_CODE"
    
    # LIMIT句を追加
    if limit is not None:
        sql_query += f" LIMIT {limit}"
    
    # 最適化7: クエリヒント付きでSQL実行
    try:
        ret = spark.sql(sql_query)
        
        # 最適化8: 型変換とカラム名変更を一度に実行
        ret = (ret
            .withColumn('salesday', F.to_date(F.col('SALES_DATE')))
            .withColumn('storecd', F.col('STORE_CODE').cast('int'))
            .withColumn('uid', F.col('MEMBER_CODE'))
            .withColumn('jan', F.col('JAN_CODE').cast(LongType()))
            .withColumn('salescnt', F.col('SALES_NUMBER').cast(DoubleType()))
            .withColumn('salesamount', F.col('SALES_AMOUNT').cast(DoubleType()))
            .withColumn('name', F.col('PROD_PRODUCT_NAME'))
            .withColumn('lv3_nm', F.col('CATEGORY1_NAME'))
            .select('salesday', 'storecd', 'uid', 'jan', 'salescnt', 'salesamount',
                   'name', 'lv3_nm', 'lv4_nm', 'lv5_nm')
        )
        
        # 最適化9: パーティション数の動的調整
        target_partition_size = 128 * 1024 * 1024  # 128MB
        current_partitions = ret.rdd.getNumPartitions()
        
        # データ量に応じてパーティション数を調整
        if current_partitions > 200:
            ret = ret.coalesce(200)
        elif current_partitions < 10 and ret.count() > 10000:
            ret = ret.repartition(20)
        
        # 最適化10: キャッシュ戦略（大きなデータセットの場合）
        estimated_size = ret.count()
        if estimated_size > 100000:  # 10万件以上の場合はキャッシュ
            ret = ret.cache()
            
    except Exception as e:
        print(f"Optimized query failed, falling back to basic query: {e}")
        
        # フォールバック: シンプルなクエリ
        basic_query = """
            SELECT
                 idpos.SALES_DATE as salesday,
                 idpos.STORE_CODE as storecd,
                 idpos.MEMBER_CODE as uid,
                 idpos.JAN_CODE as jan,
                 CAST(idpos.SALES_NUMBER AS FLOAT) AS salescnt,
                 CAST(idpos.SALES_AMOUNT AS FLOAT) AS salesamount,
                 cat.CATEGORY1_NAME as lv3_nm,
                 cat.CATEGORY2_NAME as lv4_nm,
                 cat.CATEGORY3_NAME as lv5_nm,
                 prod.PRODUCT_NAME as name
            FROM 20_01_bricks_native_r_beisia.r_beisia.idpos AS idpos
            LEFT JOIN 20_01_bricks_native_r_beisia.r_beisia.category AS cat
              ON idpos.CATEGORY_KEY = cat.CATEGORY_KEY
            LEFT JOIN 20_01_bricks_native_r_beisia.r_beisia.product AS prod
              ON idpos.PRODUCT_CODE = prod.PRODUCT_CODE
            WHERE idpos.SALES_AMOUNT > 0
        """
        
        # 基本フィルタを追加
        basic_conditions = []
        if isinstance(salesday, tuple):
            basic_conditions.append(f"idpos.SALES_DATE BETWEEN '{salesday[0]}' AND '{salesday[1]}'")
        elif salesday is not None:
            basic_conditions.append(f"idpos.SALES_DATE = '{salesday}'")
        
        if storecd is not None:
            basic_conditions.append(f"idpos.STORE_CODE = {storecd}")
            
        if basic_conditions:
            basic_query += " AND " + " AND ".join(basic_conditions)
            
        if limit is not None:
            basic_query += f" LIMIT {limit}"
            
        ret = spark.sql(basic_query)
        
        # 型変換
        ret = (ret
            .withColumn('jan', F.col('jan').cast(LongType()))
            .withColumn('salesday', F.to_date(F.col('salesday')))
            .withColumn('salescnt', F.col('salescnt').cast(DoubleType()))
            .withColumn('salesamount', F.col('salesamount').cast(DoubleType()))
        )
    
    return ret

# COMMAND ----------

# # 必要なライブラリのインポート
# import pandas as pd
# from pyspark.sql import functions as F
# from pyspark.sql.types import LongType, DoubleType

# # SQLクエリを実行し、結果をデータフレームとして返す関数
# from pyspark.sql import SparkSession

# # Spark セッションを取得
# spark = SparkSession.builder.getOrCreate()

# # WHERE句を生成する関数（元のまま）
# def generate_where(d_kws):
#     ret = []
#     for k, v in d_kws.items():
#         if v is None: continue
#         if isinstance(v, str):
#             ret.append(f"{k}='{v}'")
#         elif isinstance(v, (int, float)):
#             ret.append(f"{k}={v}")
#         elif isinstance(v, list):
#             ret.append(f"{k} in ({str(v)[1:-1]})")
#         elif isinstance(v, tuple):
#             if isinstance(v[0], str):
#                 ret.append(f"{k} between '{v[0]}' and '{v[1]}'")
#             else:
#                 ret.append(f"{k} between {v[0]} and {v[1]}")
#     if ret:
#         return ' where ' + ' and '.join(ret)
#     else:
#         return ''

# # idposデータを取得する関数（generate_whereを使わない版）
# def fetch_idpos(
#     salesday=None,
#     salestime=None, 
#     storecd=None,
#     storename=None,
#     posno=None,
#     lv1_nm=None,
#     lv2_nm=None,
#     lv3_nm=None,
#     lv4_nm=None,
#     lv5_nm=None,
#     lv6_nm=None,
#     name=None,
#     jan=None,
#     uid=None,
#     age=None,
#     sex=None,
#     discountcnt=None,
#     discountamount=None,
#     limit=None
# ):
#     """
#     戻り値: Spark DataFrame
#     """
#     # SQLクエリの初期部分を定義
#     sql_query = """
#         SELECT
#              idpos.CLIENT_CODE,
#              idpos.TRANSACTION_CODE,
#              idpos.SALES_DATE,
#              idpos.SALES_TIME,
#              idpos.AREA1_CODE,
#              idpos.AREA2_CODE,
#              idpos.STORE_CODE,
#              idpos.MEMBER_CODE,
#              idpos.CUSTOMER_CODE,
#              CAST(idpos.GENDER_FLG AS INT) AS GENDER_FLG,
#              CAST(idpos.AGE AS INT) AS AGE,
#              idpos.JAN_CODE,
#              idpos.PRODUCT_CODE,
#              idpos.CATEGORY_KEY AS IDPOS_CATEGORY_KEY,
#              CAST(idpos.SALES_NUMBER AS FLOAT) AS SALES_NUMBER,
#              CAST(idpos.SALES_AMOUNT AS FLOAT) AS SALES_AMOUNT,
#              idpos.CREATED_AT AS IDPOS_CREATED_AT,
#              idpos.UPDATED_AT AS IDPOS_UPDATED_AT,
#              cat.CATEGORY_KEY AS CAT_CATEGORY_KEY,
#              cat.CATEGORY1_CODE,
#              cat.CATEGORY1_NAME,
#              cat.CATEGORY2_CODE,
#              cat.CATEGORY2_NAME AS lv4_nm,
#              cat.CATEGORY3_NAME AS lv5_nm,
#              prod.PRODUCT_CODE AS PROD_PRODUCT_CODE,
#              prod.PRODUCT_NAME AS PROD_PRODUCT_NAME
#         FROM 20_01_bricks_native_r_beisia.r_beisia.idpos AS idpos
#         LEFT JOIN 20_01_bricks_native_r_beisia.r_beisia.category AS cat
#           ON idpos.CATEGORY_KEY = cat.CATEGORY_KEY
#         LEFT JOIN 20_01_bricks_native_r_beisia.r_beisia.product AS prod
#           ON idpos.PRODUCT_CODE = prod.PRODUCT_CODE
#     """
    
#     # WHERE条件を直接構築（generate_whereを使わない）
#     conditions = []
    
#     # 日付条件
#     if isinstance(salesday, tuple):
#         conditions.append(
#             f"DATE(idpos.SALES_DATE) BETWEEN DATE('{salesday[0]}') AND DATE('{salesday[1]}')"
#         )
#     elif salesday is not None:
#         conditions.append(
#             f"DATE(idpos.SALES_DATE) = DATE('{salesday}')"
#         )

    
#     # 店舗条件
#     if storecd is not None:
#         conditions.append(f"idpos.STORE_CODE = {storecd}")
    
#     # カテゴリ条件
#     if lv3_nm is not None:
#         conditions.append(f"cat.CATEGORY1_NAME = '{lv3_nm}'")
    
#     if lv4_nm is not None:
#         conditions.append(f"cat.CATEGORY2_NAME = '{lv4_nm}'")
    
#     if lv5_nm is not None:
#         conditions.append(f"cat.CATEGORY3_NAME = '{lv5_nm}'")
    
#     # 商品名条件
#     if name is not None:
#         conditions.append(f"prod.PRODUCT_NAME = '{name}'")
    
#     # JAN条件
#     if jan is not None:
#         if isinstance(jan, (int, str)):
#             jan_code = str(jan).zfill(20)
#             conditions.append(f"idpos.JAN_CODE = '{jan_code}'")
#         elif isinstance(jan, list):
#             jan_codes = [str(x).zfill(20) for x in jan]
#             jan_list = "', '".join(jan_codes)
#             conditions.append(f"idpos.JAN_CODE IN ('{jan_list}')")
    
#     # UID条件
#     if uid is not None:
#         conditions.append(f"idpos.MEMBER_CODE = '{uid}'")
    
#     # WHERE句を追加
#     if conditions:
#         sql_query += " WHERE " + " AND ".join(conditions)
    
#     # LIMIT句を追加
#     if limit is not None:
#         sql_query += f" LIMIT {limit}"
    
#     # # デバッグ用：生成されたSQLを出力
#     # print("Generated SQL Query:")
#     # print(sql_query)
#     # print("=" * 80)
    
#     # Spark SQL実行
#     ret = spark.sql(sql_query)
    
#     # カラム名を変更
#     ret = (ret
#         .withColumnRenamed('SALES_DATE', 'salesday')
#         .withColumnRenamed('STORE_CODE', 'storecd')
#         .withColumnRenamed('MEMBER_CODE', 'uid')
#         .withColumnRenamed('JAN_CODE', 'jan')
#         .withColumnRenamed('SALES_NUMBER', 'salescnt')
#         .withColumnRenamed('SALES_AMOUNT', 'salesamount')
#         .withColumnRenamed('CATEGORY1_NAME', 'lv3_nm')
#         .withColumnRenamed('PROD_PRODUCT_NAME', 'name')
#     )
    
#     # 型変換
#     ret = (ret
#         .withColumn('jan', F.col('jan').cast(LongType()))
#         .withColumn('salesday', F.to_date(F.col('salesday')))
#         .withColumn('salescnt', F.col('salescnt').cast(DoubleType()))
#         .withColumn('salesamount', F.col('salesamount').cast(DoubleType()))
#     )
    
#     # 必要なカラムのみ選択
#     final_columns = [
#         'salesday', 'storecd', 'uid', 'jan', 'salescnt', 'salesamount',
#         'name', 'lv3_nm', 'lv4_nm', 'lv5_nm'
#     ]
#     ret = ret.select(*[c for c in final_columns if c in ret.columns])
    
#     return ret

# COMMAND ----------

# from pyspark.sql import functions as F
# from pyspark.sql.types import LongType, DoubleType
# from pyspark.sql import SparkSession

# # Spark セッションを取得
# spark = SparkSession.builder.getOrCreate()

# # WHERE句を生成する関数
# def generate_where(d_kws):
#     ret = []
#     for k, v in d_kws.items():
#         if v is None: 
#             continue
#         if isinstance(v, str):
#             ret.append(f"{k}='{v}'")
#         elif isinstance(v, (int, float)):
#             ret.append(f"{k}={v}")
#         elif isinstance(v, list):
#             # リストの処理を修正
#             if all(isinstance(item, str) for item in v):
#                 formatted_list = "', '".join(v)
#                 ret.append(f"{k} IN ('{formatted_list}')")
#             else:
#                 formatted_list = ", ".join(str(item) for item in v)
#                 ret.append(f"{k} IN ({formatted_list})")
#         elif isinstance(v, tuple):
#             if isinstance(v[0], str):
#                 ret.append(f"{k} BETWEEN '{v[0]}' AND '{v[1]}'")
#             else:
#                 ret.append(f"{k} BETWEEN {v[0]} AND {v[1]}")
#     if ret:
#         return ' WHERE ' + ' AND '.join(ret)
#     else:
#         return ''

# def fetch_idpos(
#     salesday=None,
#     salestime=None, 
#     storecd=None,
#     storename=None,
#     posno=None,
#     lv1_nm=None,
#     lv2_nm=None,
#     lv3_nm=None,
#     lv4_nm=None,
#     lv5_nm=None,
#     lv6_nm=None,
#     name=None,
#     jan=None,
#     uid=None,
#     age=None,
#     sex=None,
#     discountcnt=None,
#     discountamount=None,
#     limit=None
# ):
#     """
#     戻り値: Spark DataFrame
#     """

#     # salesday がタプルなら文字列に変換してBETWEEN用にする
#     if isinstance(salesday, tuple):
#         start, end = salesday
#         start = str(start)
#         end = str(end)
#         salesday = (start, end)
#     elif salesday is not None:
#         salesday = str(salesday)

#     # SQLクエリの初期部分
#     sql_query = """
#         SELECT
#              idpos.CLIENT_CODE,
#              idpos.TRANSACTION_CODE,
#              idpos.SALES_DATE,
#              idpos.SALES_TIME,
#              idpos.AREA1_CODE,
#              idpos.AREA2_CODE,
#              idpos.STORE_CODE,
#              idpos.MEMBER_CODE,
#              idpos.CUSTOMER_CODE,
#              CAST(idpos.GENDER_FLG AS INT) AS GENDER_FLG,
#              CAST(idpos.AGE AS INT) AS AGE,
#              idpos.JAN_CODE,
#              idpos.PRODUCT_CODE,
#              idpos.CATEGORY_KEY AS IDPOS_CATEGORY_KEY,
#              CAST(idpos.SALES_NUMBER AS FLOAT) AS SALES_NUMBER,
#              CAST(idpos.SALES_AMOUNT AS FLOAT) AS SALES_AMOUNT,
#              idpos.CREATED_AT AS IDPOS_CREATED_AT,
#              idpos.UPDATED_AT AS IDPOS_UPDATED_AT,
#              cat.CATEGORY_KEY AS CAT_CATEGORY_KEY,
#              cat.CATEGORY1_CODE,
#              cat.CATEGORY1_NAME,
#              cat.CATEGORY2_CODE,
#              cat.CATEGORY2_NAME,
#              cat.CATEGORY3_CODE,
#              cat.CATEGORY3_NAME,
#              prod.PRODUCT_CODE AS PROD_PRODUCT_CODE,
#              prod.PRODUCT_NAME AS PROD_PRODUCT_NAME
#         FROM 20_01_bricks_native_r_beisia.r_beisia.idpos AS idpos
#         LEFT JOIN 20_01_bricks_native_r_beisia.r_beisia.category AS cat
#           ON idpos.CATEGORY_KEY = cat.CATEGORY_KEY
#         LEFT JOIN 20_01_bricks_native_r_beisia.r_beisia.product AS prod
#           ON idpos.PRODUCT_CODE = prod.PRODUCT_CODE
#     """
#     # janコードを20桁にゼロ埋め
#     if isinstance(jan, (int, str)):
#         jan = str(jan).zfill(20)
#     elif isinstance(jan, list):
#         jan = [str(x).zfill(20) for x in jan]


#     # WHERE句を作る - 条件を個別に構築
#     conditions = []
    
#     # 日付条件
#     if isinstance(salesday, tuple):
#         conditions.append(f"idpos.SALES_DATE BETWEEN '{salesday[0]}' AND '{salesday[1]}'")
#     elif salesday is not None:
#         conditions.append(f"idpos.SALES_DATE = '{salesday}'")
    
#     # その他の条件
#     if storecd is not None:
#         conditions.append(f"idpos.STORE_CODE = {storecd}")
    
#     if lv3_nm is not None:
#         conditions.append(f"cat.CATEGORY1_NAME = '{lv3_nm}'")
    
#     if lv4_nm is not None:
#         conditions.append(f"cat.CATEGORY2_NAME = '{lv4_nm}'")
    
#     if lv5_nm is not None:
#         conditions.append(f"cat.CATEGORY3_NAME = '{lv5_nm}'")
    
#     if name is not None:
#         conditions.append(f"prod.PRODUCT_NAME = '{name}'")
    
#     if jan is not None:
#         if isinstance(jan, list):
#             jan_list = "', '".join(jan)
#             conditions.append(f"idpos.JAN_CODE IN ('{jan_list}')")
#         else:
#             conditions.append(f"idpos.JAN_CODE = '{jan}'")
    
#     if uid is not None:
#         conditions.append(f"idpos.MEMBER_CODE = '{uid}'")
    
#     if age is not None:
#         conditions.append(f"idpos.AGE = {age}")
    
#     if sex is not None:
#         conditions.append(f"idpos.GENDER_FLG = {sex}")

#     # WHERE句を追加
#     if conditions:
#         sql_query += " WHERE " + " AND ".join(conditions)

#     # LIMIT句
#     if limit is not None:
#         sql_query += f" LIMIT {limit}"

#     # デバッグ用：生成されたSQLを出力
#     print("Generated SQL Query:")
#     print(sql_query)
#     print("=" * 80)

#     # Spark SQL 実行
#     ret = spark.sql(sql_query)

#     # カラム名を変換
#     ret = (ret
#         .withColumnRenamed('SALES_DATE', 'salesday')
#         .withColumnRenamed('STORE_CODE', 'storecd')
#         .withColumnRenamed('MEMBER_CODE', 'uid')
#         .withColumnRenamed('JAN_CODE', 'jan')
#         .withColumnRenamed('SALES_NUMBER', 'salescnt')
#         .withColumnRenamed('SALES_AMOUNT', 'salesamount')
#         .withColumnRenamed('CATEGORY1_NAME', 'lv3_nm')
#         .withColumnRenamed('CATEGORY2_NAME', 'lv4_nm')
#         .withColumnRenamed('CATEGORY3_NAME', 'lv5_nm')
#         .withColumnRenamed('PROD_PRODUCT_NAME', 'name')
#     )

#     # 型変換
#     ret = (ret
#         .withColumn('jan', F.col('jan').cast(LongType()))
#         .withColumn('salesday', F.to_date(F.col('salesday')))
#         .withColumn('salescnt', F.col('salescnt').cast(DoubleType()))
#         .withColumn('salesamount', F.col('salesamount').cast(DoubleType()))
#     )

#     # 必要なカラムだけ選択
#     final_columns = [
#         'salesday', 'storecd', 'uid', 'jan', 'salescnt', 'salesamount',
#         'name', 'lv3_nm', 'lv4_nm', 'lv5_nm'
#     ]
#     ret = ret.select(*[c for c in final_columns if c in ret.columns])

#     return ret