from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, Blueprint

admin_r = Blueprint('admin',__name__, url_prefix='/admin')

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)
app.register_blueprint(admin_r)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)

class Quiz_result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    right_number = db.Column(db.Integer)
    quiz_number = db.Column(db.Integer)

class Quiz_questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255))
    answer = db.Column(db.String(10))

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)