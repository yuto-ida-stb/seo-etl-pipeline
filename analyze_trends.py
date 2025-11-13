import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import glob
from pathlib import Path

def calculate_weekly_changes(df: pd.DataFrame, weeks: int = 12):
    """
    週次の順位と距離の差分、変化率を計算する

    Args:
        df: マージされたデータフレーム（date, キーワード, URL, ランク, 距離カラムを含む）
        weeks: 遡る週数（デフォルト12週=3ヶ月）

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

def generate_insights(analysis_df: pd.DataFrame, output_file: str = None):
    """
    分析データから主要な示唆を生成

    Args:
        analysis_df: 分析済みデータフレーム
        output_file: 示唆を保存するファイル名（Noneの場合は保存しない）
    """
    insights = []

    insights.append("=== SEOデータ分析レポート ===\n")
    insights.append(f"分析期間: {analysis_df['date'].min().strftime('%Y-%m-%d')} ～ {analysis_df['date'].max().strftime('%Y-%m-%d')}\n")
    insights.append(f"総データ数: {len(analysis_df)}件\n")

    # 順位が大きく改善したキーワード（Top 10）
    insights.append("\n【順位が大きく改善したキーワード Top 10】")
    top_improved = analysis_df.nsmallest(10, 'rank_diff')[['keyword', 'url', 'date', 'previous_rank', 'current_rank', 'rank_diff']]
    insights.append(top_improved.to_string(index=False))

    # 順位が大きく下落したキーワード（Top 10）
    insights.append("\n\n【順位が大きく下落したキーワード Top 10】")
    top_declined = analysis_df.nlargest(10, 'rank_diff')[['keyword', 'url', 'date', 'previous_rank', 'current_rank', 'rank_diff']]
    insights.append(top_declined.to_string(index=False))

    # 距離が大きく改善したキーワード（Top 10）
    insights.append("\n\n【距離が大きく改善したキーワード Top 10】")
    top_distance_improved = analysis_df.nsmallest(10, 'distance_diff')[['keyword', 'url', 'date', 'previous_distance', 'current_distance', 'distance_diff']]
    insights.append(top_distance_improved.to_string(index=False))

    # 統計サマリー
    insights.append("\n\n【統計サマリー】")
    insights.append(f"平均順位変化: {analysis_df['rank_diff'].mean():.2f}")
    insights.append(f"平均距離変化: {analysis_df['distance_diff'].mean():.2f}")
    insights.append(f"順位改善件数: {len(analysis_df[analysis_df['rank_diff'] < 0])}件")
    insights.append(f"順位下落件数: {len(analysis_df[analysis_df['rank_diff'] > 0])}件")

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

    # 週次変化を計算（3ヶ月 = 12週）
    analysis_df = calculate_weekly_changes(df, weeks=12)

    # 分析結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = "./data/analysis"
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    analysis_output = os.path.join(output_folder, f"weekly_analysis_{timestamp}.csv")
    analysis_df.to_csv(analysis_output, index=False, encoding='utf-8-sig')
    print(f"分析結果を保存: {analysis_output}")

    # 示唆レポートを生成
    insights_output = os.path.join(output_folder, f"insights_report_{timestamp}.txt")
    generate_insights(analysis_df, insights_output)
