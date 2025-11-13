import pandas as pd
import glob
import os
from pathlib import Path
from datetime import datetime

def merge_weekly_data(input_folder: str, output_folder: str, columns_to_keep: list = None):
    """
    週次のCSVファイルをマージして不要なカラムを削除する

    Args:
        input_folder: 入力CSVファイルが格納されているフォルダ
        output_folder: 出力先フォルダ
        columns_to_keep: 残すカラムのリスト（Noneの場合は全カラム保持）
    """
    # 入力フォルダ内の全CSVファイルを取得
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

    if not csv_files:
        print(f"Error: {input_folder}にCSVファイルが見つかりません")
        return None

    print(f"{len(csv_files)}個のCSVファイルを検出しました")

    # 全てのCSVファイルを読み込んでマージ
    dataframes = []
    for file in sorted(csv_files):
        print(f"読み込み中: {file}")
        df = pd.read_csv(file)

        # ファイル名から日付を抽出（ファイル名に日付が含まれていると仮定）
        filename = os.path.basename(file)
        # 日付カラムがない場合は追加
        if 'date' not in df.columns and 'Date' not in df.columns:
            df['date'] = filename.replace('.csv', '')

        dataframes.append(df)

    # データフレームを結合
    merged_df = pd.concat(dataframes, ignore_index=True)
    print(f"マージ完了: {len(merged_df)}行のデータ")

    # 指定されたカラムのみ保持
    if columns_to_keep:
        available_columns = [col for col in columns_to_keep if col in merged_df.columns]
        missing_columns = [col for col in columns_to_keep if col not in merged_df.columns]

        if missing_columns:
            print(f"警告: 以下のカラムが見つかりません: {missing_columns}")

        merged_df = merged_df[available_columns]
        print(f"カラムをフィルタリング: {len(available_columns)}カラム保持")

    # 出力フォルダを作成
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # 出力ファイル名を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_folder, f"merged_data_{timestamp}.csv")

    # CSVファイルとして保存
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"保存完了: {output_file}")

    return merged_df

if __name__ == "__main__":
    # 使用例
    # 必要に応じて保持するカラムを指定
    columns_to_keep = [
        'keyword',
        'url',
        'rank',
        'distance',
        'date',
        # 必要なカラムを追加
    ]

    input_folder = "./data/raw"
    output_folder = "./data/processed"

    merge_weekly_data(input_folder, output_folder, columns_to_keep)
