-- ================================================================================
-- Search Console 週次分析クエリ（r_hash別）
-- ================================================================================
-- 目的: SEO向け求人一覧ページ（r_hash）の週次パフォーマンスを分析
-- 対象: /r_で始まるURL（例: https://jp.stanby.com/r_a15acbf7cde25342eae61940978698aa）
-- 指標: インプレッション、クリック、CTR、平均順位
-- 出力: r_hash別の週次データと前週比（差分・変化率）
-- ================================================================================

-- パラメータ（Pythonスクリプトから置換される）
-- {weeks}: 取得する週数（デフォルト: 12週 = 3ヶ月）
-- {min_impressions}: 週次の最小インプレッション数（デフォルト: 50）
-- {project_id}: BigQueryプロジェクトID
-- {dataset_id}: データセット名
-- {table_id}: テーブル名

WITH
  -- ================================================================================
  -- STEP 1: データフィルタリング
  -- ================================================================================
  -- 目的: 31億行のテーブルから必要なデータのみを抽出（パフォーマンス最適化）
  -- 処理: 日付・URL・インプレッション条件でフィルタ
  filtered_data AS (
    SELECT
      data_date,
      REGEXP_EXTRACT(url, r'/r_([a-f0-9]+)') as r_hash,  -- URLからr_hash部分を抽出
      impressions,
      clicks,
      sum_position  -- 順位の合計（平均順位 = sum_position / impressions）
    FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE
      -- 日付フィルタ（パーティション列なら高速）
      data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {weeks} WEEK)
      -- r_hashページのみ（/r_で始まるURL）
      AND url LIKE 'https://jp.stanby.com/r_%'
      -- インプレッションがあるデータのみ
      AND impressions > 0
  ),

  -- ================================================================================
  -- STEP 2: 日次集計
  -- ================================================================================
  -- 目的: r_hash × 日付単位で集計（複数クエリ・デバイス等を集約）
  -- 処理: r_hashと日付でグループ化してSUM集計
  daily_aggregated AS (
    SELECT
      data_date,
      r_hash,
      SUM(impressions) as impressions,
      SUM(clicks) as clicks,
      SUM(sum_position) as sum_position
    FROM filtered_data
    WHERE r_hash IS NOT NULL  -- r_hashが抽出できたデータのみ
    GROUP BY data_date, r_hash
  ),

  -- ================================================================================
  -- STEP 3: 週次集計
  -- ================================================================================
  -- 目的: 日次データを週単位（月曜日始まり）に集計
  -- 処理: 週ごとにインプレッション・クリック・CTR・平均順位を計算
  weekly_data AS (
    SELECT
      r_hash,
      DATE_TRUNC(data_date, WEEK(MONDAY)) as week_start,  -- 週の開始日（月曜日）
      SUM(impressions) as total_impressions,              -- 週次総インプレッション
      SUM(clicks) as total_clicks,                        -- 週次総クリック数
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) as avg_ctr,  -- 週次平均CTR
      SAFE_DIVIDE(SUM(sum_position), SUM(impressions)) as avg_position,  -- 週次平均順位
      COUNT(DISTINCT data_date) as days_count             -- データがある日数
    FROM daily_aggregated
    GROUP BY r_hash, week_start
    -- パフォーマンス向上: 週次インプレッションが一定以上のr_hashのみ取得
    HAVING SUM(impressions) >= {min_impressions}
  ),

  -- ================================================================================
  -- STEP 4: 前週データの追加
  -- ================================================================================
  -- 目的: r_hash別に前週のデータを取得（前週比計算のため）
  -- 処理: LAG関数を使用して同じr_hashの1週前のデータを取得
  weekly_with_prev AS (
    SELECT
      *,
      LAG(total_impressions) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_impressions,
      LAG(total_clicks) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_clicks,
      LAG(avg_ctr) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_ctr,
      LAG(avg_position) OVER (PARTITION BY r_hash ORDER BY week_start) as prev_position
    FROM weekly_data
  )

-- ================================================================================
-- STEP 5: 最終出力（差分・変化率の計算）
-- ================================================================================
-- 目的: 前週比の差分と変化率を計算して出力
-- 出力カラム:
--   - 基本情報: r_hash, week_start
--   - 今週の指標: total_impressions, total_clicks, avg_ctr, avg_position
--   - 前週の指標: prev_impressions, prev_clicks, prev_ctr, prev_position
--   - 差分: imp_diff, clicks_diff, ctr_diff, position_diff
--   - 変化率(%): imp_change_rate, clicks_change_rate, ctr_change_rate, position_change_rate
--   - その他: days_count（データがある日数）
SELECT
  r_hash,
  week_start,

  -- 今週の指標
  total_impressions,
  total_clicks,
  avg_ctr,
  avg_position,

  -- 前週の指標
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
WHERE prev_impressions IS NOT NULL  -- 前週データがある行のみ（初週は除外）
ORDER BY week_start DESC, imp_diff DESC
