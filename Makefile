.PHONY: help clean download merge analyze-seo analyze-search-console analyze-search-console-trends analyze-index-drop generate-insights export-dify upload commit all diagram slides slides-html slides-pdf slides-pptx upload-slides deploy-slides

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
	@echo "  make analyze-search-console-trends  # Search Console順位推移傾向を分析"
	@echo "  make analyze-index-drop   # インデックス落ちr_hashを分析"
	@echo "  make generate-insights    # Claude Codeで考察を生成（要API Key）"
	@echo "  make export-dify          # Dify用データをエクスポート"
	@echo "  make upload               # Google Driveにアップロード"
	@echo "  make commit               # Git commitを実行"
	@echo "  make setup-folders        # Google Driveフォルダを作成"
	@echo "  make upload-raw-data      # ローカルの生データをGoogle Driveにアップロード"
	@echo "  make upload-dify          # Dify APIに自動アップロード（要.env設定）"
	@echo "  make diagram              # パイプライン図を生成（HTML）"
	@echo "  make slides               # プレゼン資料を全形式で生成（HTML/PDF/PPTX）"
	@echo "  make slides-html          # プレゼン資料をHTML形式で生成"
	@echo "  make slides-pdf           # プレゼン資料をPDF形式で生成"
	@echo "  make slides-pptx          # プレゼン資料をPPTX形式で生成"
	@echo "  make upload-slides        # プレゼン資料をGoogle Slidesにアップロード"
	@echo "  make deploy-slides        # プレゼン資料をビルドしてGoogle Slidesにデプロイ"
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

# Search Console順位推移傾向分析（独立タスク）
analyze-search-console-trends:
	@echo "=========================================="
	@echo "Search Console順位推移傾向分析を実行中..."
	@echo "=========================================="
	@echo "1. Google Driveから過去3ヶ月分のデータをダウンロード中..."
	@python scripts/download_search_console_history.py
	@echo ""
	@echo "2. 順位推移傾向を分析中..."
	@python scripts/analyze_search_console_trends.py
	@echo "✓ Search Console順位推移傾向分析完了"
	@echo ""

# インデックス落ち分析（独立タスク）
analyze-index-drop:
	@echo "=========================================="
	@echo "インデックス落ち分析を実行中..."
	@echo "=========================================="
	@python scripts/analyze_index_drop.py
	@echo "✓ インデックス落ち分析完了"
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

# プレゼン資料の生成（全形式）
slides: slides-html slides-pdf slides-pptx
	@echo ""
	@echo "=========================================="
	@echo "✅ プレゼン資料の生成が完了しました！"
	@echo "=========================================="
	@echo ""
	@echo "生成されたファイル:"
	@echo "  - docs/presentation.html"
	@echo "  - docs/presentation.pdf"
	@echo "  - docs/presentation.pptx"
	@echo ""
	@echo "ブラウザで開くには:"
	@echo "  open docs/presentation.html"
	@echo ""

# プレゼン資料の生成（HTML形式）
slides-html:
	@echo "プレゼン資料をHTML形式で生成中..."
	@command -v marp >/dev/null 2>&1 || { echo "Error: marp-cliがインストールされていません。"; echo "インストール: npm install -g @marp-team/marp-cli"; exit 1; }
	@marp docs/presentation.md -o docs/presentation.html --html
	@echo "✓ HTML形式のプレゼン資料を生成しました"

# プレゼン資料の生成（PDF形式）
slides-pdf:
	@echo "プレゼン資料をPDF形式で生成中..."
	@command -v marp >/dev/null 2>&1 || { echo "Error: marp-cliがインストールされていません。"; echo "インストール: npm install -g @marp-team/marp-cli"; exit 1; }
	@marp docs/presentation.md -o docs/presentation.pdf --html --allow-local-files
	@echo "✓ PDF形式のプレゼン資料を生成しました"

# プレゼン資料の生成（PPTX形式）
slides-pptx:
	@echo "プレゼン資料をPPTX形式で生成中..."
	@command -v marp >/dev/null 2>&1 || { echo "Error: marp-cliがインストールされていません。"; echo "インストール: npm install -g @marp-team/marp-cli"; exit 1; }
	@marp docs/presentation.md -o docs/presentation.pptx --html --allow-local-files
	@echo "✓ PPTX形式のプレゼン資料を生成しました"

# プレゼン資料をGoogle Slidesにアップロード
upload-slides:
	@echo "=========================================="
	@echo "プレゼン資料をGoogle Slidesにアップロード中..."
	@echo "=========================================="
	@python scripts/upload_slides_to_drive.py

# プレゼン資料をビルドしてGoogle Slidesにデプロイ
deploy-slides: slides-pptx upload-slides
	@echo ""
	@echo "=========================================="
	@echo "✅ プレゼン資料のデプロイが完了しました！"
	@echo "=========================================="
