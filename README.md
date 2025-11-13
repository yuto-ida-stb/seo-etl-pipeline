# SEO Data Analysis Pipeline

週次のSEOデータを自動的にダウンロード、分析し、Google Driveにアップロードするパイプライン

## 機能

- Google Driveからの週次CSVファイルの自動ダウンロード
- 複数ファイルのマージと不要カラムの削除
- 週次の順位・距離の差分と変化率の計算（3ヶ月分）
- 分析結果のレポート生成
- Google Driveへの自動アップロード
- GitHub Actionsによる週次自動実行

## ディレクトリ構造

```
seo_data/
├── .github/
│   └── workflows/
│       └── weekly_seo_analysis.yml  # GitHub Actions ワークフロー
├── data/
│   ├── raw/                         # ダウンロードした生データ
│   ├── processed/                   # マージ済みデータ
│   └── analysis/                    # 分析結果
├── merge_data.py                    # データマージスクリプト
├── analyze_trends.py                # 分析スクリプト
├── download_from_drive.py           # Google Drive ダウンロード
├── upload_to_drive.py               # Google Drive アップロード
├── requirements.txt                 # Python依存関係
└── README.md
```

## セットアップ

### 1. Python環境の準備

```bash
pip install -r requirements.txt
```

### 2. Google Drive API認証設定

#### ローカル実行の場合:
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Drive APIを有効化
3. サービスアカウントを作成し、JSONキーをダウンロード
4. ダウンロードしたJSONファイルを `credentials.json` として保存
5. サービスアカウントに共有フォルダへのアクセス権を付与

#### GitHub Actionsの場合:
1. 上記の手順でサービスアカウントJSONキーを取得
2. GitHubリポジトリの Settings > Secrets and variables > Actions に移動
3. 新しいシークレット `GCP_SA_KEY` を作成し、JSONキーの内容を貼り付け

### 3. フォルダIDの設定

`download_from_drive.py` と `upload_to_drive.py` の `FOLDER_ID` を更新してください:

```python
FOLDER_ID = '1sSy8mDQgtkmyODigpIiWiNh6hOJxG1Pt'
```

## 使い方

### ローカルで実行

```bash
# 1. Google Driveからデータをダウンロード
python download_from_drive.py

# 2. CSVファイルをマージ
python merge_data.py

# 3. トレンド分析を実行
python analyze_trends.py

# 4. 結果をGoogle Driveにアップロード
python upload_to_drive.py
```

### GitHub Actionsで自動実行

- **自動実行**: 毎週月曜日午前9時（JST）に自動実行されます
- **手動実行**: GitHubリポジトリの Actions タブから手動でトリガー可能

## データ形式

### 入力CSVファイルの期待フォーマット

```csv
keyword,url,rank,distance,date
"キーワード1","https://example.com/page1",5,1.2,"2024-01-01"
"キーワード2","https://example.com/page2",10,2.5,"2024-01-01"
```

必要なカラム:
- `keyword`: 検索キーワード
- `url`: ページURL
- `rank`: 検索順位
- `distance`: 距離スコア
- `date`: 日付（自動付与も可能）

### 出力ファイル

1. **マージデータ**: `data/processed/merged_data_YYYYMMDD_HHMMSS.csv`
2. **分析結果**: `data/analysis/weekly_analysis_YYYYMMDD_HHMMSS.csv`
3. **示唆レポート**: `data/analysis/insights_report_YYYYMMDD_HHMMSS.txt`

## カスタマイズ

### 保持するカラムの変更

`merge_data.py` の `columns_to_keep` を編集:

```python
columns_to_keep = [
    'keyword',
    'url',
    'rank',
    'distance',
    'date',
    # 追加のカラム
]
```

### 分析期間の変更

`analyze_trends.py` の `weeks` パラメータを変更:

```python
# 6ヶ月分のデータを分析する場合
analysis_df = calculate_weekly_changes(df, weeks=24)
```

## トラブルシューティング

### 認証エラー
- `credentials.json` が正しく配置されているか確認
- サービスアカウントに共有フォルダへのアクセス権があるか確認

### データが見つからない
- Google DriveのフォルダIDが正しいか確認
- CSVファイルが共有フォルダに存在するか確認

### GitHub Actions失敗
- シークレット `GCP_SA_KEY` が正しく設定されているか確認
- ワークフローログでエラー詳細を確認

## ライセンス

MIT License
