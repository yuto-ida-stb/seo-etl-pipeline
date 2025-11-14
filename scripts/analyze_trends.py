import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import glob
from pathlib import Path

def calculate_weekly_changes(df: pd.DataFrame, weeks: int = 12):
    """
    期間ごとの順位と距離の差分、変化率を計算する

    注: 週次データの場合は週次比較、日次データの場合は日次比較として動作します。

    Args:
        df: マージされたデータフレーム（date, キーワード, URL, ランク, 距離カラムを含む）
        weeks: 遡る期間数（デフォルト12期間=週次なら3ヶ月分）

    Returns:
        変化率と差分を含むデータフレーム
    """
    # カラム名を英語にマッピング
    df = df.rename(columns={
        'キーワード': 'keyword',
        'URL': 'url',
        'ランク': 'rank',
        '距離': 'distance'
    })

    # データ型を変換
    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce')

    # 日付カラムをdatetime型に変換
    df['date'] = pd.to_datetime(df['date'])

    # NaNを含む行を除外
    df = df.dropna(subset=['rank', 'distance'])

    # データを日付順にソート
    df = df.sort_values(['keyword', 'url', 'date'])

    # keyword + url で グループ化
    df['key'] = df['keyword'] + '_' + df['url']

    results = []

    for key, group in df.groupby('key'):
        group = group.sort_values('date').reset_index(drop=True)

        # 最新のweeks週分のデータのみ使用
        if len(group) > weeks:
            group = group.tail(weeks)

        for i in range(1, len(group)):
            current = group.iloc[i]
            previous = group.iloc[i-1]

            # 前週との差分を計算
            rank_diff = current['rank'] - previous['rank']
            distance_diff = current['distance'] - previous['distance']

            # 変化率を計算（0除算を避ける）
            rank_change_rate = (rank_diff / previous['rank'] * 100) if previous['rank'] != 0 else 0
            distance_change_rate = (distance_diff / previous['distance'] * 100) if previous['distance'] != 0 else 0

            # 週単位の経過
            weeks_elapsed = (current['date'] - previous['date']).days // 7

            result = {
                'date': current['date'],
                'keyword': current['keyword'],
                'url': current['url'],
                'current_rank': current['rank'],
                'previous_rank': previous['rank'],
                'rank_diff': rank_diff,
                'rank_change_rate': round(rank_change_rate, 2),
                'current_distance': current['distance'],
                'previous_distance': previous['distance'],
                'distance_diff': round(distance_diff, 2),
                'distance_change_rate': round(distance_change_rate, 2),
                'weeks_elapsed': weeks_elapsed,
            }

            results.append(result)

    return pd.DataFrame(results)

def analyze_trends_over_period(df: pd.DataFrame, min_data_points: int = 5):
    """
    期間全体の推移を分析し、継続的に改善/悪化しているキーワードを抽出

    Args:
        df: 元のデータフレーム（date, keyword, url, rank, distanceカラムを含む）
        min_data_points: 分析に必要な最小データポイント数

    Returns:
        継続的改善/悪化キーワードのリスト
    """
    # カラム名を統一
    if 'キーワード' in df.columns:
        df = df.rename(columns={'キーワード': 'keyword', 'URL': 'url', 'ランク': 'rank', '距離': 'distance'})

    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce')
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['rank', 'distance'])
    df = df.sort_values(['keyword', 'url', 'date'])

    trends = []

    for (keyword, url), group in df.groupby(['keyword', 'url']):
        group = group.sort_values('date').reset_index(drop=True)

        # データポイントが少ない場合はスキップ
        if len(group) < min_data_points:
            continue

        # 最初と最後の順位
        first_rank = group.iloc[0]['rank']
        last_rank = group.iloc[-1]['rank']
        total_change = last_rank - first_rank

        # 線形回帰で傾向を計算
        x = np.arange(len(group))
        y = group['rank'].values

        # 傾き（正＝悪化、負＝改善）
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
        else:
            slope = 0

        # 単調性チェック（連続して改善/悪化している回数）
        improvements = 0
        deteriorations = 0

        for i in range(1, len(group)):
            diff = group.iloc[i]['rank'] - group.iloc[i-1]['rank']
            if diff < 0:  # 改善
                improvements += 1
            elif diff > 0:  # 悪化
                deteriorations += 1

        # 一貫性スコア（-1〜1、負＝改善傾向、正＝悪化傾向）
        total_changes = improvements + deteriorations
        if total_changes > 0:
            consistency_score = (deteriorations - improvements) / total_changes
        else:
            consistency_score = 0

        trends.append({
            'keyword': keyword,
            'url': url,
            'first_date': group.iloc[0]['date'],
            'last_date': group.iloc[-1]['date'],
            'first_rank': first_rank,
            'last_rank': last_rank,
            'total_change': total_change,
            'slope': slope,
            'improvements': improvements,
            'deteriorations': deteriorations,
            'consistency_score': consistency_score,
            'data_points': len(group)
        })

    return pd.DataFrame(trends)

def generate_insights(analysis_df: pd.DataFrame, original_df: pd.DataFrame = None, output_file: str = None):
    """
    分析データから主要な示唆を生成（期間全体の推移ベース）

    Args:
        analysis_df: 分析済みデータフレーム（週次変化）
        original_df: 元のデータフレーム（推移分析用）
        output_file: 示唆を保存するファイル名（Noneの場合は保存しない）
    """
    insights = []

    insights.append("=== SEOデータ分析レポート（推移分析） ===\n")
    insights.append(f"分析期間: {analysis_df['date'].min().strftime('%Y-%m-%d')} ～ {analysis_df['date'].max().strftime('%Y-%m-%d')}\n")
    insights.append(f"総データ数: {len(analysis_df)}件\n")

    # 推移分析（元データがある場合）
    if original_df is not None:
        trends_df = analyze_trends_over_period(original_df, min_data_points=5)

        # 継続的に改善しているキーワード（負の傾きが大きく、一貫性が高い）
        improving = trends_df[
            (trends_df['slope'] < 0) &  # 改善傾向
            (trends_df['consistency_score'] < -0.3)  # 一貫して改善
        ].sort_values('slope').head(10)

        insights.append("\n【継続的に順位が改善しているキーワード Top 10】")
        insights.append("（期間全体で一貫して順位が上昇しているもの）\n")
        if len(improving) > 0:
            display_cols = ['keyword', 'first_rank', 'last_rank', 'total_change', 'improvements', 'data_points']
            improving_display = improving[display_cols].copy()
            improving_display.columns = ['キーワード', '初期順位', '最新順位', '総変化', '改善回数', 'データ数']
            insights.append(improving_display.to_string(index=False))
        else:
            insights.append("該当なし")

        # 継続的に悪化しているキーワード（正の傾きが大きく、一貫性が高い）
        deteriorating = trends_df[
            (trends_df['slope'] > 0) &  # 悪化傾向
            (trends_df['consistency_score'] > 0.3)  # 一貫して悪化
        ].sort_values('slope', ascending=False).head(10)

        insights.append("\n\n【継続的に順位が悪化しているキーワード Top 10】")
        insights.append("（期間全体で一貫して順位が下降しているもの）\n")
        if len(deteriorating) > 0:
            display_cols = ['keyword', 'first_rank', 'last_rank', 'total_change', 'deteriorations', 'data_points']
            deteriorating_display = deteriorating[display_cols].copy()
            deteriorating_display.columns = ['キーワード', '初期順位', '最新順位', '総変化', '悪化回数', 'データ数']
            insights.append(deteriorating_display.to_string(index=False))
        else:
            insights.append("該当なし")

        # 最も改善幅が大きいキーワード
        insights.append("\n\n【期間全体で最も改善したキーワード Top 10】")
        top_improved = trends_df.nsmallest(10, 'total_change')[['keyword', 'first_rank', 'last_rank', 'total_change', 'data_points']]
        if len(top_improved) > 0:
            top_improved_display = top_improved.copy()
            top_improved_display.columns = ['キーワード', '初期順位', '最新順位', '総変化', 'データ数']
            insights.append(top_improved_display.to_string(index=False))

        # 最も悪化幅が大きいキーワード
        insights.append("\n\n【期間全体で最も悪化したキーワード Top 10】")
        top_declined = trends_df.nlargest(10, 'total_change')[['keyword', 'first_rank', 'last_rank', 'total_change', 'data_points']]
        if len(top_declined) > 0:
            top_declined_display = top_declined.copy()
            top_declined_display.columns = ['キーワード', '初期順位', '最新順位', '総変化', 'データ数']
            insights.append(top_declined_display.to_string(index=False))

    # 統計サマリー
    insights.append("\n\n【統計サマリー】")
    insights.append(f"平均順位変化（週次）: {analysis_df['rank_diff'].mean():.2f}")
    insights.append(f"平均距離変化（週次）: {analysis_df['distance_diff'].mean():.2f}")
    insights.append(f"順位改善件数（週次）: {len(analysis_df[analysis_df['rank_diff'] < 0])}件")
    insights.append(f"順位下落件数（週次）: {len(analysis_df[analysis_df['rank_diff'] > 0])}件")

    # カテゴリ別サマリー
    if 'カテゴリ' in analysis_df.columns and analysis_df['カテゴリ'].notna().sum() > 0:
        insights.append("\n\n【カテゴリ別サマリー】")
        category_summary = analysis_df[analysis_df['カテゴリ'].notna()].groupby('カテゴリ').agg({
            'rank_diff': ['mean', 'count'],
            'keyword': 'nunique'
        }).round(2)
        category_summary.columns = ['平均順位変化', 'データ数', 'ユニークキーワード数']
        category_summary = category_summary.sort_values('平均順位変化')
        insights.append(category_summary.to_string())

    report = "\n".join(insights)
    print(report)

    if output_file:
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n示唆レポートを保存しました: {output_file}")

    return report

if __name__ == "__main__":
    # マージ済みデータを読み込み（最新のファイルを自動検出）
    processed_folder = "./data/processed"
    csv_files = sorted(glob.glob(os.path.join(processed_folder, "merged_data_*.csv")))

    if not csv_files:
        print(f"エラー: {processed_folder}にマージ済みファイルが見つかりません。先にmerge_data.pyを実行してください。")
        exit(1)

    input_file = csv_files[-1]  # 最新のファイルを使用
    print(f"使用するファイル: {input_file}")

    df = pd.read_csv(input_file)
    print(f"データ読み込み完了: {len(df)}行")

    # カテゴリマッピングを読み込み
    category_mapping_file = "./data/category_mapping.csv"
    if os.path.exists(category_mapping_file):
        print(f"カテゴリマッピングを読み込み中: {category_mapping_file}")
        category_df = pd.read_csv(category_mapping_file)
        print(f"カテゴリマッピング: {len(category_df)}行")

        # キーワード列を統一
        if 'キーワード' in df.columns:
            keyword_col = 'キーワード'
        else:
            keyword_col = 'keyword'

        # カテゴリ情報をマージ
        df = df.merge(
            category_df[['キーワード', 'カテゴリ', 'Groups']],
            left_on=keyword_col,
            right_on='キーワード',
            how='left'
        )
        print(f"カテゴリ情報をマージ完了")
        print(f"カテゴリがマッチしたキーワード数: {df['カテゴリ'].notna().sum()}件")
    else:
        print(f"警告: カテゴリマッピングファイルが見つかりません: {category_mapping_file}")

    # 週次変化を計算（3ヶ月 = 12週）
    analysis_df = calculate_weekly_changes(df, weeks=12)

    # カテゴリ情報を分析結果にもマージ
    if 'カテゴリ' in df.columns:
        # キーワード列を確認
        if 'キーワード' in df.columns:
            df_category = df[['キーワード', 'URL', 'カテゴリ', 'Groups']].drop_duplicates()
        else:
            df_category = df[['keyword', 'url', 'カテゴリ', 'Groups']].drop_duplicates()
            df_category = df_category.rename(columns={'keyword': 'キーワード', 'url': 'URL'})

        analysis_df = analysis_df.merge(
            df_category,
            left_on=['keyword', 'url'],
            right_on=['キーワード', 'URL'],
            how='left'
        )
        print(f"分析結果にカテゴリ情報をマージ: {analysis_df['カテゴリ'].notna().sum()}件マッチ")

    # 分析結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = "./data/analysis"
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    analysis_output = os.path.join(output_folder, f"weekly_analysis_{timestamp}.csv")
    analysis_df.to_csv(analysis_output, index=False, encoding='utf-8-sig')
    print(f"分析結果を保存: {analysis_output}")

    # 示唆レポートを生成（元データも渡して推移分析を行う）
    insights_output = os.path.join(output_folder, f"insights_report_{timestamp}.txt")
    generate_insights(analysis_df, original_df=df, output_file=insights_output)
