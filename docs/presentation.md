---
marp: true
theme: default
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.svg')
header: 'スタンバイSEO 11月大阪合宿'
footer: '2025年11月13-14日'
---

<!-- _class: lead -->
# スタンバイSEO
# 11月大阪合宿

## Dify × ETLパイプライン
### SEOデータ分析基盤の構築

2025年11月13-14日

---

# アジェンダ

1. **11/13（1日目）** - Dify環境構築
2. **11/14（2日目）** - ETLパイプライン構築
3. **成果物とデモ**
4. **今後の展望**

---

<!-- _class: lead -->
# 11/13（1日目）
## Dify環境構築フェーズ

---

## Phase1: AWS環境準備

### インフラ構築
- AI開発基盤用のAWSアカウントを**2つ**用意
  - 検証環境
  - 本番環境
- 北内さんにサポートいただきました 🙏

### リポジトリ作成
- **Dify AWS構成管理用リポジトリ**を作成
  - https://github.com/stanby-inc/dify-on-aws
  - AWS公式のDifyリポジトリをベース
  - **AWS公式のメンテナンスの恩恵**を受けられる設計

---

## Phase1: デプロイ完了

### 環境構築
- 検証環境にDifyをデプロイ ✅
- 本番環境にDifyをデプロイ ✅
- 最低限の動作確認完了 ✅

---

## Phase2: Difyワークフロー構築

### 目標機能
以下の4つの分析機能を実現：

1. **インデックス落ちr_hashの特定**
   - データソース: site:検索から作成した月次データ

2. **SEO順位変動の把握**（r_hash別）
   - データソース: DemandMetricsダウンロードデータ

3. **獲得セッション変動の把握**（r_hash別）
   - データソース: BigQueryダウンロードデータ

4. **生成AIによる考察取得**

---

## 1日目の課題

### 直面した問題

❌ **生データを直接Difyに渡すと処理されない**
- データの前処理が必要
- Difyのナレッジベースが生データを十分に理解できず

❌ **Dify操作に時間がかかった**
- Dify力が不足していた
- ワークフロー設計の試行錯誤に時間を要した

### 結論
→ **データの前処理（ETL）が必須**と判明

---

<!-- _class: lead -->
# 11/14（2日目）
## ETLパイプライン構築フェーズ

---

## 2日目の成果：ETLパイプライン実装

### 主要な実装内容

1. ✅ **Search Console分析のSQL最適化**
   - BigQueryとの連携自動化
   - r_hash別週次分析（IMP, CTR, 順位）

2. ✅ **スクリプト整理とMakefile導入**
   - `make all` で全処理を一括実行
   - 7ステップの自動パイプライン

3. ✅ **インデックス落ちr_hashの特定**
   - site:検索データからの月次分析

4. ❌ **Claude Codeでのインサイト生成**
   - 分析結果から自動考察を生成（未実施）

---

## 2日目の成果（続き）

5. ✅ **SEOランク継続トレンド追跡**
   - カテゴリーマッピング統合
   - 時系列での順位・距離変化を追跡

6. ✅ **Google Driveフォルダ再編成**
   - 生データ、分析結果を自動アップロード
   - フォルダ構造の最適化

---

## ETLパイプライン全体像

```
[Google Drive]        [BigQuery]
     ↓                    ↓
[1. ダウンロード]   [BigQueryでクエリ実行・ダウンロード]
     ↓                    ↓
[2. CSVマージ] ←──────────┘
     ↓
[3. SEOランク分析]
     ↓
[4. Search Console分析]
     ↓
[5. Claude Code考察生成]
     ↓
[6. Google Driveアップロード]
     ↓
[7. Gitコミット]
```

---

## パイプライン詳細

### データフロー
```bash
Google Drive (生データ) → ローカル → マージ → 分析
                                          ↓
BigQuery (Search Console)でクエリ実行 ──→ 分析
                                          ↓
                          ← Google Driveアップロード
                          ← Git管理
```

### 実行コマンド
```bash
make all  # 7ステップを一括実行
```

---

## データ処理の工夫

### 前処理の実装

1. **不要データの除外**
   - `50+`ランクのデータを除外
   - 空URLのデータを除外

2. **統計情報の追加**
   - 前週比の差分・変化率を計算
   - Top 10リスト（改善/下落）を自動生成

3. **Markdown形式の出力**
   - Difyが理解しやすい構造化データ
   - データ辞書・メタデータの自動生成

---

<!-- _class: lead -->
# 成果物

---

## 成果物一覧

### 1. リポジトリ
- **dify-on-aws**: AWS環境管理
- **seo_data**: ETLパイプライン本体

### 2. データ分析パイプライン
- 自動化されたデータ収集・分析・配信
- Makefileによる簡単操作

### 3. Dify連携
- ナレッジベースへの自動データ投入
- AIチャットボットによる分析結果の問い合わせ

---

## フォルダ構成

```
seo_data/
├── data/
│   ├── raw/                  # Google Driveからの生データ
│   ├── processed/            # マージ済みデータ
│   ├── analysis/             # 分析結果
│   ├── dify_export/          # Dify用Markdown
│   └── search_console/       # BigQueryデータ
├── scripts/                  # 各種スクリプト
├── sql/                      # BigQuery SQL
├── docs/                     # ドキュメント・図
├── Makefile                  # 簡単実行
└── README.md
```

---

## Google Driveフォルダ構成

```
SEO Data/
├── 00_raw_data/                              # 週次平均データ
├── 01_seo_rank_analysis/                     # SEOランク・距離分析結果
│   ├── weekly_analysis_YYYYMMDD.csv
│   └── insights_report_YYYYMMDD.txt
├── 02_search_console_analysis/               # Search Console分析結果
│   └── search_console_weekly_YYYYMMDD.csv
├── 03_demand_metrics_category_mapping/       # カテゴリーマッピング
├── 03_presentations/                         # プレゼンテーション資料
└── 04_site_analysis/                         # site:検索分析
```

---

## 出力データ例

### 1. 分析結果CSV
- キーワード×URL別の前週比較
- 順位変化、距離変化、変化率

### 2. インサイトレポート（テキスト）
- 改善Top 10
- 下落Top 10
- 統計サマリー

### 3. Dify用Markdown
- データ辞書
- SEOランク分析
- Search Console分析

---

<!-- _class: lead -->
# 今後の展望

---

## 今後の展開

### Phase3: 運用フェーズ
1. **Difyチャットボット統合**
   - Dify APIによるナレッジベース自動更新
   - ワークフローの拡充

2. **定期実行の自動化**
   - GitHub Actionsでの週次実行
   - 結果の自動配信

3. **Claude Codeでのインサイト生成**
   - 分析結果から自動考察を生成

4. **ダッシュボード化**
   - 可視化ツールとの連携
   - リアルタイムモニタリング

---

## 技術的な改善点

### データ処理
- ✅ 前処理パイプラインの構築 → 完了
- 🔄 増分更新の実装
- 🔄 データ品質チェックの強化

### Dify連携
- ✅ 基本的なナレッジベース連携 → 完了
- 🔄 RAGの精度向上
- 🔄 カスタムワークフローの追加

### 運用
- 🔄 エラーハンドリングの強化
- 🔄 ログ・モニタリング整備

---

## 学んだこと

### 技術面
1. **データの前処理の重要性**
   - 生データをそのまま投入しても効果薄
   - 構造化・要約が必須

2. **自動化の価値**
   - Makefileによる簡単操作
   - Git管理による履歴追跡

3. **Difyの特性理解**
   - Markdownベースのナレッジが有効
   - データ辞書の重要性

---

## 学んだこと（続き）

### プロジェクト運営
1. **段階的な構築**
   - Phase1: 環境構築
   - Phase2: ワークフロー
   - Phase3: 運用（今後）

2. **迅速な方向転換**
   - 1日目の課題を2日目で解決
   - ETLパイプラインの追加実装

3. **ドキュメンテーション**
   - README、コード、図の整備
   - 他メンバーへの引き継ぎ容易化

---

<!-- _class: lead -->
# まとめ

---

## 合宿の成果

### 2日間で実現したこと

✅ **Dify環境構築**（検証・本番）
✅ **ETLパイプラインの実装**
✅ **自動分析・考察生成の仕組み**
✅ **Dify連携の基盤**
✅ **Make1コマンドでの簡単実行**
✅ **ドキュメント・図の整備**

### 次のステップ
→ **運用フェーズへ移行**（定期実行・ワークフロー拡充）

---

<!-- _class: lead -->
# ありがとうございました！

## Questions?

リポジトリ:
- https://github.com/stanby-inc/dify-on-aws
- ローカル: `~/work/seo_data`

実行コマンド:
```bash
make all     # 全処理実行
make diagram # パイプライン図生成
```
