# PostgreSQL Setup for Flask Todo App

このドキュメントでは、Flask TodoアプリケーションをPostgreSQLで動作させるためのセットアップ手順を説明します。

## 前提条件

- Ubuntu環境（Ubuntu 18.04以降推奨）
- sudo権限
- Python 3.6以降
- pip3

## セットアップ手順

### 1. セットアップスクリプトの実行

```bash
chmod +x setup.sh
./setup.sh
```

このスクリプトは以下の処理を自動で行います：

1. PostgreSQLのインストール
2. PostgreSQLサービスの起動
3. データベースとユーザーの作成
4. Python依存関係のインストール
5. app.pyの自動更新（SQLite → PostgreSQL）
6. データベーステーブルの初期化

### 2. アプリケーションの起動

```bash
python3 app.py
```

ブラウザで http://localhost:5000 にアクセスしてください。

## データベース設定（固定値）

setup.shで以下の固定値が設定されます：

- **データベース名**: todo_db
- **ユーザー名**: todo_user
- **パスワード**: todo_password
- **ホスト**: localhost
- **ポート**: 5432

## 手動でのデータベース操作

PostgreSQLに直接アクセスする場合：

```bash
# psqlでデータベースに接続
psql -U todo_user -d todo_db -h localhost

# パスワード入力が求められたら: todo_password
```

## トラブルシューティング

### PostgreSQLサービスが起動しない場合

```bash
sudo service postgresql start
sudo service postgresql status
```

### データベースを再作成する場合

```bash
./setup.sh
```

setup.shは既存のデータベースを削除してから再作成します。

### app.pyが元のSQLite設定に戻ってしまった場合

```bash
# 手動でPostgreSQL接続文字列に更新
sed -i "s|sqlite:///db.sqlite|postgresql://todo_user:todo_password@localhost/todo_db|g" app.py
```

## 注意事項

- このセットアップは開発環境向けです
- 本番環境では、パスワードを環境変数で管理してください
- セキュリティを強化する場合は、PostgreSQLの設定ファイル（pg_hba.conf）を適切に設定してください
