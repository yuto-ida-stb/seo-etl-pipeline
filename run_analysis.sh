#!/bin/bash

# SEOデータ分析を実行するスクリプト
set -e  # エラーが発生したら停止

echo "=========================================="
echo "SEOデータ分析を開始します"
echo "=========================================="
echo ""

# ステップ1: Google Driveからダウンロード
echo "[1/6] Google Driveからデータをダウンロード中..."
python download_from_drive_oauth.py
echo "✓ ダウンロード完了"
echo ""

# ステップ2: データマージ
echo "[2/6] CSVファイルをマージ中..."
python merge_data.py
echo "✓ マージ完了"
echo ""

# ステップ3: SEOランク トレンド分析
echo "[3/6] SEOランク トレンド分析を実行中..."
python analyze_trends.py
echo "✓ SEOランク分析完了"
echo ""

# ステップ4: Search Console 週次分析
echo "[4/6] Search Console 週次分析を実行中..."
python query_search_console.py 12 50
echo "✓ Search Console分析完了"
echo ""

# ステップ5: Google Driveにアップロード
echo "[5/6] Google Driveに結果をアップロード中..."
python upload_to_drive_oauth.py
echo "✓ アップロード完了"
echo ""

# ステップ6: 結果をGitにコミット
echo "[6/6] 分析結果をGitにコミット中..."
TIMESTAMP=$(date +"%Y-%m-%d")

git add data/analysis/*.csv data/analysis/*.txt
# Search ConsoleデータはGoogle Driveのみに保存（Gitには含めない）
git commit -m "Add SEO analysis results for ${TIMESTAMP}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
" || echo "変更がないためコミットをスキップしました"

echo "✓ コミット完了"
echo ""

echo "=========================================="
echo "✅ 全ての処理が完了しました！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "  git push origin main    # GitHubにプッシュ"
echo ""
