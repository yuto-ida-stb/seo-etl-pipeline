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

def get_weekly_search_console_data(weeks: int = 12, min_impressions: int = 10):
    """
    週次のSearch Consoleデータを取得し、前週比を計算

    r_hash別（SEO向け求人一覧ページ）の週次集計を行います。
    パフォーマンス向上のため、一定以上のインプレッションがあるr_hashのみ取得します。

    Args:
        weeks: 取得する週数（デフォルト12週=3ヶ月）
        min_impressions: 週次の最小インプレッション数（デフォルト10）

    Returns:
        週次データと前週比を含むDataFrame
    """
    client = get_bigquery_client()

    print(f"BigQueryクエリを構築中...")
    print(f"  対象期間: 過去{weeks}週")
    print(f"  最小インプレッション: {min_impressions}/週")

    # 最適化されたクエリ：WHEREを先に適用してスキャン量を削減
    query = f"""
    WITH filtered_data AS (
      -- 最初にフィルタを適用してデータ量を削減
      SELECT
        data_date,
        REGEXP_EXTRACT(url, r'/r_([a-f0-9]+)') as r_hash,
        impressions,
        clicks,
        sum_position
      FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
      WHERE
        -- 日付フィルタを最初に適用（パーティションがあれば高速）
        data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {weeks} WEEK)
        -- r_hashページのみ
        AND url LIKE 'https://jp.stanby.com/r_%'
        -- インプレッションがあるもののみ
        AND impressions > 0
    ),
    daily_aggregated AS (
      -- 日次で集計（クエリ等を集約）
      SELECT
        data_date,
        r_hash,
        SUM(impressions) as impressions,
        SUM(clicks) as clicks,
        SUM(sum_position) as sum_position
      FROM filtered_data
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
      -- 週次インプレッションが一定以上のr_hashのみ
      HAVING SUM(impressions) >= {min_impressions}
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

    print("\nBigQueryクエリ実行中...")
    print("※大量データのため、数分かかる場合があります...")

    # ジョブを開始
    query_job = client.query(query)

    # 進捗を表示しながら待機
    import time
    start_time = time.time()
    while not query_job.done():
        elapsed = int(time.time() - start_time)
        print(f"  実行中... ({elapsed}秒経過)", end='\r')
        time.sleep(2)

    elapsed = int(time.time() - start_time)
    print(f"\n✓ クエリ完了 ({elapsed}秒)")

    # 結果を取得
    print("結果を取得中...")
    df = query_job.to_dataframe()
    print(f"✓ 取得完了: {len(df):,}行")

    if len(df) == 0:
        print("\n警告: データが0件でした。期間やフィルタ条件を確認してください。")

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
            # デフォルト: 12週間、最小インプレッション10
            weeks = int(sys.argv[1]) if len(sys.argv) > 1 else 12
            min_imp = int(sys.argv[2]) if len(sys.argv) > 2 else 10

            print("="*50)
            print("Search Console 週次データ取得")
            print("="*50)

            df = get_weekly_search_console_data(weeks=weeks, min_impressions=min_imp)

            if len(df) == 0:
                print("\n⚠ データが取得できませんでした")
                sys.exit(0)

            output_file = save_to_csv(df)

            # サマリー表示
            print("\n" + "="*50)
            print("=== データサマリー ===")
            print("="*50)
            print(f"対象期間: {df['week_start'].min()} ～ {df['week_start'].max()}")
            print(f"ユニークr_hash数: {df['r_hash'].nunique():,}")
            print(f"総レコード数: {len(df):,}")
            print(f"\nTop 5 インプレッション増加:")
            print(df.nlargest(5, 'imp_diff')[['r_hash', 'week_start', 'total_impressions', 'imp_diff', 'imp_change_rate']].to_string(index=False))
            print(f"\nTop 5 CTR改善:")
            print(df.nlargest(5, 'ctr_diff')[['r_hash', 'week_start', 'avg_ctr', 'ctr_diff', 'ctr_change_rate']].to_string(index=False))

            print("\n✅ 完了！")
            print(f"ファイル: {output_file}")
        except KeyboardInterrupt:
            print("\n\n中断されました")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
