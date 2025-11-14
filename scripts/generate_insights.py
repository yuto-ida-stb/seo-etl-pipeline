"""
Claude Codeを使って前処理済みデータから考察を生成

使い方:
    # 最新の分析結果から考察を生成
    python scripts/generate_insights.py

    # 特定のファイルを指定
    python scripts/generate_insights.py --seo data/analysis/weekly_analysis_20251114.csv

    # Search Consoleデータも含める
    python scripts/generate_insights.py --search-console data/search_console/search_console_weekly_20251114.csv
"""
import os
import sys
import glob
import pandas as pd
from datetime import datetime
import anthropic

# 環境変数から設定を読み込み
def load_env():
    """簡易的な.envファイル読み込み"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def get_latest_files():
    """最新の分析結果ファイルを取得"""
    seo_files = sorted(glob.glob('./data/analysis/weekly_analysis_*.csv'))
    search_console_files = sorted(glob.glob('./data/search_console/search_console_weekly_*.csv'))
    insights_files = sorted(glob.glob('./data/analysis/insights_report_*.txt'))

    result = {}

    if seo_files:
        result['seo_csv'] = seo_files[-1]
    if insights_files:
        result['seo_txt'] = insights_files[-1]
    if search_console_files:
        result['search_console'] = search_console_files[-1]

    return result

def load_seo_data(csv_path, txt_path=None):
    """SEOランク分析データを読み込み"""
    data_summary = {}

    # CSVデータを読み込み
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        data_summary['total_records'] = len(df)
        data_summary['date_range'] = f"{df['date'].min()} ～ {df['date'].max()}"

        # Top改善/下落
        data_summary['top_improved'] = df.nsmallest(10, 'rank_diff')[
            ['keyword', 'url', 'previous_rank', 'current_rank', 'rank_diff']
        ].to_dict('records')

        data_summary['top_declined'] = df.nlargest(10, 'rank_diff')[
            ['keyword', 'url', 'previous_rank', 'current_rank', 'rank_diff']
        ].to_dict('records')

        # 統計
        data_summary['stats'] = {
            'avg_rank_change': df['rank_diff'].mean(),
            'improved_count': (df['rank_diff'] < 0).sum(),
            'declined_count': (df['rank_diff'] > 0).sum(),
        }

    # テキストレポートを読み込み
    if txt_path and os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            data_summary['text_report'] = f.read()

    return data_summary

def load_search_console_data(csv_path):
    """Search Console分析データを読み込み（サンプルのみ）"""
    if not os.path.exists(csv_path):
        return None

    df = pd.read_csv(csv_path)

    data_summary = {
        'total_records': len(df),
        'unique_rhash': df['r_hash'].nunique(),
        'date_range': f"{df['week_start'].min()} ～ {df['week_start'].max()}",

        # Top インプレッション増加
        'top_impression_increase': df.nlargest(10, 'imp_diff')[
            ['r_hash', 'week_start', 'total_impressions', 'prev_impressions', 'imp_diff', 'imp_change_rate']
        ].to_dict('records'),

        # Top CTR改善
        'top_ctr_improvement': df.nlargest(10, 'ctr_diff')[
            ['r_hash', 'week_start', 'avg_ctr', 'prev_ctr', 'ctr_diff', 'ctr_change_rate']
        ].to_dict('records'),

        # Top 順位改善（position_diffが負の方が良い）
        'top_position_improvement': df.nsmallest(10, 'position_diff')[
            ['r_hash', 'week_start', 'avg_position', 'prev_position', 'position_diff', 'position_change_rate']
        ].to_dict('records'),

        # 統計
        'stats': {
            'avg_imp_change': df['imp_diff'].mean(),
            'avg_ctr_change': df['ctr_diff'].mean(),
            'avg_position_change': df['position_diff'].mean(),
            'imp_increased_count': (df['imp_diff'] > 0).sum(),
            'imp_decreased_count': (df['imp_diff'] < 0).sum(),
        }
    }

    return data_summary

def generate_insights_with_claude(seo_data, search_console_data=None):
    """Claude APIを使って考察を生成"""

    # APIキーを取得
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ エラー: ANTHROPIC_API_KEYが設定されていません")
        print("\nセットアップ手順:")
        print("1. https://console.anthropic.com/ でAPIキーを取得")
        print("2. .envファイルを作成:")
        print("   cp .env.example .env")
        print("3. .envファイルにAPIキーを設定:")
        print("   ANTHROPIC_API_KEY=sk-ant-xxxxx")
        sys.exit(1)

    # プロンプトを構築
    prompt = build_prompt(seo_data, search_console_data)

    # Claude APIクライアントを作成
    client = anthropic.Anthropic(api_key=api_key)

    print("Claude APIで考察を生成中...")
    print(f"モデル: claude-3-5-sonnet-20241022")

    # APIリクエスト
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        temperature=0.3,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return message.content[0].text

def build_prompt(seo_data, search_console_data=None):
    """考察生成用のプロンプトを構築"""

    prompt = f"""あなたはSEOデータ分析の専門家です。以下のデータを分析して、包括的な考察レポートを日本語で作成してください。

# SEOランク分析データ

## 基本情報
- データ期間: {seo_data.get('date_range', 'N/A')}
- 総レコード数: {seo_data.get('total_records', 0):,}件
- 順位改善: {seo_data.get('stats', {}).get('improved_count', 0)}件
- 順位下落: {seo_data.get('stats', {}).get('declined_count', 0)}件
- 平均順位変化: {seo_data.get('stats', {}).get('avg_rank_change', 0):.2f}

## Top 10 順位改善キーワード
"""

    for i, item in enumerate(seo_data.get('top_improved', [])[:10], 1):
        prompt += f"{i}. {item['keyword']}: {item['previous_rank']:.0f}位→{item['current_rank']:.0f}位 ({item['rank_diff']:+.0f})\n"

    prompt += "\n## Top 10 順位下落キーワード\n"
    for i, item in enumerate(seo_data.get('top_declined', [])[:10], 1):
        prompt += f"{i}. {item['keyword']}: {item['previous_rank']:.0f}位→{item['current_rank']:.0f}位 ({item['rank_diff']:+.0f})\n"

    # Search Consoleデータがあれば追加
    if search_console_data:
        prompt += f"""

# Search Console週次分析データ

## 基本情報
- データ期間: {search_console_data.get('date_range', 'N/A')}
- 総レコード数: {search_console_data.get('total_records', 0):,}件
- ユニークr_hash数: {search_console_data.get('unique_rhash', 0):,}件
- 平均インプレッション変化: {search_console_data.get('stats', {}).get('avg_imp_change', 0):+.1f}
- 平均CTR変化: {search_console_data.get('stats', {}).get('avg_ctr_change', 0):+.4f}
- 平均順位変化: {search_console_data.get('stats', {}).get('avg_position_change', 0):+.2f}

## Top 5 インプレッション増加
"""
        for i, item in enumerate(search_console_data.get('top_impression_increase', [])[:5], 1):
            prompt += f"{i}. r_hash: {item['r_hash'][:16]}... | {item['week_start']} | {item['prev_impressions']:,.0f}→{item['total_impressions']:,.0f} ({item['imp_change_rate']:+.1f}%)\n"

        prompt += "\n## Top 5 CTR改善\n"
        for i, item in enumerate(search_console_data.get('top_ctr_improvement', [])[:5], 1):
            prompt += f"{i}. r_hash: {item['r_hash'][:16]}... | {item['week_start']} | CTR: {item['prev_ctr']:.4f}→{item['avg_ctr']:.4f} ({item['ctr_change_rate']:+.1f}%)\n"

    prompt += """

# 依頼内容

以下の形式で包括的な考察レポートを作成してください：

## 1. エグゼクティブサマリー
- 今期の主要な成果と課題を3-5行で要約

## 2. 主要な発見事項
### 2.1 SEOランク分析
- 順位改善の傾向分析
  - 改善が顕著なキーワードの共通点
  - 地域名や職種などのパターン分析
- 順位下落の要因分析
  - 下落したキーワードの特徴
  - 競合の影響や市場変化の可能性
"""

    if search_console_data:
        prompt += """
### 2.2 Search Console分析
- インプレッション動向
  - 急増したr_hashの特徴
  - 全体的なトレンド
- CTRパフォーマンス
  - CTR改善要因の仮説
  - タイトル・メタディスクリプションの影響
- 検索順位の変化
  - 順位改善と他指標との相関
"""

    prompt += """
## 3. データから読み取れる課題
- 改善が必要な領域
- 注意すべきネガティブトレンド
- リスク要因

## 4. 改善提案
- 短期的アクションアイテム（1-2週間で実施可能）
- 中期的施策（1-2ヶ月）
- 検証すべき仮説

## 5. 次回分析時の着目点
- モニタリングすべきKPI
- 追加で取得すべきデータ

---

**注意事項:**
- データに基づいた客観的な分析を行う
- 推測する場合は「～と考えられる」「～の可能性がある」など明示
- 具体的なキーワード名やr_hashを適宜引用
- 数値は具体的に記載
- マーケティング視点とSEO技術視点の両方から分析
"""

    return prompt

def save_insights(insights_text, output_dir='./data/insights'):
    """考察結果を保存"""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f'claude_insights_{timestamp}.md')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# SEOデータ分析 - Claude考察レポート\n\n")
        f.write(f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(insights_text)

    print(f"\n✅ 考察レポートを保存しました: {output_file}")
    return output_file

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Claude Codeで考察を生成')
    parser.add_argument('--seo', type=str, help='SEOランク分析CSVファイルのパス')
    parser.add_argument('--seo-txt', type=str, help='SEOランク分析レポートtxtファイルのパス')
    parser.add_argument('--search-console', type=str, help='Search Console分析CSVファイルのパス')

    args = parser.parse_args()

    print("=" * 70)
    print("Claude Code考察生成")
    print("=" * 70)
    print()

    # 環境変数を読み込み
    load_env()

    # ファイルを指定
    if args.seo or args.search_console:
        # コマンドライン引数で指定された場合
        seo_csv = args.seo
        seo_txt = args.seo_txt
        search_console_csv = args.search_console
    else:
        # 最新ファイルを自動検出
        print("最新の分析結果を自動検出中...")
        files = get_latest_files()
        seo_csv = files.get('seo_csv')
        seo_txt = files.get('seo_txt')
        search_console_csv = files.get('search_console')

    # データを読み込み
    print("\nデータ読み込み中...")

    if not seo_csv or not os.path.exists(seo_csv):
        print("❌ エラー: SEOランク分析データが見つかりません")
        print("   make analyze-seo を先に実行してください")
        sys.exit(1)

    print(f"  SEOランク分析: {seo_csv}")
    seo_data = load_seo_data(seo_csv, seo_txt)

    search_console_data = None
    if search_console_csv and os.path.exists(search_console_csv):
        print(f"  Search Console: {search_console_csv}")
        search_console_data = load_search_console_data(search_console_csv)
    else:
        print("  Search Console: スキップ（データなし）")

    print()

    # Claude APIで考察を生成
    try:
        insights = generate_insights_with_claude(seo_data, search_console_data)

        # 結果を保存
        output_file = save_insights(insights)

        # プレビュー表示
        print("\n" + "=" * 70)
        print("考察レポート（プレビュー）")
        print("=" * 70)
        print(insights[:500] + "...\n")
        print(f"完全版: {output_file}")

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
