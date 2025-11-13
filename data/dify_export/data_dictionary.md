# SEO ETLパイプライン データ辞書

## 1. SEOランク分析データ

### データソース
- Google Drive (`00_raw_data`フォルダ)
- 週次平均データ（現在は日次データで代用）

### カラム定義
- **keyword**: 検索キーワード
- **url**: 対象URL（r_hash形式）
- **date**: データ取得日
- **previous_rank**: 前回の検索順位
- **current_rank**: 現在の検索順位
- **rank_diff**: 順位変化（負の値が改善）
- **previous_distance**: 前回の距離スコア
- **current_distance**: 現在の距離スコア
- **distance_diff**: 距離変化（負の値が改善）

## 2. Search Console分析データ（r_hash別）

### データソース
- BigQuery: `stanby-prod.searchconsole.searchdata_url_impression`
- 週次集計（月曜日始まり）

### カラム定義
- **r_hash**: SEO向け求人一覧ページのハッシュ値
- **week_start**: 週の開始日（月曜日）
- **total_impressions**: 週次総インプレッション数
- **total_clicks**: 週次総クリック数
- **avg_ctr**: 週次平均CTR（クリック率）
- **avg_position**: 週次平均検索順位
- **prev_***: 前週の各指標
- ***_diff**: 前週比の差分
- ***_change_rate**: 前週比の変化率（%）
- **days_count**: データがある日数

## よくある質問

### Q1: 順位が良いとはどういうことですか？
A: 検索順位は小さいほど良いです（1位が最も良い）。順位変化（rank_diff）が負の値の場合、順位が改善しています。

### Q2: r_hashとは何ですか？
A: SEO向けの求人一覧ページを識別するハッシュ値です。例: `https://jp.stanby.com/r_a15acbf7cde25342eae61940978698aa`

### Q3: CTRとは何ですか？
A: Click Through Rate（クリック率）の略で、インプレッション数に対するクリック数の割合です。CTRが高いほど、ユーザーにとって魅力的なコンテンツと言えます。

### Q4: 距離（distance）とは何ですか？
A: 検索結果との関連性を示すスコアです。距離が小さいほど、検索クエリに対してより関連性が高いと判断されています。

