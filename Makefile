.PHONY: help clean download merge analyze-seo analyze-search-console generate-insights export-dify upload commit all diagram

# デフォルトターゲット
help:
	@echo "=========================================="
	@echo "SEO ETL Pipeline - Makefile"
	@echo "=========================================="
	@echo ""
	@echo "利用可能なコマンド:"
	@echo "  make all                  # 全ての処理を実行（デフォルト）"
	@echo "  make clean                # 中間ファイルと分析結果を削除"
	@echo "  make download             # Google Driveからデータをダウンロード"
	@echo "  make merge                # CSVファイルをマージ"
	@echo "  make analyze-seo          # SEOランク分析を実行"
	@echo "  make analyze-search-console  # Search Console分析を実行"
	@echo "  make generate-insights    # Claude Codeで考察を生成（要API Key）"
	@echo "  make export-dify          # Dify用データをエクスポート"
	@echo "  make upload               # Google Driveにアップロード"
	@echo "  make commit               # Git commitを実行"
	@echo "  make setup-folders        # Google Driveフォルダを作成"
	@echo "  make upload-raw-data      # ローカルの生データをGoogle Driveにアップロード"
	@echo "  make upload-dify          # Dify APIに自動アップロード（要.env設定）"
	@echo "  make diagram              # パイプライン図を生成（HTML）"
	@echo ""
	@echo "パラメータ:"
	@echo "  WEEKS=12                  # Search Console取得週数（デフォルト: 12）"
	@echo "  MIN_IMP=50                # Search Console最小インプレッション（デフォルト: 50）"
	@echo ""

# パラメータ
WEEKS ?= 12
MIN_IMP ?= 50
TIMESTAMP := $(shell date +"%Y-%m-%d")

# 全ての処理を実行
all: download merge analyze-seo analyze-search-console generate-insights export-dify upload commit
	@echo ""
	@echo "=========================================="
	@echo "✅ 全ての処理が完了しました！"
	@echo "=========================================="
	@echo ""
	@echo "次のステップ:"
	@echo "  git push origin main    # GitHubにプッシュ"
	@echo ""

# クリーンアップ
clean:
	@echo "=========================================="
	@echo "クリーンアップ実行"
	@echo "=========================================="
	@bash scripts/cleanup.sh

# ステップ1: Google Driveからダウンロード
download:
	@echo "[1/8] Google Driveからデータをダウンロード中..."
	@python scripts/download_from_drive_oauth.py
	@echo "✓ ダウンロード完了"
	@echo ""

# ステップ2: CSVファイルをマージ
merge:
	@echo "[2/8] CSVファイルをマージ中..."
	@python scripts/merge_data.py
	@echo "✓ マージ完了"
	@echo ""

# ステップ3: SEOランク分析
analyze-seo:
	@echo "[3/8] SEOランク トレンド分析を実行中..."
	@python scripts/analyze_trends.py
	@echo "✓ SEOランク分析完了"
	@echo ""

# ステップ4: Search Console分析
analyze-search-console:
	@echo "[4/8] Search Console 週次分析を実行中..."
	@python scripts/query_search_console.py $(WEEKS) $(MIN_IMP)
	@echo "✓ Search Console分析完了"
	@echo ""

# ステップ5: Claude Codeで考察生成
generate-insights:
	@echo "[5/8] Claude Codeで考察を生成中..."
	@python scripts/generate_insights.py
	@echo "✓ 考察生成完了"
	@echo ""

# ステップ6: Dify用データエクスポート
export-dify:
	@echo "[6/8] Dify用データをエクスポート中..."
	@python scripts/export_for_dify.py
	@echo "✓ Difyエクスポート完了"
	@echo ""

# ステップ7: Google Driveにアップロード
upload:
	@echo "[7/8] Google Driveに結果をアップロード中..."
	@python scripts/upload_to_drive_oauth.py
	@echo "✓ アップロード完了"
	@echo ""

# ステップ8: Gitコミット
commit:
	@echo "[8/8] 分析結果をGitにコミット中..."
	@git add data/analysis/*.csv data/analysis/*.txt data/dify_export/*.md data/insights/*.md 2>/dev/null || true
	@git commit -m "Add SEO analysis results for $(TIMESTAMP)\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>" || echo "変更がないためコミットをスキップしました"
	@echo "✓ コミット完了"
	@echo ""

# Google Driveフォルダセットアップ（初回のみ）
setup-folders:
	@echo "Google Driveフォルダを作成中..."
	@python scripts/setup_drive_folders.py
	@echo "✓ フォルダ作成完了"
	@echo ""

# ローカルの生データをGoogle Driveにアップロード
upload-raw-data:
	@echo "ローカルの生データをGoogle Driveにアップロード中..."
	@python scripts/upload_raw_data.py
	@echo "✓ アップロード完了"
	@echo ""

# Dify API自動アップロード（オプション）
upload-dify:
	@echo "Dify APIに自動アップロード中..."
	@python scripts/upload_to_dify_api.py
	@echo "✓ Difyアップロード完了"
	@echo ""

# パイプライン図の生成
diagram:
	@echo "=========================================="
	@echo "パイプライン図を生成中..."
	@echo "=========================================="
	@python scripts/generate_diagram.py
	@echo ""
	@echo "ブラウザで開くには:"
	@echo "  open docs/pipeline_diagram.html"
	@echo ""
