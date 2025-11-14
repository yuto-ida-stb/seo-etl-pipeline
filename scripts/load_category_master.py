#!/usr/bin/env python3
"""
BigQueryからカテゴリマスタを取得してCSVに保存するスクリプト
"""
from google.cloud import bigquery
import pandas as pd
import os

# BigQuery設定
PROJECT_ID = 'stanby-prod'

def load_category_master():
    """カテゴリマスタをBigQueryから取得"""
    client = bigquery.Client(project=PROJECT_ID)

    print("カテゴリマスタをBigQueryから取得中...")

    query = """
    SELECT
        query_hash,
        query_keyword,
        query_location,
        cate as category
    FROM `stanby-prod.temp_adhoc.query_category`
    """

    df = client.query(query).to_dataframe()

    print(f"✓ カテゴリマスタ取得完了: {len(df):,}件")

    # 保存
    output_file = './data/query_category_master.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✓ 保存完了: {output_file}")

    return df

if __name__ == "__main__":
    load_category_master()
