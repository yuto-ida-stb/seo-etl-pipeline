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

## Phase0: AWS環境準備

### インフラ構築
- Infra&DataチームにDifyのAWSセルフホスティングについて相談
  - タグの付与ルール等について確認
- AI開発基盤用のAWSアカウントを**2つ**用意
  - 検証環境
  - 本番環境
- 北内さんにサポートいただきました 🙏

---

## Phase1: デプロイ完了


### リポジトリ作成
- **Dify AWS構成管理用リポジトリ**を作成
  - https://github.com/stanby-inc/dify-on-aws
  - AWS公式のDifyリポジトリをベース
  - **AWS公式のメンテナンスの恩恵**を受けられる設計

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

1. ✅ **インデックス落ちr_hashの特定**
   - site:検索データからの月次分析

2. ✅ **Search Console分析のSQL最適化**
   - BigQueryとの連携自動化
   - r_hash別週次分析（IMP, CTR, 順位）

3. ✅ **SEOランク継続トレンド追跡**
   - カテゴリーマッピング統合
   - 時系列での順位・距離変化を追跡

4. ❌ **Claude Codeでのインサイト生成**
   - 分析結果から自動考察を生成（未実施）

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
[5. Google Driveアップロード]
     ↓
[6. Claude Code考察生成]
```

---

## データ処理の工夫

### 前処理の実装

1. **不要データの除外**
2. **統計情報の追加**
   - 前週比の差分・変化率を計算
   - Top xリスト（改善/下落）を自動生成
---

<!-- _class: lead -->
# 成果物

---

## 成果物一覧

### 1. リポジトリ
- **dify-on-aws**: AWS環境管理
- **seo_etl_pipeline**: ETLパイプライン本体

### 2. データ分析パイプライン
- 自動化されたデータ収集・分析・配信
- Makefileによる簡単操作

---

## フォルダ構成

```
seo_etl_pipeline/
├── data/
│   ├── raw/                  # Google Driveからの生データ
│   ├── processed/            # マージ済みデータ
│   ├── analysis/             # 分析結果
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

### 1. インデックス落ちr_hashの特定

### 2. 分析結果CSV
- キーワード×URL別の前週比較
- 順位変化、距離変化、変化率

### 3. インサイトレポート（テキスト）
- 改善Top 10
- 下落Top 10
- 統計サマリー

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

## 学んだこと

### 技術面
1. **データの前処理の重要性**
   - 生データをそのまま投入しても効果薄
   - 構造化・要約が必須

---

## 学んだこと（続き）

### プロジェクト運営
1. **迅速な方向転換**
   - 1日目の課題を2日目で解決
   - ETLパイプラインの追加実装

---

<!-- _class: lead -->
# まとめ

---

## 合宿の成果

### 2日間で実現したこと

✅ **Dify環境構築**（検証・本番）
✅ **ETLパイプラインの実装**
✅ **自動分析・考察生成の仕組み**
✅ **makeコマンドでの簡単実行**
✅ **ドキュメント・図の整備**

### 次のステップ
-> **生成AIによる考察取得**
-> **運用フェーズへ移行**（定期実行・ワークフロー拡充）

---

