import os
import collections

import sqlite3

from flask import Flask
from flask import abort
from flask import g
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request

DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'escape.sqlite')

app = Flask(__name__)

LAST_QUESTION_NUMBER = 9


def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = sqlite3.connect(DATABASE_PATH)
    g._database = db
  return db

@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()
    del g._database

# Debug only endpoint to clear the cookie for restarting under a different player ID.
@app.route('/clear_cookie')
def clear_cookie():
  response = make_response()
  response.set_cookie("player_id", "", expires=0)
  return response

# 1. Login page for the game.
@app.route('/', methods=['GET', 'POST'])
def index():
  player_id_cookie = request.cookies.get("player_id", None)
  player_id_url = request.args.get("player_id", None)

  if not player_id_cookie and not player_id_url:
    abort(403)

  if player_id_cookie and player_id_url and player_id_cookie != player_id_url:
    return render_template('cookie_already_set.html')

  response = make_response(render_template('index.html'))
  if player_id_cookie is None and player_id_url:
    response.set_cookie("player_id", player_id_url)
  return response

# 2. Forgot Password dialog to start the game.
@app.route('/forgotten')
def forgotten():
  get_player_id_or_abort()
  return render_template('forgotten.html')

def get_player_id_or_abort():
  player_id = request.cookies.get("player_id")
  if not player_id:
    abort(403)
  return player_id

# 3. Actual game: Rendering of questions.
@app.route('/question/<int:question_number>', methods=['GET', 'POST'])
def show_question(question_number):
  player_id = get_player_id_or_abort()

  question = lookup_question(question_number)
  if question is None:
    return render_template('invalid_question.html'), 404

  if check_question_permission(player_id, question_number) is False:
    return render_template('not_yet.html'), 404

  # Choose the kind of keyboard is displayed during input (numbers only vs full).
  # TODO: Add keyboard choice in database.
  question_name = lookup_question_name(question_number)
  answer_type = "text"
  if question_name in ['bubba', 'finger_food', 'pencil_shadow']:
    answer_type = "tel"

  if request.method == "GET":
    known_answer = ""
    if is_already_solved(player_id, question_number):
      known_answer = get_known_answer(question_number)
    return render_template('question1.html',
                           question=question,
                           question_number=question_number,
                           answer_provided=False,
                           known_answer=known_answer,
                           answer_type=answer_type)

  answer_submitted = request.form["question1_answer"]
  return check_answer(player_id, question_number, answer_submitted, answer_type=answer_type)

def check_question_permission(player_id, question_number):
  if question_number == 1:
    return True

  query = """SELECT number FROM player_status
             INNER JOIN questions ON player_status.question_name_solved = questions.question_name
             WHERE player_id = :player_id"""
  cur = get_db().execute(query, {"player_id": player_id})
  sequence_answered_question_numbers = cur.fetchall()
  cur.close()

  if not sequence_answered_question_numbers:
    return False
  list_answered_question_numbers = []

  for item in sequence_answered_question_numbers:
    list_answered_question_numbers.append(item[0])

  if question_number <= max(list_answered_question_numbers) + 1:
    return True
  return False


def check_answer(player_id, question_number, answer_submitted, answer_type):
  """Looks in database if 'answer_submitted' for 'question_number' is correct and if yes updates quiz database."""
  # Check database for answers.
  question_name = lookup_question_name(question_number)
  if question_name is None:
    return render_template('invalid_question.html'), 404

  question = lookup_question(question_number)
  list_correct_answers = lookup_anwers(question_name)
  if question is None or list_correct_answers is None:
    abort(500)

  # Compare given_answer with correct answers.
  for answer in list_correct_answers:
    if (answer.lower() == answer_submitted.lower() or
        answer.replace(" ", "") == answer_submitted.replace(" ", "")):
      update_correct_answers(player_id, question_name)
      if question_number == LAST_QUESTION_NUMBER:
        return redirect("/thank_you")
      return render_template('question1.html',
                             correct=True,
                             question=question,
                             question_number=question_number,
                             answer_provided=True,
                             answer_submitted=answer_submitted,
                             next_question_number=question_number+1,
                             answer_type=answer_type)

  return render_template('question1.html',
                         correct=False,
                         question=question,
                         question_number=question_number,
                         answer_provided=True,
                         answer_submitted=answer_submitted,
                         answer_type=answer_type)


def lookup_question(question_number):
  query = "SELECT question FROM questions WHERE number = :question_number"
  cur = get_db().execute(query, {"question_number": question_number})
  question_sequence = cur.fetchone()
  cur.close()
  if question_sequence is None:
    return None
  return question_sequence[0]


def lookup_question_name(question_number):
  query = "SELECT question_name FROM questions WHERE number = :question_number"
  cur = get_db().execute(query, {"question_number": question_number})
  sequence_question_name = cur.fetchone()
  cur.close()
  if sequence_question_name is None:
    return None
  return sequence_question_name[0]


def lookup_anwers(question_name):
  query = "SELECT answer FROM answers WHERE question_name = :question_name"
  cur = get_db().execute(query, {"question_name": question_name})
  sequence_correct_answers = cur.fetchall()
  cur.close()

  if sequence_correct_answers is None:
    return None

  list_correct_answers = []
  for item in sequence_correct_answers:
    list_correct_answers.append(item[0])
  return list_correct_answers

def get_known_answer(question_number):
  question_name = lookup_question_name(question_number)
  if not question_name:
    return False

  query = "SELECT answer FROM answers WHERE question_name = :question_name ORDER BY answer LIMIT 1"
  cur = get_db().execute(query, {"question_name": question_name})
  known_answer = cur.fetchone()[0]
  cur.close()
  return known_answer

def is_already_solved(player_id, question_number):
  question_name = lookup_question_name(question_number)
  if not question_name:
    return False

  query = "SELECT COUNT(*) FROM player_status WHERE player_id = :player_id AND question_name_solved = :question_name"
  cur = get_db().execute(query, {"player_id":player_id, "question_name":question_name})
  count_sequence = cur.fetchone()[0]
  cur.close()
  if count_sequence:
    return True
  return False

def update_correct_answers(player_id, question_name):
  query = "INSERT OR IGNORE INTO player_status (player_id, question_name_solved) VALUES (:player_id, :question_name)"
  db = get_db()
  cur = db.execute(query, {"player_id": player_id, "question_name": question_name})
  db.commit()
  cur.close()

@app.route('/status')
def status():
  player_id = get_player_id_or_abort()
  all_questions = get_all_questions_and_unlocked_status(player_id)
  if check_question_permission(player_id, LAST_QUESTION_NUMBER + 1):
    return render_template('status.html', all_questions=all_questions, all_questions_solved=True)
  return render_template('status.html', all_questions=all_questions)

class QuestionStatus:
  def __init__(self, description):
    self.solved = False
    self.unlocked = False
    self.description = description

def get_all_questions_and_unlocked_status(player_id):
  all_questions = collections.OrderedDict()

  query_initial_dict = "SELECT number, question_name FROM questions ORDER BY number ASC"
  cur_initial = get_db().execute(query_initial_dict)
  sequence_initial_dict = cur_initial.fetchall()
  cur_initial.close()
  if not sequence_initial_dict:
    return all_questions

  for item_initial in sequence_initial_dict:
    question_number = item_initial[0]
    question_name = item_initial[1]
    description = "Question %d" % question_number
    if question_name.lower() == "challenge":
      description += " (Challenge)"
    all_questions[question_number] = QuestionStatus(description)

  all_questions[1].unlocked = True

  query_update_dict = "SELECT number FROM player_status INNER JOIN questions ON player_status.question_name_solved = questions.question_name WHERE player_id = :player_id ORDER BY number ASC"
  cur = get_db().execute(query_update_dict, {"player_id": player_id})
  sequence_answered_question_numbers = cur.fetchall()
  cur.close()
  help_last_entry = 1
  if not sequence_answered_question_numbers:
    return all_questions

  for item in sequence_answered_question_numbers:
    question_number = item[0]
    all_questions[question_number].solved = True
    all_questions[question_number].unlocked = True
    help_last_entry = max(question_number, help_last_entry)

  help_last_entry = help_last_entry + 1
  if help_last_entry in all_questions:
    all_questions[help_last_entry].unlocked = True
  return all_questions

@app.route('/thank_you')
def thank_you():
  player_id = get_player_id_or_abort()
  if check_question_permission(player_id, LAST_QUESTION_NUMBER + 1) is False:
    abort(404)
  return render_template("final.html")

@app.route('/not_yet')
def not_yet():
  return render_template("not_yet.html")

@app.route('/invalid_question')
def invalid_question():
  return render_template("invalid_question.html")

@app.route('/cookie_already_set')
def cookie_already_set():
  return render_template("cookie_already_set.html")
