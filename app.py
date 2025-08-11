from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, Blueprint, request, redirect, session, url_for
import random

admin_r = Blueprint('admin',__name__, url_prefix='/admin')

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'replace_this_with_a_secret_key'

db = SQLAlchemy()
db.init_app(app)
app.register_blueprint(admin_r)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)

class Quiz_result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    right_number = db.Column(db.Integer)
    quiz_number = db.Column(db.Integer)

class Quiz_questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255))  # 包含题目和选项
    answer = db.Column(db.String(10))     # 正确答案

@app.route("/homepage")
def homepage():
    # 这里简单判定用户登录
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        entry = User(
            email = email,
            password = password,
        )
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template("register.html")

@app.route("/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        match = User.query.filter_by(email=email, password=password).first()
        if match:
            session['user_id'] = match.id
            session['user_email'] = match.email
            return redirect(url_for('homepage'))
        else:
            message = "Invalid password or email"
            return render_template("login.html", message=message)
    else:
        return render_template("login.html")

# 新增：答题页面-选择难度（GET）和开始答题（POST）
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        # 显示难度选择页面
        return render_template('select_difficulty.html')

    difficulty = request.form.get('difficulty')
    if difficulty not in ['easy', 'medium', 'hard']:
        return redirect(url_for('quiz'))

    # 根据难度获取题目id范围
    if difficulty == 'easy':
        ids = list(range(1, 21))
        count = 10
    elif difficulty == 'medium':
        ids = list(range(21, 41))
        count = 10
    else:
        ids = list(range(41, 51))
        count = 5

    question_ids = random.sample(ids, count)
    questions = Quiz_questions.query.filter(Quiz_questions.id.in_(question_ids)).all()

    # 把题目和答案存session方便提交校验
    session['questions'] = [{
        'id': q.id,
        'question': q.question,
        'answer': q.answer
    } for q in questions]

    return render_template('quiz.html', questions=session['questions'])

# 新增：提交答题结果，显示报告并保存记录
@app.route('/submit', methods=['POST'])
def submit():
    if not session.get('user_id') or not session.get('questions'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    questions = session['questions']

    user_answers = {}
    for q in questions:
        # 从表单中获取答案，name是题目id
        ans = request.form.get(str(q['id']), '').strip()
        user_answers[q['id']] = ans

    correct_count = 0
    results = []

    for q in questions:
        correct = (user_answers[q['id']].lower() == q['answer'].lower())
        if correct:
            correct_count += 1
        results.append({
            'question': q['question'],
            'correct_answer': q['answer'],
            'user_answer': user_answers[q['id']],
            'correct': correct
        })

    # 保存结果
    quiz_result = Quiz_result(
        user_id=user_id,
        right_number=correct_count,
        quiz_number=len(questions)
    )
    db.session.add(quiz_result)
    db.session.commit()

    accuracy = round(correct_count / len(questions) * 100, 2)

    # 清除session中的题目
    session.pop('questions', None)

    return render_template('result.html', results=results, accuracy=accuracy)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=8000)
