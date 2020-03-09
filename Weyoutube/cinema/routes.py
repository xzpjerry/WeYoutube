#################
#### imports ####
#################
import random

from flask import render_template, redirect, flash, request, jsonify
from flask_login import login_required, current_user, logout_user, login_user

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

@cinema_blueprint.route('/enter', methods=('POST',))
def enter_cinema():
    res = {}
    data = request.form
    username = data.get('username', False)
    room_id = data.get('room_id', False)
    secret = data.get('secret', False)
    if username and room_id and secret:
        room_id = int(room_id)
        secret = int(secret)
        target_user = User.query.filter_by(username = username).first()
        if target_user:
            res['success'] = False
            res['errors'] = ['This Username has been used; please try another one.']
        else:
            target_room = Room.query.filter_by(id = room_id).first()
            if not target_room:
                target_room = Room(secret = gen_4digits())
                db.session.add(target_room)
            elif not target_room.secret == secret:
                    res['success'] = False
                    res['errors'] = ['Invalid Secret.']
                    return jsonify(res)
            newuser = User(username = username, room=target_room)
            db.session.add(newuser)
            db.session.commit()
            login_user(newuser, remember=True)
            return redirect('/watch')
    else:
        res['success'] = False
        res['errors'] = ['You must filled out all values.']
    return jsonify(res)

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

@cinema_blueprint.route('/getusers', methods=('GET', ))
def get_all_current_user():
    res = {}
    tmp = User.query.all()
    for user in tmp:
        sub_res = {}
        sub_res['Room id'] = user.room.id
        sub_res['Room secret'] = user.room.secret
        res[user.username] = sub_res
    return jsonify(res)

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))