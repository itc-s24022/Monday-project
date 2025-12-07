from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 環境変数でデータベースを切り替え可能
# デフォルトはSQLite、USE_POSTGRESQL=1でPostgreSQLを使用
USE_POSTGRESQL = os.environ.get('USE_POSTGRESQL') == '1'

if USE_POSTGRESQL:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://todo_user:todo_password@localhost/todo_db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))


@app.route("/", methods=["GET", "POST"])
def home():
    todo_list = Todo.query.all()

    # データベース情報を取得
    db_info = None
    if USE_POSTGRESQL:
        db_info = {
            'type': 'PostgreSQL',
            'database': 'todo_db',
            'user': 'todo_user',
            'host': 'localhost'
        }

    return render_template("index.html", todo_list=todo_list, db_info=db_info)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    new_todo = Todo(title=title)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
