#!/bin/bash

# SEOデータ分析を実行するスクリプト
set -e  # エラーが発生したら停止

echo "=========================================="
echo "SEOデータ分析を開始します"
echo "=========================================="
echo ""

# ステップ1: Google Driveからダウンロード
echo "[1/4] Google Driveからデータをダウンロード中..."
python download_from_drive_oauth.py
echo "✓ ダウンロード完了"
echo ""

# ステップ2: データマージ
echo "[2/4] CSVファイルをマージ中..."
python merge_data.py
echo "✓ マージ完了"
echo ""

# ステップ3: トレンド分析
echo "[3/4] トレンド分析を実行中..."
python analyze_trends.py
echo "✓ 分析完了"
echo ""

# ステップ4: 結果をGitにコミット
echo "[4/4] 分析結果をGitにコミット中..."
TIMESTAMP=$(date +"%Y-%m-%d")

git add data/analysis/*.csv data/analysis/*.txt
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
