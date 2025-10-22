# Databricks notebook source
from datetime import datetime, timedelta
from pyspark.sql import functions as F

def strdoffset(date_str: str, offset: int) -> str:
    """
    Python文字列用: YYYY-MM-DD の文字列を受け取り、offset日だけずらした文字列を返す
    """
    if not isinstance(date_str, str):
        raise TypeError(f"strdoffset_str expects str, got {type(date_str)}")
    
    base = datetime.strptime(date_str, "%Y-%m-%d")
    shifted = base + timedelta(days=offset)
    return shifted.strftime("%Y-%m-%d")


def strdoffset_col(date_col, offset: int):
    """
    Spark Column用: YYYY-MM-DD の文字列カラムを受け取り、offset日だけずらしたカラムを返す
    """
    return F.date_format(
        F.date_add(F.to_date(date_col, "yyyy-MM-dd"), offset),
        "yyyy-MM-dd"
    )
