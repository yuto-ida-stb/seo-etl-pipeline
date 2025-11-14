#!/bin/bash

# SEO ETL Pipeline クリーンアップスクリプト
# 中間ファイルと分析結果を削除して、クリーンな状態に戻します

set -e

echo "=========================================="
echo "SEO ETL Pipeline クリーンアップ"
echo "=========================================="
echo ""

# 削除対象を確認
echo "削除対象ファイルを確認中..."
echo ""

ANALYSIS_COUNT=$(ls data/analysis/*.csv data/analysis/*.txt 2>/dev/null | wc -l | tr -d ' ')
PROCESSED_COUNT=$(ls data/processed/*.csv 2>/dev/null | wc -l | tr -d ' ')
DIFY_COUNT=$(ls data/dify_export/*.md 2>/dev/null | wc -l | tr -d ' ')

echo "削除対象:"
echo "  - data/analysis/: ${ANALYSIS_COUNT}件"
echo "  - data/processed/: ${PROCESSED_COUNT}件"
echo "  - data/dify_export/: ${DIFY_COUNT}件"
echo ""

# 削除実行
echo "削除中..."

rm -f data/analysis/*.csv data/analysis/*.txt
echo "✓ data/analysis/ をクリア"

rm -f data/processed/*.csv
echo "✓ data/processed/ をクリア"

rm -f data/dify_export/*.md
echo "✓ data/dify_export/ をクリア"

echo ""
echo "=========================================="
echo "✅ クリーンアップ完了"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "  make all    # 分析を実行"
echo ""
