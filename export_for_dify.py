"""
DifyのナレッジベースにアップロードするためのMarkdownファイルを生成
"""
import pandas as pd
import os
from datetime import datetime
import glob

OUTPUT_DIR = './data/dify_export'

def export_seo_rank_analysis():
    """SEOランク分析データをMarkdown形式でエクスポート"""
    # 最新のCSVとレポートを取得
    csv_files = sorted(glob.glob('./data/analysis/weekly_analysis_*.csv'))
    txt_files = sorted(glob.glob('./data/analysis/insights_report_*.txt'))

    if not csv_files:
        print("SEOランク分析データが見つかりません")
        return

    latest_csv = csv_files[-1]
    latest_txt = txt_files[-1] if txt_files else None

    # CSVデータを読み込み
    df = pd.read_csv(latest_csv)

    # Markdown形式で出力
    output = []
    output.append("# SEOランク分析データ\n")
    output.append(f"**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    output.append(f"**データ期間**: {df['date'].min()} ～ {df['date'].max()}\n")
    output.append(f"**総データ数**: {len(df):,}件\n\n")

    # インサイトレポートを追加
    if latest_txt and os.path.exists(latest_txt):
        output.append("## 分析サマリー\n\n")
        with open(latest_txt, 'r', encoding='utf-8') as f:
            output.append(f.read())
        output.append("\n\n")

    # 詳細データ（サンプル）
    output.append("## 詳細データ（最新100件）\n\n")
    output.append("| キーワード | URL | 日付 | 前回順位 | 現在順位 | 順位変化 | 前回距離 | 現在距離 | 距離変化 |\n")
    output.append("|----------|-----|------|---------|---------|---------|---------|---------|----------|\n")

    for _, row in df.head(100).iterrows():
        output.append(f"| {row['keyword']} | {row['url'][:50]}... | {row['date']} | "
                     f"{row['previous_rank']:.0f} | {row['current_rank']:.0f} | {row['rank_diff']:+.0f} | "
                     f"{row['previous_distance']:.0f} | {row['current_distance']:.0f} | {row['distance_diff']:+.0f} |\n")

    # ファイルに保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, 'seo_rank_analysis.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output)

    print(f"✓ SEOランク分析データをエクスポート: {output_file}")
    return output_file

def export_search_console_analysis():
    """Search Console分析データをMarkdown形式でエクスポート"""
    # 最新のCSVを取得
    csv_files = sorted(glob.glob('./data/search_console/search_console_weekly_*.csv'))

    if not csv_files:
        print("Search Consoleデータが見つかりません")
        return

    latest_csv = csv_files[-1]
    df = pd.read_csv(latest_csv)

    # Markdown形式で出力
    output = []
    output.append("# Search Console週次分析データ（r_hash別）\n")
    output.append(f"**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    output.append(f"**データ期間**: {df['week_start'].min()} ～ {df['week_start'].max()}\n")
    output.append(f"**総レコード数**: {len(df):,}件\n")
    output.append(f"**ユニークr_hash数**: {df['r_hash'].nunique():,}件\n\n")

    # トップパフォーマー
    output.append("## インプレッション増加 Top 20\n\n")
    output.append("| r_hash | 週開始日 | 今週imp | 前週imp | 差分 | 変化率(%) |\n")
    output.append("|--------|---------|---------|---------|------|----------|\n")

    top_imp = df.nlargest(20, 'imp_diff')
    for _, row in top_imp.iterrows():
        output.append(f"| {row['r_hash'][:16]}... | {row['week_start']} | "
                     f"{row['total_impressions']:,.0f} | {row['prev_impressions']:,.0f} | "
                     f"{row['imp_diff']:+,.0f} | {row['imp_change_rate']:+.1f}% |\n")

    output.append("\n## CTR改善 Top 20\n\n")
    output.append("| r_hash | 週開始日 | 今週CTR | 前週CTR | 差分 | 変化率(%) |\n")
    output.append("|--------|---------|---------|---------|------|----------|\n")

    top_ctr = df.nlargest(20, 'ctr_diff')
    for _, row in top_ctr.iterrows():
        output.append(f"| {row['r_hash'][:16]}... | {row['week_start']} | "
                     f"{row['avg_ctr']:.4f} | {row['prev_ctr']:.4f} | "
                     f"{row['ctr_diff']:+.4f} | {row['ctr_change_rate']:+.1f}% |\n")

    output.append("\n## 順位改善 Top 20\n\n")
    output.append("| r_hash | 週開始日 | 今週順位 | 前週順位 | 差分 | 変化率(%) |\n")
    output.append("|--------|---------|---------|---------|------|----------|\n")

    # 順位は小さいほど良いので、position_diffが負の方が改善
    top_pos = df.nsmallest(20, 'position_diff')
    for _, row in top_pos.iterrows():
        output.append(f"| {row['r_hash'][:16]}... | {row['week_start']} | "
                     f"{row['avg_position']:.1f} | {row['prev_position']:.1f} | "
                     f"{row['position_diff']:+.1f} | {row['position_change_rate']:+.1f}% |\n")

    # 統計サマリー
    output.append("\n## 統計サマリー\n\n")
    output.append(f"- **平均インプレッション変化**: {df['imp_diff'].mean():+,.1f}\n")
    output.append(f"- **平均CTR変化**: {df['ctr_diff'].mean():+.4f}\n")
    output.append(f"- **平均順位変化**: {df['position_diff'].mean():+.2f}\n")
    output.append(f"- **インプレッション増加r_hash数**: {(df['imp_diff'] > 0).sum():,}件\n")
    output.append(f"- **インプレッション減少r_hash数**: {(df['imp_diff'] < 0).sum():,}件\n")

    # ファイルに保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, 'search_console_analysis.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output)

    print(f"✓ Search Console分析データをエクスポート: {output_file}")
    return output_file

def export_metadata():
    """メタデータとデータ説明を生成"""
    output = []
    output.append("# SEO ETLパイプライン データ辞書\n\n")

    output.append("## 1. SEOランク分析データ\n\n")
    output.append("### データソース\n")
    output.append("- Google Drive (`00_raw_data`フォルダ)\n")
    output.append("- 週次平均データ（現在は日次データで代用）\n\n")

    output.append("### カラム定義\n")
    output.append("- **keyword**: 検索キーワード\n")
    output.append("- **url**: 対象URL（r_hash形式）\n")
    output.append("- **date**: データ取得日\n")
    output.append("- **previous_rank**: 前回の検索順位\n")
    output.append("- **current_rank**: 現在の検索順位\n")
    output.append("- **rank_diff**: 順位変化（負の値が改善）\n")
    output.append("- **previous_distance**: 前回の距離スコア\n")
    output.append("- **current_distance**: 現在の距離スコア\n")
    output.append("- **distance_diff**: 距離変化（負の値が改善）\n\n")

    output.append("## 2. Search Console分析データ（r_hash別）\n\n")
    output.append("### データソース\n")
    output.append("- BigQuery: `stanby-prod.searchconsole.searchdata_url_impression`\n")
    output.append("- 週次集計（月曜日始まり）\n\n")

    output.append("### カラム定義\n")
    output.append("- **r_hash**: SEO向け求人一覧ページのハッシュ値\n")
    output.append("- **week_start**: 週の開始日（月曜日）\n")
    output.append("- **total_impressions**: 週次総インプレッション数\n")
    output.append("- **total_clicks**: 週次総クリック数\n")
    output.append("- **avg_ctr**: 週次平均CTR（クリック率）\n")
    output.append("- **avg_position**: 週次平均検索順位\n")
    output.append("- **prev_***: 前週の各指標\n")
    output.append("- ***_diff**: 前週比の差分\n")
    output.append("- ***_change_rate**: 前週比の変化率（%）\n")
    output.append("- **days_count**: データがある日数\n\n")

    output.append("## よくある質問\n\n")
    output.append("### Q1: 順位が良いとはどういうことですか？\n")
    output.append("A: 検索順位は小さいほど良いです（1位が最も良い）。順位変化（rank_diff）が負の値の場合、順位が改善しています。\n\n")

    output.append("### Q2: r_hashとは何ですか？\n")
    output.append("A: SEO向けの求人一覧ページを識別するハッシュ値です。例: `https://jp.stanby.com/r_a15acbf7cde25342eae61940978698aa`\n\n")

    output.append("### Q3: CTRとは何ですか？\n")
    output.append("A: Click Through Rate（クリック率）の略で、インプレッション数に対するクリック数の割合です。CTRが高いほど、ユーザーにとって魅力的なコンテンツと言えます。\n\n")

    output.append("### Q4: 距離（distance）とは何ですか？\n")
    output.append("A: 検索結果との関連性を示すスコアです。距離が小さいほど、検索クエリに対してより関連性が高いと判断されています。\n\n")

    # ファイルに保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, 'data_dictionary.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output)

    print(f"✓ データ辞書をエクスポート: {output_file}")
    return output_file

if __name__ == '__main__':
    print("=" * 50)
    print("Dify用データエクスポート")
    print("=" * 50)
    print()

    files = []

    # SEOランク分析データ
    file1 = export_seo_rank_analysis()
    if file1:
        files.append(file1)

    # Search Console分析データ
    file2 = export_search_console_analysis()
    if file2:
        files.append(file2)

    # メタデータ
    file3 = export_metadata()
    if file3:
        files.append(file3)

    print()
    print("=" * 50)
    print("✅ エクスポート完了")
    print("=" * 50)
    print()
    print("次のステップ:")
    print("1. https://dify.ai にアクセスしてアカウント作成")
    print("2. 新しいナレッジベースを作成")
    print("3. 以下のファイルをアップロード:")
    for f in files:
        print(f"   - {f}")
    print("4. チャットアプリを作成してナレッジベースを接続")
    print()
