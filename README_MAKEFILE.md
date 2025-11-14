# Makefile使用ガイド

## 基本コマンド

### 全体実行
```bash
make all         # 全7ステップを一括実行（推奨）
make             # make all と同じ
```

### 個別実行
```bash
make clean                      # 中間ファイルと分析結果を削除
make download                   # Google Driveからデータをダウンロード
make merge                      # CSVファイルをマージ
make analyze-seo                # SEOランク分析を実行
make analyze-search-console     # Search Console分析を実行
make export-dify                # Dify用データをエクスポート
make upload                     # Google Driveにアップロード
make commit                     # Git commitを実行
```

### ユーティリティ
```bash
make setup-folders              # Google Driveフォルダを作成（初回のみ）
make upload-raw-data            # ローカルの生データをGoogle Driveにアップロード
make upload-dify                # Dify APIに自動アップロード（要.env設定）
make help                       # ヘルプ表示
```

## パラメータ

### Search Console分析のカスタマイズ
```bash
# 取得週数を変更（デフォルト: 12週）
make analyze-search-console WEEKS=24

# 最小インプレッションを変更（デフォルト: 50）
make analyze-search-console MIN_IMP=100

# 全体実行時に適用
make all WEEKS=24 MIN_IMP=100
```

## 典型的なワークフロー

### 1. 初回セットアップ
```bash
# Google Driveフォルダを作成
make setup-folders

# ローカルの生データをGoogle Driveにアップロード
make upload-raw-data
```

### 2. 定期実行（週次）
```bash
# 全てを実行
make all

# GitHubにプッシュ
git push origin main
```

### 3. クリーンスタート
```bash
# 古い結果を削除
make clean

# 再実行
make all
```

### 4. Dify自動更新（オプション）
```bash
# .envファイルを設定後
make export-dify
make upload-dify
```

## トラブルシューティング

### エラーが発生した場合
```bash
# クリーンアップして再実行
make clean
make all
```

### 特定のステップのみ再実行
```bash
# 例: Search Console分析のみやり直し
make analyze-search-console
make export-dify
make upload
```

### Google Driveからダウンロードできない
```bash
# 生データを手動でアップロード
make upload-raw-data

# または、drive_folder_ids.jsonを確認
cat drive_folder_ids.json
```
