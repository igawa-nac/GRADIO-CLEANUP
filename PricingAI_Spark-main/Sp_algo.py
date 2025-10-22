# Databricks notebook source
# MAGIC %run ./Sp_config.py

# COMMAND ----------

# MAGIC %md
# MAGIC #9/29実行中コード

# COMMAND ----------

"""
algorithm used in prediction.
"""

from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np

class RandomForestClassifierPrice:
    
    def __init__(self, param_jan=None, param_lv5=None):
        """
        Parameters
        ----------
        param_jan, param_lv5: dict / None.
            parameters passed to RandomForestClassifier.
        """
        if not param_jan:
            param_jan = {
                'n_estimators': 80,
                'random_state': 100,
                'n_jobs': 4,
                'min_samples_split': 90,
                'min_samples_leaf': 40
            }
        if not param_lv5:
            param_lv5 = {
                'n_estimators': 80,
                'random_state': 100,
                'n_jobs': 4,
                'min_samples_split': 160,
                'min_samples_leaf': 70
            }
        
        self.mdl_jan = RandomForestClassifier(**param_jan)
        self.mdl_lv5 = RandomForestClassifier(**param_lv5)
        
    def _create_fillv(self, X):
        """
        Spark DataFrame または pandas DataFrame から中央値辞書を作成
        """
        if hasattr(X, 'toPandas'):  # Spark DataFrame
            # 数値列のみを取得して中央値を計算
            from pyspark.sql import functions as F
            from pyspark.sql.types import NumericType
            
            numeric_cols = [field.name for field in X.schema.fields 
                           if isinstance(field.dataType, NumericType)]
            
            fillv_dict = {}
            for col in numeric_cols:
                try:
                    median_val = X.approxQuantile(col, [0.5], 0.01)[0]
                    fillv_dict[col] = median_val
                except:
                    fillv_dict[col] = 0.0
            return fillv_dict
        else:  # pandas DataFrame
            return X.median().to_dict()

    def _fillv(self, X, d_fillv):
        """
        欠損値を埋める
        """
        if hasattr(X, 'toPandas'):  # Spark DataFrame
            from pyspark.sql import functions as F
            result = X
            for col, fill_val in d_fillv.items():
                if col in X.columns:
                    result = result.fillna(fill_val, subset=[col])
            return result
        else:  # pandas DataFrame
            return X.fillna(d_fillv)

    def _resample(self, df, mr, mx):
        """
        リサンプリング処理（pandas DataFrameで実行）
        """
        # Spark DataFrameの場合はpandasに変換
        if hasattr(df, 'toPandas'):
            df = df.toPandas()
            
        ldf = [df.loc[df['dprice']==i] for i in mr]
        for i in range(len(mr)):
            if ldf[i].empty: 
                raise ValueError(f'invalid dprice {mr[i]} in mprice_range.')
        
        maxv = max(x.shape[0] for x in ldf)
        ret = [df]
        for idf in ldf:
            time = min(maxv / idf.shape[0], mx) - 1
            vint = int(time)
            ret.extend([idf for _ in range(vint)])
            vhd = int((time - vint) * idf.shape[0])
            ret.append(idf.head(vhd))
            
        return pd.concat(ret)
    
    def fit_jan(
        self, 
        X, 
        y, 
        mdprice_range=None, 
        max_times=None
    ):
        """
        Parameters
        ----------
        X: pd.DataFrame or Spark DataFrame.
        y: pd.Series or Spark DataFrame.
        mdprice_range: list[int].
            duplicate samples to same scale in these dprice range.
        max_times: int.
            max times in scale process.
        """
        # Spark DataFrameの場合はpandasに変換
        if hasattr(X, 'toPandas'):
            X_pd = X.toPandas()
        else:
            X_pd = X.copy() if hasattr(X, 'copy') else X

        if hasattr(y, 'toPandas'):
            y_pd = y.toPandas()
        elif hasattr(y, 'copy'):
            y_pd = y.copy()
        else:
            y_pd = y

        # 中央値辞書を作成（元のXから）
        self.d_fillv_jan = self._create_fillv(X)
        
        # 欠損値を埋める
        X_filled = self._fillv(X_pd if isinstance(X_pd, pd.DataFrame) else X, self.d_fillv_jan)
        if hasattr(X_filled, 'toPandas'):
            X_filled = X_filled.toPandas()

        if mdprice_range is not None:
            # yをSeriesに変換
            if isinstance(y_pd, pd.DataFrame):
                if y_pd.shape[1] == 1:
                    y_series = y_pd.iloc[:, 0]
                else:
                    y_series = y_pd
            else:
                y_series = y_pd
                
            df = pd.concat([X_filled, y_series.rename('_fit_label')], axis=1)
            df = self._resample(df, mdprice_range, max_times)
            X_final = df.drop('_fit_label', axis=1)
            y_final = df['_fit_label']
        else:
            X_final = X_filled
            y_final = y_pd
        
        self.mdl_jan.fit(X_final, y_final)
        return
    
    def fit_lv5(
        self, 
        X, 
        y, 
        mdprice_range=None, 
        max_times=None
    ):
        """
        Parameters
        ----------
        X: pd.DataFrame or Spark DataFrame.
        y: pd.Series or Spark DataFrame.
        mdprice_range: list[int].
            duplicate samples to same scale in these dprice range.
        max_times: int.
            max times in scale process.
        """
        # Spark DataFrameの場合はpandasに変換
        if hasattr(X, 'toPandas'):
            X_pd = X.toPandas()
        else:
            X_pd = X.copy() if hasattr(X, 'copy') else X

        if hasattr(y, 'toPandas'):
            y_pd = y.toPandas()
        elif hasattr(y, 'copy'):
            y_pd = y.copy()
        else:
            y_pd = y

        # 中央値辞書を作成（元のXから）
        self.d_fillv_lv5 = self._create_fillv(X)
        
        # 欠損値を埋める
        X_filled = self._fillv(X_pd if isinstance(X_pd, pd.DataFrame) else X, self.d_fillv_lv5)
        if hasattr(X_filled, 'toPandas'):
            X_filled = X_filled.toPandas()

        if mdprice_range is not None:
            # yをSeriesに変換
            if isinstance(y_pd, pd.DataFrame):
                if y_pd.shape[1] == 1:
                    y_series = y_pd.iloc[:, 0]
                else:
                    y_series = y_pd
            else:
                y_series = y_pd
                
            df = pd.concat([X_filled, y_series.rename('_fit_label')], axis=1)
            df = self._resample(df, mdprice_range, max_times)
            X_final = df.drop('_fit_label', axis=1)
            y_final = df['_fit_label']
        else:
            X_final = X_filled
            y_final = y_pd
            
        self.mdl_lv5.fit(X_final, y_final)
        return
    
    def predict_jan(self, X):
        """
        Parameters
        ----------
        X: pd.DataFrame or Spark DataFrame.
        
        Returns
        -------
        np.1darray.
        """
        # Spark DataFrameの場合はpandasに変換
        if hasattr(X, 'toPandas'):
            X_pd = X.toPandas()
        else:
            X_pd = X
            
        X_filled = X_pd.fillna(self.d_fillv_jan)
        idx = self.mdl_jan.classes_.tolist().index(True)
        return self.mdl_jan.predict_proba(X_filled)[:, idx]
    
    def predict_lv5(self, X):
        """
        Parameters
        ----------
        X: pd.DataFrame or Spark DataFrame.
        
        Returns
        -------
        np.1darray.
        """
        # Spark DataFrameの場合はpandasに変換
        if hasattr(X, 'toPandas'):
            X_pd = X.toPandas()
        else:
            X_pd = X
            
        X_filled = X_pd.fillna(self.d_fillv_lv5)
        idx = self.mdl_lv5.classes_.tolist().index(True)
        return self.mdl_lv5.predict_proba(X_filled)[:, idx]


def fix_prob(df_pred):
    """
    use high acc prob to fix low acc prob.
    
    Parameters
    ----------
    df_pred: pd.DataFrame or Spark DataFrame.
        columns=key_cols+['prob_jan_x', 'prob_lv5_x', ...].
    
    Returns
    -------
    same type as input (pd.DataFrame or Spark DataFrame).
    """
    # Spark DataFrame の場合は pandas に変換
    is_spark = False
    if hasattr(df_pred, 'toPandas'):
        df_pred_pd = df_pred.toPandas()
        is_spark = True
    else:
        df_pred_pd = df_pred.copy()

    df_ret = df_pred_pd.copy()
    
    # dprice_rangeが定義されていない場合のフォールバック
    try:
        l_dprice = [0] + sorted(dprice_range)
    except NameError:
        # dprice_rangeが定義されていない場合は、カラム名から推定
        prob_cols = [col for col in df_ret.columns if col.startswith('prob_')]
        dprice_values = []
        for col in prob_cols:
            try:
                dp = int(col.split('_')[-1])
                dprice_values.append(dp)
            except ValueError:
                continue
        l_dprice = [0] + sorted(list(set(dprice_values)))

    # fix_パラメータが定義されていない場合のデフォルト値
    try:
        fix_same_dprice_val = fix_same_dprice
    except NameError:
        fix_same_dprice_val = 0.000
        
    try:
        fix_same_type_lv5_val = fix_same_type_lv5
    except NameError:
        fix_same_type_lv5_val = 0.008
        
    try:
        fix_same_type_jan_val = fix_same_type_jan
    except NameError:
        fix_same_type_jan_val = 0.028

    for it in ['lv5', 'jan']:
        for iip, ip in enumerate(l_dprice):
            iname = f'prob_{it}_{ip}'
            
            # カラムが存在しない場合はスキップ
            if iname not in df_ret.columns:
                continue
                
            if it == 'jan':
                jname = f'prob_lv5_{ip}'
                if jname in df_ret.columns:
                    df_ret[iname] = pd.concat(
                        [df_ret[iname], df_ret[jname] - fix_same_dprice_val],
                        axis=1
                    ).min(axis=1)
            if iip:
                jname = f'prob_{it}_{l_dprice[iip-1]}'
                if jname in df_ret.columns:
                    thd = fix_same_type_lv5_val if it == 'lv5' else fix_same_type_jan_val
                    df_ret[iname] = pd.concat(
                        [df_ret[iname], df_ret[jname] - thd],
                        axis=1
                    ).min(axis=1)
            df_ret[iname] = df_ret[iname].clip(lower=0.00)

    # 元がSpark DataFrameの場合は戻す
    if is_spark:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        return spark.createDataFrame(df_ret)
    
    return df_ret

# COMMAND ----------

# MAGIC %md
# MAGIC 改良版

# COMMAND ----------

# from pyspark.ml.classification import RandomForestClassifier
# from pyspark.ml.feature import VectorAssembler
# from pyspark.sql import functions as F

# class RandomForestClassifierPriceSpark:
#     def __init__(self, param_jan=None, param_lv5=None):
#         if not param_jan:
#             param_jan = {
#                 'numTrees': 80,
#                 'seed': 100,
#                 'minInstancesPerNode': 40,
#                 'minInfoGain': 0.0,
#                 'maxDepth': 10
#             }
#         if not param_lv5:
#             param_lv5 = {
#                 'numTrees': 80,
#                 'seed': 100,
#                 'minInstancesPerNode': 70,
#                 'minInfoGain': 0.0,
#                 'maxDepth': 10
#             }

#         self.param_jan = param_jan
#         self.param_lv5 = param_lv5
#         self.mdl_jan = None
#         self.mdl_lv5 = None

#     def _prepare_features(self, df, feature_cols):
#         assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
#         return assembler.transform(df).select("features", "label")

#     def fit_jan(self, df, feature_cols, label_col="label"):
#         df = df.fillna({c: df.approxQuantile(c, [0.5], 0.01)[0] for c in feature_cols})
#         df = df.withColumnRenamed(label_col, "label")
#         train_df = self._prepare_features(df, feature_cols)
#         rf = RandomForestClassifier(featuresCol="features", labelCol="label", probabilityCol="probability", **self.param_jan)
#         self.mdl_jan = rf.fit(train_df)

#     def fit_lv5(self, df, feature_cols, label_col="label"):
#         df = df.fillna({c: df.approxQuantile(c, [0.5], 0.01)[0] for c in feature_cols})
#         df = df.withColumnRenamed(label_col, "label")
#         train_df = self._prepare_features(df, feature_cols)
#         rf = RandomForestClassifier(featuresCol="features", labelCol="label", probabilityCol="probability", **self.param_lv5)
#         self.mdl_lv5 = rf.fit(train_df)

#     def predict_jan(self, df, feature_cols):
#         test_df = self._prepare_features(df, feature_cols)
#         preds = self.mdl_jan.transform(test_df)
#         return preds.withColumn("prob_jan_pred", preds["probability"].getItem(1)).select("prob_jan_pred")

#     def predict_lv5(self, df, feature_cols):
#         test_df = self._prepare_features(df, feature_cols)
#         preds = self.mdl_lv5.transform(test_df)
#         return preds.withColumn("prob_lv5_pred", preds["probability"].getItem(1)).select("prob_lv5_pred")


# COMMAND ----------

