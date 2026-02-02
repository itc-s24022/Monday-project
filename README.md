# ItCol 月次作業報告ツール

IT業務における作業実績を日々記録し、月次で集計・報告するためのWebアプリケーションです。

## 📋 プロジェクトの現状

### 現在の実装状況

✅ **完了済み**

- PostgreSQL データベース接続
- 基本的なタスク管理機能（登録・一覧・削除）
- Flask + SQLAlchemy による基本構造

❌ **未実装（これから開発する機能）**

- タイマー機能（作業時間の自動計測）
- カテゴリ分類機能
- 月次集計機能（プロジェクト別、カテゴリ別）
- レポート画面
- A4印刷対応

### 開発体制

- **対象者**: IT専門学生 6名
- **開発期間**: 9時間（1日）
- **合計工数**: 54人時間

## 📖 ドキュメント

### 外部設計書

**場所**: `docs/external_design.html`

外部設計書には以下の内容が含まれています：

- システム概要と目的
- UI画面と機能仕様（MUST機能 / OPTION機能）
- データベース設計
- API設計
- 工数見積もり
- 役割分担（6名体制）
- タイムライン

**閲覧方法**:

```bash
# ブラウザで開く
open docs/external_design.html
# または
firefox docs/external_design.html
```

### UI参考画像の配置方法

外部設計書にUI参考画像を表示するには、以下の手順で画像を配置してください：

1. UI画面のスクリーンショットを用意
   - タスク登録画面のスクリーンショット
   - 月次レポート画面のスクリーンショット

2. 画像を以下の場所に配置

   ```
   docs/images/ui_task_entry.png      ← タスク登録画面
   docs/images/ui_monthly_report.png  ← 月次レポート画面
   ```

3. 外部設計書（`docs/external_design.html`）をブラウザで開くと画像が表示されます

**注**: 画像が配置されていない場合は、プレースホルダーが表示されます。

## 🚀 クイックスタート

### 前提条件

- Python 3.x
- PostgreSQL

### セットアップ

1. リポジトリをクローン

   ```bash
   git clone <repository-url>
   cd ItColTaskReportMonthly
   ```

2. PostgreSQL をセットアップ

   ```bash
   # Linux/Mac (ローカル PostgreSQL を使う手順)
   ./setup.sh

   # Windows
   .\setup_windows.ps1

   # Docker を使う（推奨）
   # - 既にホストの5432が使われていると `docker compose up` が失敗します。
   # - 本リポジトリには競合ポートを自動で選ぶヘルパーとセットアップスクリプトがあります。
   # 推奨: 自動で空きポートを選んで起動する
   ./setup_docker.sh

   # あるいは、短いヘルパースクリプトを使う
   ./scripts/docker_compose_up.sh
   ```

3. Python 依存関係をインストール

   ```bash
   pip install -r requirements.txt
   ```

4. アプリケーションを起動

   ```bash
   # PostgreSQL を使用する場合
   USE_POSTGRESQL=1 python app.py

   # SQLite を使用する場合（開発用）
   python app.py
   ```

5. ブラウザで `http://localhost:5000` にアクセス

## 📂 プロジェクト構成

```
ItColTaskReportMonthly/
├── app.py                    # Flask アプリケーション本体
├── requirements.txt          # Python 依存関係
├── docker-compose.yml        # Docker 構成
├── README.md                 # このファイル
├── docs/
│   ├── external_design.html  # 外部設計書（必読）
│   └── images/               # UI 参考画像の配置場所
│       ├── ui_task_entry.png       # （配置してください）
│       └── ui_monthly_report.png   # （配置してください）
├── templates/
│   └── index.html            # フロントエンド（現在は基本的なタスク一覧のみ）
├── static/
│   └── style.css             # スタイルシート
├── setup.sh                  # Linux/Mac セットアップスクリプト
├── setup_windows.ps1         # Windows セットアップスクリプト
├── setup_docker.sh           # Docker セットアップスクリプト
├── setup_macos.sh            # macOS セットアップスクリプト
└── setup_wsl.sh              # WSL セットアップスクリプト
```

## 👥 開発の進め方

### 1. 外部設計書を確認

まず `docs/external_design.html` を開いて、以下を確認してください：

- 実装する機能（MUST / OPTION）
- データベース設計
- API 仕様
- 役割分担

### 2. チームで役割分担

外部設計書の「6. 役割分担と作業計画」を参照し、6名で以下の役割に分かれます：

| 担当者 | 役割                                  |
| ------ | ------------------------------------- |
| A      | プロジェクトリーダー兼 API 開発       |
| B      | データベース担当兼集計 API 開発       |
| C      | フロントエンド実装1（タスク登録画面） |
| D      | フロントエンド実装2（レポート画面）   |
| E      | テスト担当兼品質保証                  |
| F      | 技術検証・調査兼発表資料作成          |

### 3. タイムライン（9時間 / 1日）

- **0:00 - 1:00**: キックオフ・設計レビュー
- **1:00 - 4:00**: 実装フェーズ1
- **4:00 - 4:30**: 中間レビュー
- **4:30 - 7:00**: 実装フェーズ2
- **7:00 - 8:30**: テスト・修正
- **8:30 - 9:00**: 成果確認・発表準備

### 4. MUST 機能（優先実装）

- **M-1**: タスク登録フォーム
- **M-2**: タイマー機能
- **M-3**: 月次集計機能
- **M-4**: プロジェクト別一覧表示
- **M-5**: カテゴリ別集計
- **M-6**: 印刷対応（CSS）

## 🎯 目標

月次の作業報告を以下の流れで実現する：

1. **日次操作**: タスクを登録し、タイマーで作業時間を計測
2. **月次集計**: プロジェクトやカテゴリ別に作業時間を集計
3. **レポート出力**: A4サイズで印刷可能なレポートを生成

## 🛠 技術スタック

- **バックエンド**: Python 3.x + Flask
- **データベース**: PostgreSQL
- **ORM**: SQLAlchemy
- **フロントエンド**: HTML5 + CSS3 + JavaScript (Vanilla JS)
- **タイマー実装**: JavaScript (setInterval / Date)
- **印刷対応**: CSS @media print

## 📝 開発ノート

### データベース

現在のテーブル構成：

- `Todo` テーブル（既存）: id, title

改修後のテーブル構成（外部設計書参照）：

- `tasks` テーブル: id, task_name, category, memo, start_time, end_time, duration_seconds, created_date, created_at

### API エンドポイント（予定）

- `GET /` - タスク登録画面
- `POST /task/add` - タスク登録
- `POST /task/start` - タイマー開始
- `POST /task/stop` - タイマー停止
- `POST /task/delete/<id>` - タスク削除
- `GET /report` - 月次レポート画面
- `GET /api/report/monthly` - 月次集計データ取得（JSON）

## 📞 サポート

質問や問題が発生した場合は、チーム内で共有してください。

## 📄 ライセンス

このプロジェクトは教育目的で作成されています。

---

**Good luck with your development! 🚀**
