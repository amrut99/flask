import eventlet
import hashlib
eventlet.monkey_patch()
from flask import (
    Flask, 
    request, 
    redirect, 
    jsonify, 
    render_template, 
    session, 
    copy_current_request_context)
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from flask_pymongo import PyMongo
from threading import Lock
import json
import copy
import os
import datetime
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['SECRET_KEY']='thisistopsecret'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = 'static/media'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#app.config["MONGO_URI"] = "mongodb://localhost:27017/QuestionBank"
mongoQ = PyMongo(app, "mongodb://localhost:27017/QuestionBank")
mongoL = PyMongo(app, "mongodb://localhost:27017/LeaderBoard")
mongoUser = PyMongo(app, "mongodb://localhost:27017/Users")
app.host = '0.0.0.0'
socket_ = SocketIO(app, message_queue='redis://localhost:6379', cors_allowed_origins="*")
salt = "9wgt"
thread = None
thread_lock = Lock()

def is_authenticated():
    try:
        print(session['loggedin'])
        if not session['loggedin'] == "":
            user = mongoUser.db.users.find_one({"_id":ObjectId(session['loggedin'])})
            if user:
               return user
    except KeyError:
        pass
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        db_password = hashlib.sha224((request.form["password"]+salt).encode()).hexdigest()
        user = mongoUser.db.users.insert_one({"username":request.form["username"],"password":db_password})
        if user:
            return render_template('login.html',message='Your account is successfully created. Now you can login.')
        else:
            return render_template('signup.html',message='Something went wrong!!!')

@app.route("/quiz", methods=['GET'])
def create_quiz():
    if request.method =='GET':
        user = is_authenticated()
        if not user:
            return render_template('login.html', message="Please login to create new quiz")
        questions = mongoQ.db.producer.find({'owner':user['username']})
        allquizes = set([q['qcode'] for q in questions])
        return render_template("create_quiz.html", username=user['username'], allquizes=allquizes)


@app.route("/", methods=['GET', 'POST'])
def start_quiz():
    if request.method == 'GET':
        return render_template('join_quiz.html')
    elif request.method == 'POST':
        qc = request.form['quizcode']
        uname = request.form['uname']
        quiz = mongoQ.db.producer.find_one({"qcode":qc})
        if quiz:
            if uname.strip() == "":
                uname = "player " + str(datetime.datetime.now().microsecond)
            return render_template('post_answer.html',quizcode=qc, username=uname)
        else:
            return render_template('join_quiz.html', message="The quiz code does not exist!!")


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'GET':
        try:
            print(session['loggedin'])
            if not session['loggedin'] == "":
                user = mongoUser.db.users.find_one({"_id":ObjectId(session['loggedin'])})
                if user:
                    questions = mongoQ.db.producer.find({'owner':user['username']})
                    allquizes = [q['qcode'] for q in questions]
                    return render_template('create_quiz.html', username=user['username'], allquizes=allquizes)
                else:
                    return render_template('login.html')
            return render_template('login.html')
        except KeyError:
            return render_template('login.html')
    elif request.method == 'POST':
        db_password = hashlib.sha224((request.form["password"]+salt).encode()).hexdigest()
        user = mongoUser.db.users.find_one({"username":request.form["username"],"password":db_password})
        print(user)
        if user:
            session['loggedin'] = str(user['_id'])
            questions = mongoQ.db.producer.find({'owner':user['username']})
            allquizes = [q['qcode'] for q in questions]
            return render_template("create_quiz.html", username=user['username'], allquizes=allquizes)
        else:
            session['loggedin'] = ""
            return render_template('login.html',message='Login failed!!!')

@app.route("/<quiz_code>")
def question_page(quiz_code):
    questions = mongoQ.db.producer.find({"qcode":quiz_code})
    all_questions = []
    for q in questions:
        del q['_id']
        all_questions.append(copy.deepcopy(q))
    return json.dumps(all_questions)

@app.route("/post-answer/<quiz_code>",methods=['GET'])
def post_answer(quiz_code):
    return render_template('post_answer.html')

@app.route("/leaderboards/<quiz_code>", methods=['GET'])
def get_leaderboards(quiz_code):
     # Create leaderboard
    players = mongoL.db.leaderboard.aggregate([
        {'$match': {'qcode':quiz_code}},
        {'$group': {'_id':'$username','total':{'$sum':'$answer'}}}
    ])
    leaders = {}
    for p in players:
        leaders[p["_id"]] = p["total"]
    return json.dumps(leaders)

def get_leaderboard_html(quiz_code):
    players = mongoL.db.leaderboard.aggregate([
        {'$match': {'qcode':quiz_code}},
        {'$group': {'_id':'$username','total':{'$sum':'$answer'}}}
    ])
    leaders = {}
    leader_html=""
    try:
        for p in sorted(players, key= lambda item:item['total'], reverse=True):
            leader_html=("{}<tr><td>{}</td><td>{}</td></tr>").format(leader_html, p["_id"], p["total"])
    except:
        pass
    return leader_html

@socket_.on('connect')
def quiz_connect():
    print("Connected succ")
    emit('mybroadcast', json.dumps({
    "q":"Who is V. Anand?",
    "a":["cricketer","chess player","Soccer","Tennis"],
    "ans":"chess player"
  }), broadcast=True)

# @socket_.on('message')
# def quiz_message(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     print(message['q'])

@socket_.on('broadcast')
def quiz_broadcast(message):
    print("Broadcasting....")
    session['receive_count'] = session.get('receive_count', 0) + 1
    print(message['quiz'])
    emit('mybroadcast', message, room=message['quiz'])

@socket_.on('answer')
def record_answer(message):
    # Record answer
    resp = {}
    print("Answer Submitted:")
    print(message)
    question = mongoQ.db.producer.find_one({"_id":ObjectId(message['question'])})
    if message['answer'] == question['ans']:
        resp['answer'] = 1
        # Add to leaderboard
        mongoL.db.leaderboard.insert_one({
            "date": datetime.datetime.now().strftime("%Y%m%d"),
            "qcode": message["qcode"],
            "username": message["username"],
            "q":message["question"],
            "answer": 1
        })
        emit('leaderboard', resp)
    else:
        mongoL.db.leaderboard.insert_one({
            "date": datetime.datetime.now().strftime("%Y%m%d"),
            "qcode": message["qcode"],
            "username": message["username"],
            "q":message["question"],
            "answer": 0
        })
        resp['answer'] = 0
        emit('leaderboard', resp)
    emit('all_leaderboard', get_leaderboard_html(message["qcode"]), room=message["qcode"])


@socket_.on('join_quiz')
def join_quiz(message):
    print(message)
    username = message['username']
    room = message['quiz']
    join_room(room)

# @socket_.on('my_broadcast_event')
# def test_broadcast_message(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': message['data'], 'count': session['receive_count']},
#          broadcast=True)

@socket_.on('disconnect')
def leave_quiz():
    print("Client disconnected....")

@socket_.on('disconnect_request', namespace='/ws/quizstart')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)

# @app.route("/post-question/<qcode>/<nxt>", methods=['GET'])
# @app.route("/post-question/<qcode>", methods=['GET'])
# def post_question(qcode, nxt=None):
#     print(nxt)
#     if not nxt:
#         nxt = 1
#     questions = mongoQ.db.producer.find({"qcode":qcode})
#     print(questions)
#     count = 1
#     for q in questions:
#         print(q)
#         if count == int(nxt):
#             return render_template('post_question.html',quizcode=qcode,
#                                                     username="Amrut",
#                                                    q=q['q'],
#                                                    c1=q['c1'],
#                                                    c2=q['c2'],
#                                                    c3=q['c3'],
#                                                    c4=q['c4'],
#                                                    img="/"+q['img'])
#         count = count + 1
#     print("Out of loop")
#     return render_template('post_question.html',quizcode=qcode, message="No record Found!!")
@app.route("/post-questions/<qcode>", methods=['GET'])
def post_questions(qcode):
    user = is_authenticated()
    if user:
        qroom = hashlib.sha224((user["username"]+qcode).encode()).hexdigest()
        return render_template('post_question_v.html',quizcode=qcode, username=user["username"], qroom=qroom)
    else:
        return render_template('login.html',message='Please login to post questions.')

@app.route("/logout", methods=['GET'])
def logout():
    try:
        del session['loggedin']
        return render_template('login.html',message='You are logged out. Do you want to Login again?')
    except KeyError:
        return render_template('login.html',message='Please login to logout again.')
#
#
# All Ajax APIs
#
#
@app.route("/get-questions/<qcode>", methods=['GET'])
def get_questions(qcode):
    user = is_authenticated()
    if user:
        questions = mongoQ.db.producer.find({"qcode":qcode, "owner":user["username"]})
        allquestions = [q for q in questions]
        return json.dumps(allquestions, default=str)
    else:
        return json.dumps({})

# def get_quizes():
#     user = is_authenticated()
#     if not user:
#         return None
#     else:
#         questions = mongoQ.db.producer.find({'owner':user['username']})
#         all_quiz = {}

#         for q in questions:
#             if not q['qcode'] in all_quiz:
#                 all_quiz[q['qcode']] = 1
#         return json.dumps(all_quiz, default=str)


@app.route("/uploads/", methods=['POST', 'GET'])
@app.route("/uploads/<quizcode>", methods=['POST', 'GET'])
def save_question(quizcode=None):
# check if the post request has the file part
    user = is_authenticated()
    if request.method == 'POST':
        imgpath = ""
        resp = ""
        if not user:
            return render_template("login.html", message="Please login to create quiz.")
        print(request.form)
        if 'file' not in request.files:
            imgpath="/"
            # resp = jsonify({'message' : 'No file part in the request'})
            # resp.status_code = 400
            # return res
        else:
            file = request.files['file']
            if file.filename == '':
                resp = 'No file selected for uploading'
            if file and allowed_file(file.filename):
                filename = "{}-{}".format(request.form['qcode'], secure_filename(file.filename))
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                resp = jsonify({'message' : 'File successfully uploaded'})
                imgpath="/" + app.config['UPLOAD_FOLDER']+"/"+filename
            else:
                resp = 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'
        print(request.form['options'])
        mongoQ.db.producer.insert_one(
            {
                'qcode':request.form['qcode'],
                'q': request.form['q'],
                'c1': request.form['c1'],
                'c2': request.form['c2'],
                'c3': request.form['c3'],
                'c4': request.form['c4'],
                'ans': request.form[request.form['options']],
                'img': imgpath,
                'owner': user['username']
            }
        )
        resp="Question Added successfully"
        return render_template('producer.html', message=resp, quizcode=request.form['qcode'])
    if request.method == 'GET':
        if user:
            # Check is quizcode is unique]
            quiz = mongoQ.db.producer.find_one({'$and':[{'qcode':quizcode},{'owner':{'$ne':user['username']}}]})
            if quiz:
                return render_template('create_quiz.html', message="The quiz name is not unique!!! Add some more characters to the name")
            return render_template('producer.html',quizcode=quizcode, username=user['username'])
        else:
            return render_template('login.html', message="Please login to create a new quiz..")

if __name__ == '__main__':
    socket_.run(app)