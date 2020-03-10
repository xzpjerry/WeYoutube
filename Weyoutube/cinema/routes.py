#################
#### imports ####
#################
import random

from flask import render_template, redirect, flash, request, jsonify
from flask_login import login_required, current_user, logout_user, login_user
from flask_socketio import join_room, leave_room, emit, send

from . import cinema_blueprint
from Weyoutube import db, socketio
from Weyoutube.models import User, Room

################
#### helpers ####
################
def gen_4digits():
    choices = random.sample(range(10), 4)
    return int(''.join(map(str, choices)))
################
#### routes ####
################
@cinema_blueprint.route('/', methods=('GET',))
def index():
    if current_user.is_authenticated:
        return redirect('/watch')
    return render_template('cinema/index.html')

@cinema_blueprint.route('/create', methods=('POST',))
def create_cinema():
    res = {}
    code = 200
    data = request.form
    username = data.get('username', False)
    if username:
        target_user = User.query.filter_by(username = username).first()
        if target_user:
            code = 401
            res['success'] = False
            res['errors'] = ['This Username has been used; please try another one.']
        else:
            target_room = Room(secret = gen_4digits())
            newuser = User(username = username, room=target_room)
            db.session.add(target_room) 
            db.session.add(newuser)
            db.session.commit()
            login_user(newuser, remember=True)
            res['success'] = True
    else:
        code = 401
        res['success'] = False
        res['errors'] = ['You must filled out all values.']
    return jsonify(res), code

@cinema_blueprint.route('/enter', methods=('POST',))
def enter_cinema():
    res = {}
    code = 200
    data = request.form
    username = data.get('username', False)
    room_id = data.get('room_id', False)
    secret = data.get('secret', False)
    if username and room_id and secret:
        try:
            room_id = int(room_id)
            secret = int(secret)
        except:
            code = 401
            res['success'] = False
            res['errors'] = ['The room id or(and) secret is(are) not Integer.']
            return jsonify(res)
        target_user = User.query.filter_by(username = username).first()
        if target_user:
            code = 401
            res['success'] = False
            res['errors'] = ['This Username has been used; please try another one.']
        else:
            target_room = Room.query.filter_by(id = room_id).first()
            if not target_room:
                code = 401
                res['success'] = False
                res['errors'] = ['Invalid Room id.']
            elif not target_room.secret == secret:
                code = 401
                res['success'] = False
                res['errors'] = ['Invalid Secret.']
            else:
                newuser = User(username = username, room=target_room)
                db.session.add(newuser)
                db.session.commit()
                login_user(newuser, remember=True)
                res['success'] = True
    else:
        code = 401
        res['success'] = False
        res['errors'] = ['You must filled out all values.']
    return jsonify(res), code

@cinema_blueprint.route('/leave/<int:user_id>', methods=('GET',))
@login_required
def leave(user_id):
    target = User.query.filter_by(id=user_id).first()
    if target:
        if len(target.room.users) == 1:
            db.session.delete(target.room)
        db.session.delete(target)
        db.session.commit()
    return redirect('/')

@cinema_blueprint.route('/watch', methods=('GET', ))
@login_required
def watch():
    return render_template('cinema/watch.html')

@cinema_blueprint.route('/get/<int:room_id>', methods=('GET', ))
@login_required
def get_play_detail():
    room = current_user.room
    res = {
        'id': room.id,
        'secret': room.secret,
        'vid': room.current_playing_video_ID,
        'playing': room.current_isplaying,
        'seek': room.current_seek
    }
    return jsonify(res)

@socketio.on('join')
def on_join(data):
    print(data['user_id'], 'joined.', 'from', data['room'])
    room_id = data['room']
    join_room(room_id)
    room_obj = Room.query.filter_by(id = room_id).first()
    res = []
    if room_obj:
        res = [user.username for user in room_obj.users]
    emit('join_response', str({'usernames': res}), room=room_id)


'''
Working on this
'''
# @socketio.on('disconnect')
# def on_leave():
#     session_id = request.sid
#     print('Someone disconnected', room_id)
#     room_obj = Room.query.filter_by(id = room_id).first()
#     res = []
#     if room_obj:
#         res = [user.username for user in room_obj.users]
#     emit('disconnect_response', str({'usernames': res}), room=room_id)

##############################
#### For Debuging Purpose ####
##############################
@cinema_blueprint.route('/getusers', methods=('GET', ))
def get_all_current_users():
    res = {}
    tmp = User.query.all()
    for user in tmp:
        sub_res = {}
        sub_res['Room id'] = user.room.id
        sub_res['Room secret'] = user.room.secret
        res[user.username] = sub_res
    return jsonify(res)

@cinema_blueprint.route('/getrooms', methods=('GET', ))
def get_all_rooms():
    res = {}
    tmp = Room.query.all()
    for room in tmp:
        sub_res = {}
        sub_res['current_playing_video_ID'] = room.current_playing_video_ID
        sub_res['current_isplaying'] = room.current_isplaying
        sub_res['current_seek'] = room.current_seek
        sub_res['users'] = []
        for user in room.users:
            sub_res['users'].append(user.username)
        sub_res['Room secret'] = room.secret
        res[room.id] = sub_res
    return jsonify(res)
