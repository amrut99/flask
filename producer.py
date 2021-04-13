import eventlet
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
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY']='thisistopsecret'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = 'static/media'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#app.config["MONGO_URI"] = "mongodb://localhost:27017/QuestionBank"
mongoQ = PyMongo(app, "mongodb://localhost:27017/QuestionBank")
app.host = '0.0.0.0'
socket_ = SocketIO(app, message_queue='redis://localhost:6379', cors_allowed_origins="*", async_mode=async_mode)

thread = None
thread_lock = Lock()

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    return render_template('show_question.html')

@socket_.on('connect')
def quiz_connect():
    print("Connected succ")
    emit('mybroadcast', json.dumps({
    "q":"Who is V. Anand?",
    "a":["cricketer","chess player","Soccer","Tennis"],
    "ans":"chess player"
  }), broadcast=True)

@socket_.on('message')
def quiz_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    print(message['q'])

@socket_.on('broadcast')
def quiz_broadcast(message):
    print("Broadcasting....")
    session['receive_count'] = session.get('receive_count', 0) + 1
    print(message['quiz'])
    emit('mybroadcast', message, room=message['quiz'])

@socket_.on('answer')
def record_answer(message):
    # Record answer
    print("Answer Submitted:")
    print(message)

@socket_.on('join_quiz')
def join_quiz(message):
    print(message)
    username = message['username']
    room = message['quiz']
    join_room(room)

@socket_.on('my_broadcast_event')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)

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

@app.route("/post-question/<qcode>/<nxt>", methods=['GET'])
@app.route("/post-question/<qcode>", methods=['GET'])
def post_question(qcode, nxt=None):
    print(nxt)
    if not nxt:
        nxt = 1
    questions = mongoQ.db.producer.find({"qcode":qcode})
    print(questions)
    count = 1
    for q in questions:
        print(q)
        if count == int(nxt):
            return render_template('post_question.html',quizcode=qcode,
                                                    username="Amrut",
                                                   q=q['q'],
                                                   c1=q['c1'],
                                                   c2=q['c2'],
                                                   c3=q['c3'],
                                                   c4=q['c4'],
                                                   img="/"+q['img'])
        count = count + 1
    print("Out of loop")
    return render_template('post_question.html',quizcode=qcode, message="No record Found!!")


@app.route("/uploads/", methods=['POST', 'GET'])
@app.route("/uploads/<quizcode>", methods=['POST', 'GET'])
def save_question(quizcode=None):
# check if the post request has the file part
    if request.method == 'POST':
        imgpath = ""
        resp = ""
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
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                resp = jsonify({'message' : 'File successfully uploaded'})
                imgpath=os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
                'img': imgpath
            }
        )
        resp="Question Added successfully"
        return render_template('producer.html', message=resp, quizcode=request.form['qcode'])
    if request.method == 'GET':
        return render_template('producer.html',quizcode=quizcode, username="Amrut")

if __name__ == '__main__':
    socket_.run(app)