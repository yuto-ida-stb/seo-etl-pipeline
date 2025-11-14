# Claude Codeで考察生成 - 使い方ガイド

前処理済みのSEOデータをClaude APIに渡して、専門的な考察レポートを自動生成します。

## セットアップ

### 1. Claude APIキーを取得

1. https://console.anthropic.com/ にアクセス
2. アカウントを作成（未作成の場合）
3. 左メニューから「API Keys」をクリック
4. 「Create Key」ボタンをクリック
5. キー名を入力（例: `seo-analysis`）
6. APIキーをコピー（`sk-ant-`で始まる文字列）

### 2. .envファイルに設定

```bash
# .env.exampleから.envを作成
cp .env.example .env

# .envファイルを編集
nano .env
```

.envファイルに以下を追加：
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx... （取得したAPIキー）
```

### 3. ライブラリをインストール

```bash
pip install -r requirements.txt
```

## 使い方

### 方法1: Makefileで実行（推奨）

#### 全体フロー（考察生成を含む）

```bash
# 全8ステップを一括実行
make all

# 実行される処理:
# 1. Google Driveからダウンロード
# 2. CSVマージ
# 3. SEOランク分析
# 4. Search Console分析
# 5. Claude Codeで考察生成 ← NEW!
# 6. Difyエクスポート
# 7. Google Driveアップロード
# 8. Gitコミット
```

#### 考察生成のみ実行

```bash
# 既存の分析結果から考察を生成
make generate-insights
```

### 方法2: スクリプトを直接実行

#### 最新の分析結果から自動生成

```bash
python scripts/generate_insights.py
```

このコマンドは以下のファイルを自動検出して使用します：
- 最新のSEOランク分析CSV（`data/analysis/weekly_analysis_*.csv`）
- 最新のSEOランク分析レポート（`data/analysis/insights_report_*.txt`）
- 最新のSearch Console分析CSV（`data/search_console/search_console_weekly_*.csv`）

#### 特定のファイルを指定

```bash
# SEOランク分析のみ
python scripts/generate_insights.py \
  --seo data/analysis/weekly_analysis_20251114.csv

# SEOランク分析 + テキストレポート
python scripts/generate_insights.py \
  --seo data/analysis/weekly_analysis_20251114.csv \
  --seo-txt data/analysis/insights_report_20251114.txt

# SEOランク分析 + Search Console分析
python scripts/generate_insights.py \
  --seo data/analysis/weekly_analysis_20251114.csv \
  --search-console data/search_console/search_console_weekly_20251114.csv
```

## データの指定方法

### データファイルの場所

分析後、以下の場所にファイルが生成されます：

```
data/
├── analysis/                    # SEOランク分析結果
│   ├── weekly_analysis_20251114_100902.csv
│   └── insights_report_20251114_100902.txt
├── search_console/              # Search Console分析結果
│   └── search_console_weekly_20251114_101132.csv
└── insights/                    # Claude考察レポート（生成後）
    └── claude_insights_20251114_103045.md
```

### 自動検出の仕組み

`make generate-insights`または引数なしで実行した場合：

1. `data/analysis/weekly_analysis_*.csv`の最新ファイルを取得
2. `data/analysis/insights_report_*.txt`の最新ファイルを取得
3. `data/search_console/search_console_weekly_*.csv`の最新ファイルを取得
4. 見つかったファイルを全て使用して考察を生成

### 手動指定のメリット

- 過去の特定期間のデータで考察を再生成したい場合
- Search Console分析を含めたくない場合
- 複数のデータセットを比較したい場合

## 出力される考察レポート

### ファイル形式

- **保存場所**: `data/insights/claude_insights_{timestamp}.md`
- **形式**: Markdown
- **文字数**: 約2,000-4,000トークン（日本語で約1,500-3,000文字）

### レポート構成

```markdown
# SEOデータ分析 - Claude考察レポート

**生成日時**: 2025-11-14 10:30:45

---

## 1. エグゼクティブサマリー
今期の主要な成果と課題を3-5行で要約

## 2. 主要な発見事項
### 2.1 SEOランク分析
- 順位改善の傾向分析
- 順位下落の要因分析

### 2.2 Search Console分析
- インプレッション動向
- CTRパフォーマンス
- 検索順位の変化

## 3. データから読み取れる課題
- 改善が必要な領域
- 注意すべきネガティブトレンド

## 4. 改善提案
- 短期的アクションアイテム
- 中期的施策
- 検証すべき仮説

## 5. 次回分析時の着目点
- モニタリングすべきKPI
- 追加で取得すべきデータ
```

## 料金について

### Claude API料金（2025年11月時点）

| モデル | 入力 | 出力 |
|--------|------|------|
| Claude 3.5 Sonnet | $3/1M tokens | $15/1M tokens |

### 1回の考察生成コスト

- **入力**: 約2,000-5,000トークン（データ量による）
- **出力**: 約2,000-4,000トークン
- **推定コスト**: $0.06-0.10（約10円）/回

**月次実行の場合**: 週1回 × 4週 = 約40円/月

## トラブルシューティング

### Q1: "ANTHROPIC_API_KEYが設定されていません"エラー

**原因**: .envファイルが作成されていない、またはAPIキーが設定されていない

**対処法**:
```bash
# .envファイルを作成
cp .env.example .env

# .envを編集してAPIキーを設定
nano .env

# APIキーが正しく設定されているか確認
cat .env | grep ANTHROPIC_API_KEY
```

### Q2: "SEOランク分析データが見つかりません"エラー

**原因**: 分析がまだ実行されていない

**対処法**:
```bash
# SEOランク分析を実行
make analyze-seo

# または全体を実行
make all
```

### Q3: API料金が心配

**対処法**:
```bash
# Search Consoleデータを含めない（データ量削減）
python scripts/generate_insights.py --seo data/analysis/weekly_analysis_*.csv

# または、Anthropic ConsoleでAPI Keyの使用量上限を設定
# https://console.anthropic.com/settings/limits
```

### Q4: 考察の質を向上させたい

**対処法**:

1. **より多くのデータを渡す**:
   ```bash
   # Search Consoleデータも含める
   python scripts/generate_insights.py \
     --seo data/analysis/weekly_analysis_*.csv \
     --search-console data/search_console/search_console_weekly_*.csv
   ```

2. **プロンプトをカスタマイズ**:
   - `scripts/generate_insights.py`の`build_prompt()`関数を編集
   - より具体的な質問や分析観点を追加

3. **複数回実行して比較**:
   ```bash
   # Temperature=0.3（デフォルト）
   python scripts/generate_insights.py

   # scripts/generate_insights.pyを編集してtemperature=0.7に変更して再実行
   # より創造的な考察が得られる
   ```

## 活用例

### 週次レポート作成

```bash
# 毎週月曜日に実行
make all

# 生成された考察レポートを確認
cat data/insights/claude_insights_*.md | head -100

# チームに共有
# Slack/EmailなどにMarkdownファイルを添付
```

### 月次サマリー作成

```bash
# 過去4週間のデータを個別に分析
for file in data/analysis/weekly_analysis_*.csv; do
  python scripts/generate_insights.py --seo $file
done

# 4つの考察レポートを比較してトレンドを把握
```

### カスタム分析

```bash
# 特定のキーワードグループに絞った考察
# 1. 事前にCSVをフィルタリング
# 2. フィルタ済みファイルで考察生成
python scripts/generate_insights.py --seo filtered_data.csv
```

## さらに詳しく

- Claude API Documentation: https://docs.anthropic.com/
- Anthropic Console: https://console.anthropic.com/
- Claude 3.5 Sonnetモデル情報: https://www.anthropic.com/news/claude-3-5-sonnet
