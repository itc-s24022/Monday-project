from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- PostgreSQL 接続設定 ---
# setup.sh と docker-compose.yml の設定と一致させる
DB_USER="todo_user"
DB_PASSWORD="todo_password"
DB_NAME="todo_db"

USE_POSTGRESQL = True  # PostgreSQL を使用するかどうか

if USE_POSTGRESQL:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://todo_user:todo_password@localhost/todo_db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://todo_user:todo_password@localhost/todo_db'

db = SQLAlchemy(app)

class Todo(db.Model):
    # テーブル名が自動的に todo になる
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # 実際は完了フラグなども必要だが、シンプル化のため省略

@app.route("/", methods=["GET"])
def home():
    # データベースからすべての Todo を取得
    todo_list = db.session.execute(db.select(Todo).order_by(Todo.id)).scalars().all()
    
    # データベース情報（表示用）
    db_info = {
        'type': 'PostgreSQL',
        'database': DB_NAME,
        'user': DB_USER,
        'host': 'localhost:5432'
    }

    # index.html テンプレートが必要です
    return render_template("index.html", todo_list=todo_list, db_info=db_info)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    if title:
        new_todo = Todo(title=title)
        db.session.add(new_todo)
        db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    todo = db.get_or_404(Todo, todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        # アプリ起動時にテーブルが存在しなければ作成
        db.create_all()
    app.run(debug=True)