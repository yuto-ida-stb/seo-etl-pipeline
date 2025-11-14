import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import os

# 設定
INPUT_FILE = './data/siteコロン結果（取得期間9.23〜10.9）.xlsx'
OUTPUT_DIR = './data/analysis'

def extract_r_hash_from_url(url):
    """URLからr_hashを抽出"""
    if pd.isna(url):
        return None

    # r_で始まる32文字のハッシュを抽出
    match = re.search(r'r_([a-f0-9]{32})', str(url))
    if match:
        return match.group(1)
    return None

def analyze_index_drops(input_file, output_dir):
    """
    インデックス落ちしたr_hashを特定する

    Args:
        input_file: 入力Excelファイルのパス
        output_dir: 出力ディレクトリ
    """
    print(f"Excelファイルを読み込み中: {input_file}")

    # Excelファイルを開く
    excel_file = pd.ExcelFile(input_file)
    sheet_names = excel_file.sheet_names

    print(f"シート数: {len(sheet_names)}")
    print(f"シート名: {sheet_names}")

    # 各シートのr_hashセットを格納
    sheet_data = {}

    for sheet_name in sheet_names:
        print(f"\nシート '{sheet_name}' を処理中...")

        # シート全体を読み込み
        df = pd.read_excel(input_file, sheet_name=sheet_name)
        print(f"  読み込み完了: {len(df):,}行")

        # URLからr_hashを抽出
        r_hashes = set()

        if 'url' in df.columns:
            df['r_hash'] = df['url'].apply(extract_r_hash_from_url)
            r_hashes.update(df['r_hash'].dropna().unique())
        elif 'keyword' in df.columns:
            # keywordカラムからも抽出を試みる
            df['r_hash'] = df['keyword'].apply(extract_r_hash_from_url)
            r_hashes.update(df['r_hash'].dropna().unique())

        print(f"  検出されたr_hash数: {len(r_hashes):,}")
        sheet_data[sheet_name] = r_hashes

    # インデックス落ちを分析
    print("\n" + "="*60)
    print("インデックス落ち分析")
    print("="*60)

    # シート名をソート（時系列順と仮定）
    sorted_sheets = sorted(sheet_names)

    # 前のシートと比較してインデックス落ちを検出
    results = []

    for i in range(1, len(sorted_sheets)):
        prev_sheet = sorted_sheets[i-1]
        current_sheet = sorted_sheets[i]

        prev_hashes = sheet_data[prev_sheet]
        current_hashes = sheet_data[current_sheet]

        # インデックス落ち = 前には存在したが今は存在しない
        dropped = prev_hashes - current_hashes

        # 新規追加 = 前には存在しなかったが今は存在する
        added = current_hashes - prev_hashes

        print(f"\n【{prev_sheet} → {current_sheet}】")
        print(f"  前のシート: {len(prev_hashes):,}件")
        print(f"  現在のシート: {len(current_hashes):,}件")
        print(f"  インデックス落ち: {len(dropped):,}件")
        print(f"  新規追加: {len(added):,}件")

        # インデックス落ちしたr_hashを記録
        for r_hash in dropped:
            results.append({
                'r_hash': r_hash,
                'url': f'https://jp.stanby.com/r_{r_hash}',
                'dropped_from': prev_sheet,
                'dropped_to': current_sheet,
                'status': 'dropped'
            })

    # 最終的なインデックス落ち（最初のシートには存在したが最後には存在しない）
    first_sheet = sorted_sheets[0]
    last_sheet = sorted_sheets[-1]

    first_hashes = sheet_data[first_sheet]
    last_hashes = sheet_data[last_sheet]

    final_dropped = first_hashes - last_hashes

    print(f"\n{'='*60}")
    print(f"【全期間でのインデックス落ち】")
    print(f"  {first_sheet}には存在したが{last_sheet}には存在しない")
    print(f"  インデックス落ち数: {len(final_dropped):,}件")
    print(f"{'='*60}")

    # 結果をDataFrameに変換
    if results:
        df_results = pd.DataFrame(results)

        # 出力ディレクトリを作成
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"index_drops_{timestamp}.csv")

        # CSVに保存
        df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ インデックス落ち一覧を保存: {output_file}")

        # サマリーレポートも作成
        summary_file = os.path.join(output_dir, f"index_drops_summary_{timestamp}.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=== インデックス落ち分析レポート ===\n\n")
            f.write(f"分析期間: {first_sheet} ～ {last_sheet}\n")
            f.write(f"総インデックス落ち数: {len(results):,}件\n\n")

            # 期間ごとの統計
            f.write("【期間別インデックス落ち数】\n")
            for i in range(1, len(sorted_sheets)):
                prev_sheet = sorted_sheets[i-1]
                current_sheet = sorted_sheets[i]
                dropped_count = len([r for r in results if r['dropped_from'] == prev_sheet and r['dropped_to'] == current_sheet])
                f.write(f"  {prev_sheet} → {current_sheet}: {dropped_count:,}件\n")

            f.write(f"\n【全期間でのインデックス落ち】\n")
            f.write(f"  {first_sheet}には存在したが{last_sheet}には存在しない: {len(final_dropped):,}件\n")

            # 最終的なインデックス落ち一覧も別ファイルに保存
            final_dropped_file = os.path.join(output_dir, f"index_drops_final_{timestamp}.csv")
            final_df = pd.DataFrame([
                {
                    'r_hash': r_hash,
                    'url': f'https://jp.stanby.com/r_{r_hash}',
                    'first_seen': first_sheet,
                    'last_seen': 'not in ' + last_sheet
                }
                for r_hash in final_dropped
            ])
            final_df.to_csv(final_dropped_file, index=False, encoding='utf-8-sig')

            f.write(f"\n詳細は以下のファイルを参照:\n")
            f.write(f"  - 全インデックス落ち: {output_file}\n")
            f.write(f"  - 最終インデックス落ち: {final_dropped_file}\n")

        print(f"✓ サマリーレポートを保存: {summary_file}")
        print(f"✓ 最終インデックス落ち一覧を保存: {final_dropped_file}")
    else:
        print("\nインデックス落ちは検出されませんでした")

    return results

if __name__ == "__main__":
    try:
        results = analyze_index_drops(INPUT_FILE, OUTPUT_DIR)
        print(f"\n✓ インデックス落ち分析が完了しました")
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
