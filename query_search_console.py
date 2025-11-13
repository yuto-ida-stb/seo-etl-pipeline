from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import os

# BigQuery設定
PROJECT_ID = 'stanby-prod'
DATASET_ID = 'searchconsole'
TABLE_ID = 'searchdata_url_impression'

def get_bigquery_client():
    """BigQueryクライアントを取得"""
    # gcloud auth application-default loginで設定した認証を使用
    client = bigquery.Client(project=PROJECT_ID)
    return client

def check_table_schema():
    """テーブルのスキーマを確認"""
    client = get_bigquery_client()

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    table = client.get_table(table_ref)

    print(f"テーブル: {table_ref}")
    print(f"行数: {table.num_rows:,}")
    print(f"\nスキーマ:")
    for field in table.schema:
        print(f"  - {field.name}: {field.field_type}")

    # サンプルデータを取得
    query = f"""
    SELECT *
    FROM `{table_ref}`
    LIMIT 5
    """

    df = client.query(query).to_dataframe()
    print(f"\nサンプルデータ:")
    print(df)

    return table.schema

def get_weekly_search_console_data(weeks: int = 12):
    """
    週次のSearch Consoleデータを取得し、前週比を計算

    r_hash別（SEO向け求人一覧ページ）の週次集計を行います。

    Args:
        weeks: 取得する週数（デフォルト12週=3ヶ月）

    Returns:
        週次データと前週比を含むDataFrame
    """
    client = get_bigquery_client()

    # 過去N週間のデータを週次集計
    query = f"""
    WITH r_hash_data AS (
      -- URLからr_hashを抽出（/r_で始まるURL）
      SELECT
        data_date,
        REGEXP_EXTRACT(url, r'/r_([a-f0-9]+)') as r_hash,
        impressions,
        clicks,
        sum_position
      FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
      WHERE url LIKE 'https://jp.stanby.com/r_%'
        AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {weeks} WEEK)
    ),
    daily_aggregated AS (
      -- 日次で集計（クエリ等を集約）
      SELECT
        data_date,
        r_hash,
        SUM(impressions) as impressions,
        SUM(clicks) as clicks,
        SUM(sum_position) as sum_position
      FROM r_hash_data
      WHERE r_hash IS NOT NULL
      GROUP BY data_date, r_hash
    ),
    weekly_data AS (
      -- 週次集計
      SELECT
        r_hash,
        DATE_TRUNC(data_date, WEEK(MONDAY)) as week_start,
        SUM(impressions) as total_impressions,
        SUM(clicks) as total_clicks,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) as avg_ctr,
        SAFE_DIVIDE(SUM(sum_position), SUM(impressions)) as avg_position,
        COUNT(DISTINCT data_date) as days_count
      FROM daily_aggregated
      GROUP BY r_hash, week_start
    ),
    weekly_with_prev AS (
      SELECT
        *,
        LAG(total_impressions) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_impressions,
        LAG(total_clicks) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_clicks,
        LAG(avg_ctr) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_ctr,
        LAG(avg_position) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_position
      FROM weekly_data
    )
    SELECT
      r_hash,
      week_start,
      total_impressions,
      total_clicks,
      avg_ctr,
      avg_position,
      prev_impressions,
      prev_clicks,
      prev_ctr,
      prev_position,
      -- 差分計算
      total_impressions - COALESCE(prev_impressions, 0) as imp_diff,
      total_clicks - COALESCE(prev_clicks, 0) as clicks_diff,
      avg_ctr - COALESCE(prev_ctr, 0) as ctr_diff,
      avg_position - COALESCE(prev_position, 0) as position_diff,
      -- 変化率計算（%）
      CASE
        WHEN prev_impressions > 0
        THEN ROUND(((total_impressions - prev_impressions) / prev_impressions) * 100, 2)
        ELSE NULL
      END as imp_change_rate,
      CASE
        WHEN prev_clicks > 0
        THEN ROUND(((total_clicks - prev_clicks) / prev_clicks) * 100, 2)
        ELSE NULL
      END as clicks_change_rate,
      CASE
        WHEN prev_ctr > 0
        THEN ROUND(((avg_ctr - prev_ctr) / prev_ctr) * 100, 2)
        ELSE NULL
      END as ctr_change_rate,
      CASE
        WHEN prev_position > 0
        THEN ROUND(((avg_position - prev_position) / prev_position) * 100, 2)
        ELSE NULL
      END as position_change_rate,
      days_count
    FROM weekly_with_prev
    WHERE prev_impressions IS NOT NULL  -- 前週データがある行のみ
    ORDER BY week_start DESC, imp_diff DESC
    """

    print("BigQueryクエリ実行中...")
    df = client.query(query).to_dataframe()
    print(f"取得完了: {len(df)}行")

    return df

def save_to_csv(df: pd.DataFrame, output_dir: str = './data/search_console'):
    """CSVファイルとして保存"""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"search_console_weekly_{timestamp}.csv")

    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"保存完了: {output_file}")

    return output_file

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--check-schema':
        # スキーマ確認モード
        check_table_schema()
    else:
        # データ取得モード
        try:
            df = get_weekly_search_console_data(weeks=12)
            output_file = save_to_csv(df)

            # サマリー表示
            print("\n=== データサマリー ===")
            print(f"対象期間: {df['week_start'].min()} ～ {df['week_start'].max()}")
            print(f"ユニークr_hash数: {df['r_hash'].nunique()}")
            print(f"総レコード数: {len(df)}")

            print("\n完了！")
        except Exception as e:
            print(f"エラー: {e}")
            sys.exit(1)
