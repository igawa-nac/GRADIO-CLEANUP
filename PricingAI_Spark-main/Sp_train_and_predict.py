# Databricks notebook source
# MAGIC %run ./Sp_interface.py

# COMMAND ----------

# MAGIC %md
# MAGIC # 学習

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT DISTINCT STORE_NAME, STORE_CODE
# MAGIC FROM 20_01_bricks_native_r_beisia.r_beisia.store
# MAGIC

# COMMAND ----------

# train
train_model(
    case_period=('2023-08-02', '2025-08-01'), 
    stores=[393, 366, 342, 379, 300,301, 303, 304,306, 307, 309, 310, 311, 312, 313, 318, 336, 337, 339, 502, 503, 515, 600, 601, 602, 603, 604, 605, 606, 607],
    #stores=[326,349,527],
    #stores=[349],
    output_zero='/Volumes/20_01_bricks_native_r_beisia/models/model_path/model2_go_2y_zero_20251002',
    output_up='/Volumes/20_01_bricks_native_r_beisia/models/model_path/model2_go_2y_up_20251002',
    verbose=True
)



# COMMAND ----------

# MAGIC %md
# MAGIC # 予測

# COMMAND ----------

# predict
for store_cd in [326]:
    df_item, df_uid = predict_result(
        store_cd=store_cd, 
        upday='2025-09-15',
        model_zero='/Volumes/20_01_bricks_native_r_beisia/models/model_path/model2_go_2y_zero_20251002',
        model_up='/Volumes/20_01_bricks_native_r_beisia/models/model_path/model2_go_2y_zero_20251002',
        item_file='/Volumes/20_01_bricks_native_r_beisia/csv/csv_path/item_beisia_utf8_20250903.csv', 
        drop_file='/Volumes/20_01_bricks_native_r_beisia/csv/csv_path/droplist_blk_beisia_20250806.csv',
        verbose=True
    )

    df_item.write.format('csv').mode('overwrite').option('header', True).option('encoding', 'UTF-8').save(f'/Volumes/20_01_bricks_native_r_beisia/output/output_path/{store_cd:04d}_item_res_beisia_20251003')

    df_uid.write.format('csv').mode('overwrite').option('header', True).option('encoding', 'UTF-8').save(f'/Volumes/20_01_bricks_native_r_beisia/output/output_path/{store_cd:04d}_uid_res_beisia_20251003')

    # df_item[0].write.mode("overwrite").option("header", True).csv(output_dir_item)
    # df_uid.write.mode("overwrite").option("header", True).csv(output_dir_uid)

# COMMAND ----------

# MAGIC %md
# MAGIC

# COMMAND ----------

# # df_item_path = "/Volumes/20_01_bricks_native_r_beisia/output/output_path/{store_cd:04d}_item_res_beisia_20251003"
# # df_uid_path = "/Volumes/20_01_bricks_native_r_beisia/output/output_path/{store_cd:04d}_uid_res_beisia_20251003"


df_item.write.format('csv').mode('overwrite').option('header', True).option('encoding', 'UTF-8').save(f'/Volumes/20_01_bricks_native_r_beisia/output/output_path/{store_cd:04d}_item_res_beisia_20251003')

df_uid.write.format('csv').mode('overwrite').option('header', True).option('encoding', 'UTF-8').save(f'/Volumes/20_01_bricks_native_r_beisia/output/output_path/{store_cd:04d}_uid_res_beisia_20251003')

# # df_item[0].write.format("csv").mode("overwrite").option("header", True).save(df_item_path)
# # df_uid.write.format("csv").mode("overwrite").option("header", True).save(df_uid_path)

# COMMAND ----------

# # predict
# import pandas as pd

# for store_cd in [326]:
#     pd_df1 = pd.read_csv("/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/Data_beisia/item_beisia_utf8_20250903.csv")
#     # ローカルのCSVを pandas で読み込む
#     pd_df2 = pd.read_csv("/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/Data_beisia/droplist_blk_beisia_20250806.csv")

#     df_item, df_uid = predict_result(
#         store_cd=store_cd, 
#         upday='2025-09-01',
#         model_zero='/Volumes/20_01_bricks_native_r_beisia/models/model_path/model2_go_2y_zero_20251002',
#         model_up='/Volumes/20_01_bricks_native_r_beisia/models/model_path/model2_go_2y_zero_20251002',
#         item_file = spark.createDataFrame(pd_df1),
#         drop_file = spark.createDataFrame(pd_df2),

#         verbose=True
#     )
#     print(type(df_item), type(df_uid))
#     df_item[0].to_csv(f'/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/{"%04d"%store_cd}_item_res_beisia_20250916.csv', index=False, encoding="utf-8-sig")
#     df_uid.to_csv(f'/Workspace/Users/okazaki_keiya2@nippon-access.co.jp/PricingAI_spark/{"%04d"%store_cd}_uid_res_beisia_20250916.csv', index=False, encoding="utf-8-sig")