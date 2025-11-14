import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import os
import glob

# 設定
SEARCH_CONSOLE_DIR = './data/search_console'
OUTPUT_DIR = './data/analysis'
MONTHS_TO_ANALYZE = 3  # 直近3ヶ月

def analyze_search_console_trends_simple(input_dir, output_dir):
    """
    Search Consoleデータから前週→今週の順位変化を分析（シンプル版）

    Args:
        input_dir: Search Consoleデータのディレクトリ
        output_dir: 出力ディレクトリ
    """
    print("="*80)
    print("Search Console 順位推移分析（前週→今週）")
    print("="*80)

    # 最新のファイルを取得
    csv_files = sorted(glob.glob(os.path.join(input_dir, 'search_console_weekly_*.csv')))

    if not csv_files:
        print(f"エラー: {input_dir}にSearch Consoleデータが見つかりません")
        return

    latest_file = csv_files[-1]
    print(f"\n使用するファイル: {latest_file}")

    # データを読み込み
    df = pd.read_csv(latest_file)
    print(f"データ読み込み完了: {len(df):,}行")

    # CSVにquery_keyword, query_location, categoryがない場合は空の列を追加
    if 'query_keyword' not in df.columns:
        df['query_keyword'] = ''
    if 'query_location' not in df.columns:
        df['query_location'] = ''
    if 'category' not in df.columns:
        df['category'] = ''

    # 順位データをfloat型に変換
    df['avg_position'] = pd.to_numeric(df['avg_position'], errors='coerce')
    df['prev_position'] = pd.to_numeric(df['prev_position'], errors='coerce')
    df['position_diff'] = pd.to_numeric(df['position_diff'], errors='coerce')

    # NaNを除外
    df = df.dropna(subset=['avg_position', 'prev_position'])

    print(f"順位データあり: {len(df):,}行")

    # 4つの傾向を分類
    print("\n" + "="*80)
    print("傾向分析")
    print("="*80)

    # 1. 順位が10位以内から11位以上に下落したもの
    dropped_from_top10 = df[
        (df['prev_position'] <= 10) &
        (df['avg_position'] > 10)
    ].copy()
    dropped_from_top10 = dropped_from_top10.sort_values('position_diff', ascending=False)

    # 2. 順位が11位以上から10位以下に上昇したもの
    jumped_to_top10 = df[
        (df['prev_position'] > 10) &
        (df['avg_position'] <= 10)
    ].copy()
    jumped_to_top10 = jumped_to_top10.sort_values('position_diff')

    # 3. 順位が大きく下降しているもの（position_diff > 0 = 悪化）
    gradually_declining = df[
        df['position_diff'] >= 5  # 5位以上悪化
    ].copy()
    gradually_declining = gradually_declining.sort_values('position_diff', ascending=False)

    # 4. 順位が大きく上昇しているもの（position_diff < 0 = 改善）
    gradually_improving = df[
        df['position_diff'] <= -5  # 5位以上改善
    ].copy()
    gradually_improving = gradually_improving.sort_values('position_diff')

    print(f"\n【1. 順位が10位以内から11位以上に下落】: {len(dropped_from_top10)}件")
    print(f"【2. 順位が11位以上から10位以下に上昇】: {len(jumped_to_top10)}件")
    print(f"【3. 順位が大きく下降（5位以上悪化）】: {len(gradually_declining)}件")
    print(f"【4. 順位が大きく上昇（5位以上改善）】: {len(gradually_improving)}件")

    # レポート生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    report_file = os.path.join(output_dir, f"search_console_trends_{timestamp}.txt")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Search Console 順位推移分析レポート（前週→今週）\n")
        f.write("="*80 + "\n\n")
        f.write(f"分析日: {df['week_start'].iloc[0] if len(df) > 0 else 'N/A'}\n")
        f.write(f"分析データ数: {len(df):,}件\n\n")

        # 1. 10位以内から11位以上に下落
        f.write("="*80 + "\n")
        f.write("【1. 順位が10位以内から11位以上に下落したもの】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(dropped_from_top10)}件\n\n")

        if len(dropped_from_top10) > 0:
            f.write("Top 30:\n")
            for i, (idx, row) in enumerate(dropped_from_top10.head(30).iterrows(), 1):
                f.write(f"\n{i}. query_hash: {row['query_hash']}\n")
                if row['query_keyword']:
                    f.write(f"   query_keyword: {row['query_keyword']}\n")
                if row['query_location']:
                    f.write(f"   query_location: {row['query_location']}\n")
                if row['category']:
                    f.write(f"   category: {row['category']}\n")
                f.write(f"   前週順位: {row['prev_position']:.1f} → 今週順位: {row['avg_position']:.1f}\n")
                f.write(f"   変化: {row['position_diff']:+.1f}\n")
                f.write(f"   インプレッション: {row['total_impressions']:,.0f}\n")
                f.write(f"   クリック: {row['total_clicks']:,.0f}\n")

        # 2. 11位以上から10位以下に上昇
        f.write("\n" + "="*80 + "\n")
        f.write("【2. 順位が11位以上から10位以下に上昇したもの】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(jumped_to_top10)}件\n\n")

        if len(jumped_to_top10) > 0:
            f.write("Top 30:\n")
            for i, (idx, row) in enumerate(jumped_to_top10.head(30).iterrows(), 1):
                f.write(f"\n{i}. query_hash: {row['query_hash']}\n")
                if row['query_keyword']:
                    f.write(f"   query_keyword: {row['query_keyword']}\n")
                if row['query_location']:
                    f.write(f"   query_location: {row['query_location']}\n")
                if row['category']:
                    f.write(f"   category: {row['category']}\n")
                f.write(f"   前週順位: {row['prev_position']:.1f} → 今週順位: {row['avg_position']:.1f}\n")
                f.write(f"   変化: {row['position_diff']:+.1f}\n")
                f.write(f"   インプレッション: {row['total_impressions']:,.0f}\n")
                f.write(f"   クリック: {row['total_clicks']:,.0f}\n")

        # 3. 大きく下降
        f.write("\n" + "="*80 + "\n")
        f.write("【3. 順位が大きく下降しているもの（5位以上悪化）】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(gradually_declining)}件\n\n")

        if len(gradually_declining) > 0:
            f.write("Top 30:\n")
            for i, (idx, row) in enumerate(gradually_declining.head(30).iterrows(), 1):
                f.write(f"\n{i}. query_hash: {row['query_hash']}\n")
                if row['query_keyword']:
                    f.write(f"   query_keyword: {row['query_keyword']}\n")
                if row['query_location']:
                    f.write(f"   query_location: {row['query_location']}\n")
                if row['category']:
                    f.write(f"   category: {row['category']}\n")
                f.write(f"   前週順位: {row['prev_position']:.1f} → 今週順位: {row['avg_position']:.1f}\n")
                f.write(f"   変化: {row['position_diff']:+.1f}\n")
                f.write(f"   インプレッション: {row['total_impressions']:,.0f}\n")
                f.write(f"   クリック: {row['total_clicks']:,.0f}\n")

        # 4. 大きく上昇
        f.write("\n" + "="*80 + "\n")
        f.write("【4. 順位が大きく上昇しているもの（5位以上改善）】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(gradually_improving)}件\n\n")

        if len(gradually_improving) > 0:
            f.write("Top 30:\n")
            for i, (idx, row) in enumerate(gradually_improving.head(30).iterrows(), 1):
                f.write(f"\n{i}. query_hash: {row['query_hash']}\n")
                if row['query_keyword']:
                    f.write(f"   query_keyword: {row['query_keyword']}\n")
                if row['query_location']:
                    f.write(f"   query_location: {row['query_location']}\n")
                if row['category']:
                    f.write(f"   category: {row['category']}\n")
                f.write(f"   前週順位: {row['prev_position']:.1f} → 今週順位: {row['avg_position']:.1f}\n")
                f.write(f"   変化: {row['position_diff']:+.1f}\n")
                f.write(f"   インプレッション: {row['total_impressions']:,.0f}\n")
                f.write(f"   クリック: {row['total_clicks']:,.0f}\n")

        # カテゴリ別・キーワード別の傾向分析
        f.write("\n" + "="*80 + "\n")
        f.write("【総合傾向分析】\n")
        f.write("="*80 + "\n\n")

        # カテゴリ別の集計
        all_dfs = [dropped_from_top10, jumped_to_top10, gradually_declining, gradually_improving]

        category_stats = {}
        for df_temp in all_dfs:
            for cat in df_temp['category'].unique():
                if pd.notna(cat) and cat not in category_stats:
                    category_stats[cat] = {'dropped': 0, 'jumped': 0, 'declining': 0, 'improving': 0}

        for cat in dropped_from_top10['category'].unique():
            if pd.notna(cat):
                category_stats[cat]['dropped'] = len(dropped_from_top10[dropped_from_top10['category'] == cat])
        for cat in jumped_to_top10['category'].unique():
            if pd.notna(cat):
                category_stats[cat]['jumped'] = len(jumped_to_top10[jumped_to_top10['category'] == cat])
        for cat in gradually_declining['category'].unique():
            if pd.notna(cat):
                category_stats[cat]['declining'] = len(gradually_declining[gradually_declining['category'] == cat])
        for cat in gradually_improving['category'].unique():
            if pd.notna(cat):
                category_stats[cat]['improving'] = len(gradually_improving[gradually_improving['category'] == cat])

        if category_stats:
            f.write("カテゴリ別集計:\n")
            sorted_cats = sorted(category_stats.items(), key=lambda x: sum(x[1].values()), reverse=True)
            for cat, stats in sorted_cats[:30]:
                total = sum(stats.values())
                if total > 0:
                    f.write(f"\n  カテゴリ: {cat}\n")
                    f.write(f"    10位内→11位外: {stats['dropped']}件\n")
                    f.write(f"    11位外→10位内: {stats['jumped']}件\n")
                    f.write(f"    大きく下降: {stats['declining']}件\n")
                    f.write(f"    大きく上昇: {stats['improving']}件\n")
                    f.write(f"    合計: {total}件\n")

    print(f"\n✓ レポートを保存しました: {report_file}")

    # CSV出力も作成
    csv_data = []

    for idx, row in dropped_from_top10.iterrows():
        csv_data.append({
            'trend_type': '10位内→11位外',
            'query_keyword': row['query_keyword'],
            'query_location': row['query_location'],
            'query_hash': row['query_hash'],
            'category': row['category'],
            'prev_position': row['prev_position'],
            'avg_position': row['avg_position'],
            'position_diff': row['position_diff']
        })

    for idx, row in jumped_to_top10.iterrows():
        csv_data.append({
            'trend_type': '11位外→10位内',
            'query_keyword': row['query_keyword'],
            'query_location': row['query_location'],
            'query_hash': row['query_hash'],
            'category': row['category'],
            'prev_position': row['prev_position'],
            'avg_position': row['avg_position'],
            'position_diff': row['position_diff']
        })

    for idx, row in gradually_declining.iterrows():
        csv_data.append({
            'trend_type': '大きく下降',
            'query_keyword': row['query_keyword'],
            'query_location': row['query_location'],
            'query_hash': row['query_hash'],
            'category': row['category'],
            'prev_position': row['prev_position'],
            'avg_position': row['avg_position'],
            'position_diff': row['position_diff']
        })

    for idx, row in gradually_improving.iterrows():
        csv_data.append({
            'trend_type': '大きく上昇',
            'query_keyword': row['query_keyword'],
            'query_location': row['query_location'],
            'query_hash': row['query_hash'],
            'category': row['category'],
            'prev_position': row['prev_position'],
            'avg_position': row['avg_position'],
            'position_diff': row['position_diff']
        })

    if csv_data:
        df_output = pd.DataFrame(csv_data)
        csv_file = os.path.join(output_dir, f"search_console_trends_{timestamp}.csv")
        df_output.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✓ CSV出力を保存しました: {csv_file}")

    return report_file

def analyze_search_console_trends(input_dir, output_dir, months=3):
    """
    Search Consoleデータから順位推移の傾向を分析

    Args:
        input_dir: Search Consoleデータのディレクトリ
        output_dir: 出力ディレクトリ
        months: 分析対象の月数（デフォルト3ヶ月）
    """
    print("="*80)
    print("Search Console 順位推移分析")
    print("="*80)

    # 複数の週次ファイルを取得
    csv_files = sorted(glob.glob(os.path.join(input_dir, 'search_console_weekly_*.csv')))

    if not csv_files:
        print(f"エラー: {input_dir}にSearch Consoleデータが見つかりません")
        return

    # 直近N週分のファイルを読み込み
    weeks_to_analyze = months * 4  # 約3ヶ月 = 12週
    files_to_use = csv_files[-min(weeks_to_analyze, len(csv_files)):]

    print(f"\n使用するファイル数: {len(files_to_use)}件")
    for f in files_to_use:
        print(f"  - {os.path.basename(f)}")

    # 複数ファイルを結合
    df_list = []
    mapping_df = None

    # まず最新のファイルからマッピング情報を取得
    for file in reversed(files_to_use):
        df_temp = pd.read_csv(file)

        # r_hashをquery_hashにリネーム
        if 'r_hash' in df_temp.columns and 'query_hash' not in df_temp.columns:
            df_temp = df_temp.rename(columns={'r_hash': 'query_hash'})

        # query_keyword, query_location, categoryがあるファイルからマッピングを作成
        if 'query_keyword' in df_temp.columns and 'query_location' in df_temp.columns and 'category' in df_temp.columns:
            mapping_df = df_temp[['query_hash', 'query_keyword', 'query_location', 'category']].drop_duplicates(subset=['query_hash'])
            print(f"\nマッピング情報を取得: {os.path.basename(file)} ({len(mapping_df):,}件)")
            break

    # 各ファイルを読み込み
    for file in files_to_use:
        df_temp = pd.read_csv(file)
        df_temp['week_start'] = pd.to_datetime(df_temp['week_start'])

        # r_hashをquery_hashにリネーム（古いファイル対応）
        if 'r_hash' in df_temp.columns and 'query_hash' not in df_temp.columns:
            df_temp = df_temp.rename(columns={'r_hash': 'query_hash'})

        # CSVにquery_keyword, query_location, categoryがない場合
        if 'query_keyword' not in df_temp.columns or 'query_location' not in df_temp.columns or 'category' not in df_temp.columns:
            if mapping_df is not None:
                # マッピング情報があれば結合
                df_temp = df_temp.merge(
                    mapping_df,
                    on='query_hash',
                    how='left'
                )
            else:
                # マッピング情報がない場合は空の列を追加
                if 'query_keyword' not in df_temp.columns:
                    df_temp['query_keyword'] = ''
                if 'query_location' not in df_temp.columns:
                    df_temp['query_location'] = ''
                if 'category' not in df_temp.columns:
                    df_temp['category'] = ''

        df_list.append(df_temp)

    df = pd.concat(df_list, ignore_index=True)
    print(f"\nデータ読み込み完了: {len(df):,}行")

    # 重複を除去（query_hash + week_startで一意）
    df = df.drop_duplicates(subset=['query_hash', 'week_start'], keep='last')
    print(f"重複除去後: {len(df):,}行")

    # マッピング情報の統計
    has_keyword = df['query_keyword'].notna() & (df['query_keyword'] != '')
    print(f"キーワード情報あり: {has_keyword.sum():,}行 ({has_keyword.sum()/len(df)*100:.1f}%)")

    df_recent = df.copy()

    print(f"\n分析期間: {df_recent['week_start'].min().strftime('%Y-%m-%d')} ～ {df_recent['week_start'].max().strftime('%Y-%m-%d')}")
    print(f"分析データ数: {len(df_recent):,}行")
    print(f"週数: {df_recent['week_start'].nunique()}週")

    # 順位データをfloat型に変換
    df_recent['avg_position'] = pd.to_numeric(df_recent['avg_position'], errors='coerce')
    df_recent['prev_position'] = pd.to_numeric(df_recent['prev_position'], errors='coerce')

    # クエリごとに時系列データを作成
    query_trends = {}

    for (query_hash, query_keyword, query_location, category), group in df_recent.groupby(['query_hash', 'query_keyword', 'query_location', 'category']):
        group = group.sort_values('week_start')

        # 順位の推移を記録
        positions = group['avg_position'].tolist()
        weeks = group['week_start'].tolist()

        # データポイントが2つ以上ある場合のみ分析
        if len(positions) >= 2:
            query_trends[query_hash] = {
                'query_keyword': query_keyword,
                'query_location': query_location,
                'query_hash': query_hash,
                'category': category,
                'positions': positions,
                'weeks': weeks,
                'first_position': positions[0],
                'last_position': positions[-1],
                'data_points': len(positions)
            }

    print(f"\n分析対象クエリ数: {len(query_trends):,}件")

    # 4つの傾向を分類
    print("\n" + "="*80)
    print("傾向分析")
    print("="*80)

    # 1. 順位が10位以内から11位以上に下落したもの
    dropped_from_top10 = []

    # 2. 順位が11位以上から10位以下に上昇したもの
    jumped_to_top10 = []

    # 3. 順位が徐々に下降しているもの
    gradually_declining = []

    # 4. 順位が徐々に上昇しているもの
    gradually_improving = []

    for query_hash, data in query_trends.items():
        positions = data['positions']
        first_pos = data['first_position']
        last_pos = data['last_position']

        # NaNをスキップ
        if pd.isna(first_pos) or pd.isna(last_pos):
            continue

        # 1. 10位以内から11位以上に下落
        if first_pos <= 10 and last_pos > 10:
            data['position_change'] = last_pos - first_pos
            dropped_from_top10.append(data)

        # 2. 11位以上から10位以下に上昇
        elif first_pos > 10 and last_pos <= 10:
            data['position_change'] = last_pos - first_pos
            jumped_to_top10.append(data)

        # 3 & 4: 徐々に変化しているもの（線形回帰で判定）
        # NaNを除外
        valid_positions = [p for p in positions if not pd.isna(p)]

        if len(valid_positions) >= 3:
            x = np.arange(len(valid_positions))
            y = np.array(valid_positions)

            # 線形回帰で傾きを計算
            slope = np.polyfit(x, y, 1)[0]

            # 単調性をチェック
            is_monotonic_up = all(valid_positions[i] >= valid_positions[i-1] for i in range(1, len(valid_positions)))
            is_monotonic_down = all(valid_positions[i] <= valid_positions[i-1] for i in range(1, len(valid_positions)))

            data['slope'] = slope

            # 3. 徐々に下降（順位が悪化）
            if slope > 0.5:  # 正の傾き = 順位悪化
                data['position_change'] = last_pos - first_pos
                gradually_declining.append(data)

            # 4. 徐々に上昇（順位が改善）
            elif slope < -0.5:  # 負の傾き = 順位改善
                data['position_change'] = last_pos - first_pos
                gradually_improving.append(data)

    # 結果をソート
    dropped_from_top10.sort(key=lambda x: x['position_change'], reverse=True)
    jumped_to_top10.sort(key=lambda x: x['position_change'])
    gradually_declining.sort(key=lambda x: x['slope'], reverse=True)
    gradually_improving.sort(key=lambda x: x['slope'])

    print(f"\n【1. 順位が10位以内から11位以上に下落】: {len(dropped_from_top10)}件")
    print(f"【2. 順位が11位以上から10位以下に上昇】: {len(jumped_to_top10)}件")
    print(f"【3. 順位が徐々に下降しているもの】: {len(gradually_declining)}件")
    print(f"【4. 順位が徐々に上昇しているもの】: {len(gradually_improving)}件")

    # レポート生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    report_file = os.path.join(output_dir, f"search_console_trends_{timestamp}.txt")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Search Console 順位推移分析レポート\n")
        f.write("="*80 + "\n\n")
        f.write(f"分析期間: {df_recent['week_start'].min().strftime('%Y-%m-%d')} ～ {df_recent['week_start'].max().strftime('%Y-%m-%d')}\n")
        f.write(f"週数: {df_recent['week_start'].nunique()}週\n")
        f.write(f"分析対象クエリ数: {len(query_trends):,}件\n\n")

        # 1. 10位以内から11位以上に下落
        f.write("="*80 + "\n")
        f.write("【1. 順位が10位以内から11位以上に下落したもの】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(dropped_from_top10)}件\n\n")

        if dropped_from_top10:
            f.write("Top 30:\n")
            for i, item in enumerate(dropped_from_top10[:30], 1):
                f.write(f"\n{i}. query_hash: {item['query_hash']}\n")
                if item['query_keyword']:
                    f.write(f"   query_keyword: {item['query_keyword']}\n")
                if item['query_location']:
                    f.write(f"   query_location: {item['query_location']}\n")
                if item['category']:
                    f.write(f"   category: {item['category']}\n")
                f.write(f"   初期順位: {item['first_position']:.1f} → 最新順位: {item['last_position']:.1f}\n")
                f.write(f"   変化: {item['position_change']:+.1f}\n")
                f.write(f"   データポイント: {item['data_points']}週\n")

        # 2. 11位以上から10位以下に上昇
        f.write("\n" + "="*80 + "\n")
        f.write("【2. 順位が11位以上から10位以下に上昇したもの】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(jumped_to_top10)}件\n\n")

        if jumped_to_top10:
            f.write("Top 30:\n")
            for i, item in enumerate(jumped_to_top10[:30], 1):
                f.write(f"\n{i}. query_hash: {item['query_hash']}\n")
                if item['query_keyword']:
                    f.write(f"   query_keyword: {item['query_keyword']}\n")
                if item['query_location']:
                    f.write(f"   query_location: {item['query_location']}\n")
                if item['category']:
                    f.write(f"   category: {item['category']}\n")
                f.write(f"   初期順位: {item['first_position']:.1f} → 最新順位: {item['last_position']:.1f}\n")
                f.write(f"   変化: {item['position_change']:+.1f}\n")
                f.write(f"   データポイント: {item['data_points']}週\n")

        # 3. 徐々に下降
        f.write("\n" + "="*80 + "\n")
        f.write("【3. 順位が徐々に下降しているもの】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(gradually_declining)}件\n\n")

        if gradually_declining:
            f.write("Top 30:\n")
            for i, item in enumerate(gradually_declining[:30], 1):
                f.write(f"\n{i}. query_hash: {item['query_hash']}\n")
                if item['query_keyword']:
                    f.write(f"   query_keyword: {item['query_keyword']}\n")
                if item['query_location']:
                    f.write(f"   query_location: {item['query_location']}\n")
                if item['category']:
                    f.write(f"   category: {item['category']}\n")
                f.write(f"   初期順位: {item['first_position']:.1f} → 最新順位: {item['last_position']:.1f}\n")
                f.write(f"   変化: {item['position_change']:+.1f} (傾き: {item['slope']:.2f})\n")
                f.write(f"   データポイント: {item['data_points']}週\n")

        # 4. 徐々に上昇
        f.write("\n" + "="*80 + "\n")
        f.write("【4. 順位が徐々に上昇しているもの】\n")
        f.write("="*80 + "\n")
        f.write(f"該当件数: {len(gradually_improving)}件\n\n")

        if gradually_improving:
            f.write("Top 30:\n")
            for i, item in enumerate(gradually_improving[:30], 1):
                f.write(f"\n{i}. query_hash: {item['query_hash']}\n")
                if item['query_keyword']:
                    f.write(f"   query_keyword: {item['query_keyword']}\n")
                if item['query_location']:
                    f.write(f"   query_location: {item['query_location']}\n")
                if item['category']:
                    f.write(f"   category: {item['category']}\n")
                f.write(f"   初期順位: {item['first_position']:.1f} → 最新順位: {item['last_position']:.1f}\n")
                f.write(f"   変化: {item['position_change']:+.1f} (傾き: {item['slope']:.2f})\n")
                f.write(f"   データポイント: {item['data_points']}週\n")

        # カテゴリ別・キーワード別の傾向分析
        f.write("\n" + "="*80 + "\n")
        f.write("【総合傾向分析】\n")
        f.write("="*80 + "\n\n")

        # カテゴリ別の集計
        all_items = dropped_from_top10 + jumped_to_top10 + gradually_declining + gradually_improving

        if all_items:
            category_stats = {}
            for item in all_items:
                cat = item['category']
                if cat not in category_stats:
                    category_stats[cat] = {'dropped': 0, 'jumped': 0, 'declining': 0, 'improving': 0}

            for item in dropped_from_top10:
                category_stats[item['category']]['dropped'] += 1
            for item in jumped_to_top10:
                category_stats[item['category']]['jumped'] += 1
            for item in gradually_declining:
                category_stats[item['category']]['declining'] += 1
            for item in gradually_improving:
                category_stats[item['category']]['improving'] += 1

            f.write("カテゴリ別集計:\n")
            for cat, stats in sorted(category_stats.items(), key=lambda x: sum(x[1].values()), reverse=True)[:30]:
                total = sum(stats.values())
                if total > 0:
                    cat_display = cat if (cat and str(cat) != 'nan') else '(カテゴリなし)'
                    f.write(f"\n  カテゴリ: {cat_display}\n")
                    f.write(f"    10位内→11位外: {stats['dropped']}件\n")
                    f.write(f"    11位外→10位内: {stats['jumped']}件\n")
                    f.write(f"    徐々に下降: {stats['declining']}件\n")
                    f.write(f"    徐々に上昇: {stats['improving']}件\n")
                    f.write(f"    合計: {total}件\n")

    print(f"\n✓ レポートを保存しました: {report_file}")

    # CSV出力も作成
    csv_data = []

    for item in dropped_from_top10:
        csv_data.append({
            'trend_type': '10位内→11位外',
            'query_keyword': item['query_keyword'],
            'query_location': item['query_location'],
            'query_hash': item['query_hash'],
            'category': item['category'],
            'first_position': item['first_position'],
            'last_position': item['last_position'],
            'position_change': item['position_change'],
            'slope': None
        })

    for item in jumped_to_top10:
        csv_data.append({
            'trend_type': '11位外→10位内',
            'query_keyword': item['query_keyword'],
            'query_location': item['query_location'],
            'query_hash': item['query_hash'],
            'category': item['category'],
            'first_position': item['first_position'],
            'last_position': item['last_position'],
            'position_change': item['position_change'],
            'slope': None
        })

    for item in gradually_declining:
        csv_data.append({
            'trend_type': '徐々に下降',
            'query_keyword': item['query_keyword'],
            'query_location': item['query_location'],
            'query_hash': item['query_hash'],
            'category': item['category'],
            'first_position': item['first_position'],
            'last_position': item['last_position'],
            'position_change': item['position_change'],
            'slope': item['slope']
        })

    for item in gradually_improving:
        csv_data.append({
            'trend_type': '徐々に上昇',
            'query_keyword': item['query_keyword'],
            'query_location': item['query_location'],
            'query_hash': item['query_hash'],
            'category': item['category'],
            'first_position': item['first_position'],
            'last_position': item['last_position'],
            'position_change': item['position_change'],
            'slope': item['slope']
        })

    if csv_data:
        df_output = pd.DataFrame(csv_data)
        csv_file = os.path.join(output_dir, f"search_console_trends_{timestamp}.csv")
        df_output.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✓ CSV出力を保存しました: {csv_file}")

    return report_file

if __name__ == "__main__":
    try:
        # 複数週のデータを使った時系列分析を実行
        report_file = analyze_search_console_trends(SEARCH_CONSOLE_DIR, OUTPUT_DIR, MONTHS_TO_ANALYZE)
        print(f"\n✓ Search Console順位推移分析が完了しました")
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
