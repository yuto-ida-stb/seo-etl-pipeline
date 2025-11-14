-- ================================================================================
-- Search Console 週次分析クエリ（r_hash別） - 【前週 vs 2週間前 比較版】
-- ================================================================================
-- 目的: SEO向け求人一覧ページ（r_hash）の「前週」と「2週間前」のパフォーマンスを比較分析
-- 対象: /r_で始まるURL
-- 比較対象:
--   - 今週の指標 = 1週間前の月曜日～日曜日
--   - 前週の指標 = 2週間前の月曜日～日曜日
-- 指標: インプレッション、クリック、CTR、平均順位
-- 出力: r_hash別の「前週」データと、「2週間前」との差分・変化率
-- ================================================================================

-- パラメータ（Pythonスクリプトから置換される）
-- {min_impressions}: 週次の最小インプレッション数（デフォルト: 50）
-- {project_id}: BigQueryプロジェクトID
-- {dataset_id}: データセット名
-- {table_id}: テーブル名

WITH
 -- ================================================================================
 -- STEP 1: データフィルタリング
 -- ================================================================================
 -- 目的: 必要な2週間分（2週間前の月曜日以降）のデータのみを抽出
 -- 処理: 日付・URL・インプレッション条件でフィルタ
 filtered_data AS (
  SELECT
   data_date,
   REGEXP_EXTRACT(url, r'/r_([a-f0-9]+)') as query_hash, -- URLからr_hash部分を抽出
   impressions,
   clicks,
   sum_position -- 順位の合計
  FROM `{project_id}.{dataset_id}.{table_id}`
  WHERE
   -- 日付フィルタ: 2週間前の月曜日以降のデータのみ取得
   data_date >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 WEEK), WEEK(MONDAY))
   -- r_hashページのみ
   AND url LIKE 'https://jp.stanby.com/r_%'
   -- インプレッションがあるデータのみ
   AND impressions > 0
 ),

 -- ================================================================================
 -- STEP 2: 日次集計
 -- ================================================================================
 -- 目的: r_hash × 日付単位で集計
 -- 処理: r_hashと日付でグループ化してSUM集計
 daily_aggregated AS (
  SELECT
   data_date,
   query_hash,
   SUM(impressions) as impressions,
   SUM(clicks) as clicks,
   SUM(sum_position) as sum_position
  FROM filtered_data
  WHERE query_hash IS NOT NULL
  GROUP BY data_date, query_hash
 ),

 -- ================================================================================
 -- STEP 3: 週次集計
 -- ================================================================================
 -- 目的: 日次データを週単位（月曜日始まり）に集計
 -- 処理: 週ごとにインプレッション・クリック・CTR・平均順位を計算
 weekly_data AS (
  SELECT
   query_hash,
   DATE_TRUNC(data_date, WEEK(MONDAY)) as week_start, -- 週の開始日（月曜日）
   SUM(impressions) as total_impressions,
   SUM(clicks) as total_clicks,
   SAFE_DIVIDE(SUM(clicks), SUM(impressions)) as avg_ctr,
   
   -- 【修正点】ご指定の計算方法（1始まり・四捨五入）に変更
   ROUND(SUM(sum_position) / SUM(impressions)) + 1 AS avg_position, 
   
   COUNT(DISTINCT data_date) as days_count
  FROM daily_aggregated
  GROUP BY query_hash, week_start
  -- パフォーマンス向上: 週次インプレッションが一定以上のr_hashのみ取得
  HAVING SUM(impressions) >= {min_impressions}
 ),

 -- ================================================================================
 -- STEP 4: 前週データの追加
 -- ================================================================================
 -- 目的: r_hash別に前週（2週間前）のデータを取得
 -- 処理: LAG関数を使用して同じr_hashの1週前のデータを取得
 weekly_with_prev AS (
  SELECT
   *,
   LAG(total_impressions) OVER (PARTITION BY query_hash ORDER BY week_start) as prev_impressions,
   LAG(total_clicks) OVER (PARTITION BY query_hash ORDER BY week_start) as prev_clicks,
   LAG(avg_ctr) OVER (PARTITION BY query_hash ORDER BY week_start) as prev_ctr,
   LAG(avg_position) OVER (PARTITION BY query_hash ORDER BY week_start) as prev_position
  FROM weekly_data
 )

-- ================================================================================
-- STEP 5: 最終出力（差分・変化率の計算）
-- ================================================================================
-- 目的: 「前週」と「2週間前」のデータを比較し、差分と変化率を計算
SELECT
 query_hash,
 query_keyword,
 query_location,
 cate,
 week_start,

 -- 今週の指標（= 1週間前の週）
 total_impressions,
 total_clicks,
 avg_ctr,
 avg_position,

 -- 前週の指標（= 2週間前の週）
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

FROM weekly_with_prev w
left join `stanby-prod.temp_adhoc.query_category` m
on w.query_hash = m.query_hash
-- 前週（week_startが1週間前の月曜日）のデータのみを出力
WHERE week_start = DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK), WEEK(MONDAY))
ORDER BY imp_diff DESC
