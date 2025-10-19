from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, Blueprint, request, redirect, session, url_for
import random

admin_r = Blueprint('admin', __name__, url_prefix='/admin')

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto reload templates on changes
app.debug = True  # Enable debug mode

# Configure database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'replace_this_with_a_secret_key'  # Session encryption key

db = SQLAlchemy()
db.init_app(app)
app.register_blueprint(admin_r)

# User model: stores email and password
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)

# Quiz result model: stores score for each completed quiz
class Quiz_result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    right_number = db.Column(db.Integer)
    quiz_number = db.Column(db.Integer)

# Quiz questions model: stores quiz questions and correct answer
class Quiz_questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255))
    answer = db.Column(db.String(10))


@app.route("/homepage")
def homepage():
    # Redirect to login if user is not authenticated
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template("index.html")


@app.route("/about")
def about_us():
    return render_template("about.html")


@app.route("/news")
def news():
    return render_template("news.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    # Handle registration form
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        entry = User(
            email=email,
            password=password,
        )
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template("register.html")


@app.route("/", methods=['GET', 'POST'])
def login():
    # Process login form
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        match = User.query.filter_by(email=email, password=password).first()
        if match:
            # Save login status to session
            session['user_id'] = match.id
            session['user_email'] = match.email
            return redirect(url_for('homepage'))
        else:
            message = "Invalid password or email"
            return render_template("login.html", message=message)
    else:
        return render_template("login.html")


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    # Only logged-in users can take quiz
    if not session.get('user_id'):
        return redirect(url_for('login'))

    # Ask user to choose difficulty first
    if request.method == 'GET':
        return render_template('select_difficulty.html')

    # Validate difficulty choice
    difficulty = request.form.get('difficulty')
    if difficulty not in ['easy', 'medium', 'hard']:
        return redirect(url_for('quiz'))

    # Select random question IDs based on difficulty
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

    # Save questions to session for comparison later
    session['questions'] = [{
        'id': q.id,
        'question': q.question,
        'answer': q.answer
    } for q in questions]

    return render_template('quiz.html', questions=session['questions'])


@app.route('/submit', methods=['POST'])
def submit():
    # Must be logged in and have questions in session
    if not session.get('user_id') or not session.get('questions'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    questions = session['questions']

    # Collect user's submitted answers
    user_answers = {}
    for q in questions:
        ans = request.form.get(str(q['id']), '').strip()
        user_answers[q['id']] = ans

    correct_count = 0
    results = []

    # Compare answers and build result list
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

    # Save quiz result to database
    quiz_result = Quiz_result(
        user_id=user_id,
        right_number=correct_count,
        quiz_number=len(questions)
    )
    db.session.add(quiz_result)
    db.session.commit()

    accuracy = round(correct_count / len(questions) * 100, 2)

    # Clear questions from session after submission
    session.pop('questions', None)

    return render_template('result.html', results=results, accuracy=accuracy)


@app.route('/records')
def records():
    # Show all past quiz results for the logged-in user
    if not session.get('user_id'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    results = Quiz_result.query.filter_by(user_id=user_id).all()

    return render_template('records.html', results=results)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if not exist
    app.run(host='127.0.0.1', port=8000)
