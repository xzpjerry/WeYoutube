#################
#### imports ####
#################
import random, uuid

import flask
from flask import render_template, redirect, flash, request, jsonify, abort
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
    username = data.get('owner_username', False)
    if username:
        target_user = User.query.filter_by(username = username).first()
        if target_user:
            code = 401
            res['success'] = False
            res['errors'] = ['This Username has been used; please try another one.']
        else:
            target_room = Room(secret = gen_4digits())
            newuser = User(username = username, room=target_room, room_id=target_room.id)
            target_room.owner_id = newuser.id
            target_room.owner = newuser

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
    username = data.get('guest_username', False)
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

@cinema_blueprint.route('/leave/<string:sid>', methods=('DELETE',))
@login_required
def leave(sid):
    if not sid == current_user.session_id:
        return jsonify({'success': False, 'errors': 'You are not that user!'}), 401
    target = User.query.filter_by(id=current_user.id).first()
    room_dismissed = False
    res = []
    if target.room.owner_id == target.id:
        room_dismissed = True
    else:
        room_obj = target.room
        res = [user.username for user in room_obj.users if not user.id == target.id]
    logout_user()
    db.session.delete(target)
    if room_dismissed:
        socketio.emit('room_dismissed', 'The room was closed.', room=target.room.id)
    else:
        socketio.emit('people_changed_response', str([res]), room=room_obj.id)
    db.session.commit()
    return jsonify({'success': True}), 200

@cinema_blueprint.route('/watch', methods=('GET', ))
@login_required
def watch():
    return render_template('cinema/watch.html')

@cinema_blueprint.route('/get_play_detail', methods=('GET', ))
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
    room_id = current_user.room.id
    join_room(room_id)
    session_id = request.sid
    room_obj = current_user.room
    current_user.session_id = session_id
    res = [user.username for user in room_obj.users]
    emit('people_changed_response', str(res), room=room_obj.id)
    emit('returning_sid', session_id, room=session_id)
    db.session.commit()

@socketio.on('player_state_changed')
def on_state_change(data):
    room_obj = current_user.room
    if request.sid == room_obj.owner.session_id:
        seek = data['seek']
        url = data['url']
        isPlaying = data['playing']
        vid = url[url.index('v=') + 2:]
        same_vid = room_obj.current_playing_video_ID == vid
        room_obj.current_playing_video_ID = vid
        room_obj.current_isplaying = isPlaying
        room_obj.current_seek = seek
        res = {
            'vid': vid,
            'playing': isPlaying,
            'seek': seek,
            'same_vid': same_vid,
        }
        emit('player_state_changed_response', res, room=room_obj.id)
        db.session.commit()

@socketio.on('disconnect')
def on_leave():
    session_id = request.sid
    target = User.query.filter_by(session_id = session_id).first()
    if target:
        if target.room.owner_id == target.id:
            db.session.delete(target.room)
            emit('room_dismissed', 'The room was closed.', room=target.room.id)
        else:
            room_obj = target.room
            res = [user.username for user in room_obj.users if not user.id == target.id]
            emit('people_changed_response', str({'usernames': res}), room=room_obj.id)
        db.session.delete(target)
        db.session.commit()

##############################
#### For Debuging Purpose ####
##############################
@cinema_blueprint.route('/getusers', methods=('GET', ))
def get_all_current_users():
    res = {}
    tmp = User.query.all()
    for user in tmp:
        sub_res = {}
        sub_res['id'] = user.id
        sub_res['session_id'] = user.session_id
        sub_res['username'] = user.username
        sub_res['room_id'] = user.room_id
        sub_res['owned_room_id'] = user.owned_room.id if user.owned_room else -1
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
        sub_res['owner'] = room.owner.username
        for user in room.users:
            sub_res['users'].append(user.username)
        sub_res['Room secret'] = room.secret
        res[room.id] = sub_res
    return jsonify(res)
