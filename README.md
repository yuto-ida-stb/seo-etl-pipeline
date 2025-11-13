# SEO ETL Pipeline

SEOデータの抽出・変換・ロード（ETL）を自動化し、Difyチャットボットと連携するパイプライン

> **注意**: 現在は日次データで動作確認中です。Google Driveに週次平均データ（3ヶ月分）が配置されると、自動的に週次分析に切り替わります。

## 機能

### SEOランク分析
- Google Driveからのデータファイル自動ダウンロード
- 複数ファイルのマージと不要カラムの削除
- 期間比較による順位・距離の差分と変化率の計算
- 分析結果のレポート生成（改善/下落Top 10など）

### Search Console分析（r_hash別）
- BigQueryからr_hash別の週次データ取得
- インプレッション、CTR、順位の前週比計算
- 変化率・差分の集計

### Dify連携（チャットボット）
- 分析結果をMarkdown形式でエクスポート
- Dify APIによるナレッジベース自動更新（オプション）
- データ辞書・メタデータの自動生成

### 共通機能
- Google Driveへの結果自動アップロード（フォルダ別管理）
- 手動実行ワークフロー（OAuth認証）
- セキュリティ対策（認証情報の暗号化、Path Traversal対策）

## Google Driveフォルダ構成

```
SEO Data/
├── 00_raw_data/                    # 週次平均データ（手動アップロード用）
├── 01_seo_rank_analysis/           # SEOランク・距離の分析結果
│   ├── weekly_analysis_YYYYMMDD.csv
│   └── insights_report_YYYYMMDD.txt
└── 02_search_console_analysis/     # Search Console(r_hash)の分析結果
    └── search_console_weekly_YYYYMMDD.csv
```

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

### 2. Difyチャットボット設定（オプション）

#### 手動アップロード（簡単）

1. [Dify](https://dify.ai)でアカウント作成
2. ナレッジベースを作成（例: `SEO分析データ`）
3. 分析実行後、以下をアップロード：
   ```bash
   ./run_analysis.sh  # 分析実行
   # data/dify_export/*.md をDifyナレッジベースに手動アップロード
   ```

#### API自動更新（高度）

1. Difyでナレッジベース作成後、API Keyを取得
2. `.env`ファイルを作成：
   ```bash
   cp .env.example .env
   # .env を編集してAPI KeyとDataset IDを設定
   ```
3. 自動更新スクリプトを実行：
   ```bash
   python upload_to_dify_api.py
   ```

### 3. Google Drive API認証設定

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

### 4. フォルダIDの設定

`download_from_drive.py` と `upload_to_drive.py` の `FOLDER_ID` を更新してください:

```python
FOLDER_ID = '1sSy8mDQgtkmyODigpIiWiNh6hOJxG1Pt'
```

## 使い方

### 簡単実行（推奨）

```bash
# 全ての処理を一括実行（7ステップ）
./run_analysis.sh
# 1. Google Driveからダウンロード
# 2. CSVマージ
# 3. SEOランク分析
# 4. Search Console分析
# 5. Dify用データエクスポート
# 6. Google Driveにアップロード
# 7. Gitコミット

# 完了したらGitHubにプッシュ
git push origin main
```

### 個別実行

```bash
# 1. Google Driveからデータをダウンロード
python download_from_drive_oauth.py

# 2. CSVファイルをマージ
python merge_data.py

# 3. トレンド分析を実行
python analyze_trends.py

# 4. 結果をコミット
git add data/analysis/*
git commit -m "Add SEO analysis results"
git push origin main
```

### 運用フロー

1. **定期実行**: 手動で `./run_analysis.sh` を実行
   - 現在: 新しいデータが追加されたら実行
   - 将来: 週次平均データ配置後は毎週実行

2. **結果確認**:
   - ローカル: `data/analysis/` フォルダ内のレポート
   - Google Drive: [analysis_resultsフォルダ](https://drive.google.com/drive/folders/1EF8arydCbvLLih_TALvEE2LKOlH2XQEA)

3. **GitHub**: `git push origin main` で結果を共有・バックアップ

## データ形式

### 入力CSVファイルの期待フォーマット

```csv
キーワード,URL,ランク,距離,...
"龍郷町 求人","https://jp.stanby.com/...",3,1344,...
"龍谷大学 求人","https://jp.stanby.com/...",6,1472,...
```

必要なカラム:
- `キーワード`: 検索キーワード
- `URL`: ページURL
- `ランク`: 検索順位（数値または"50+"）
- `距離`: 距離スコア（数値）
- ファイル名から日付を自動抽出（例: `Site_xxx_2025-11-08.csv`）

### 出力ファイル

1. **マージデータ**: `data/processed/merged_data_YYYYMMDD_HHMMSS.csv`
   - 全CSVファイルを統合し、必要カラムのみ抽出

2. **分析結果**: `data/analysis/weekly_analysis_YYYYMMDD_HHMMSS.csv`
   - キーワード×URLごとの前期比較データ（順位変化、距離変化など）

3. **示唆レポート**: `data/analysis/insights_report_YYYYMMDD_HHMMSS.txt`
   - 改善/下落Top 10、統計サマリー

**注**: `50+`や空URLのデータは分析時に自動除外されます。

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
