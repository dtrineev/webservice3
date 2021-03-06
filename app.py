#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import pymorphy2
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import requests

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(100)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('connect_event', namespace='/test')
def connect_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    
@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
	
    morph = pymorphy2.MorphAnalyzer()
    text = message['data']
    
    #Выкашивание опечаток
    #Максимальный размер строки запроса — 10Кб
    params = {'text': text, 'lang': 'ru'}
    r = requests.get('http://speller.yandex.net/services/spellservice.json/checkText', params=params)
    if r.status_code == 200:
        if len(r.json()) > 0:
            for result in r.json():
                variants = [v for v in result['s']]
                text=text.replace(result['word'],variants[0])
                
    text = text.lower()   
    tokens = word_tokenize(text)

    #Очистить текст от знаков препинания
    tokens = [i for i in tokens if ( i not in string.punctuation )]

    #Убрать лишние слова по стоп-листу
    stop_words = stopwords.words('russian')
    stop_words.extend(['что','это','так','вот','быть','как','в','—','к','на','я','мы','вы','ты','он','она'])
    tokens = [i for i in tokens if ( i not in stop_words )]

    #Нормализовать текст
    tokens = [morph.parse(i)[0].normal_form for i in tokens if ( i not in stop_words )]

    #Убрать дубликаты
    tokens = list(set(tokens))

    #Отсортировать
    tokens.sort()

    emit('my_response',
         {'data': tokens, 'count': session['receive_count']})

@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
