from flask_login import UserMixin
from Weyoutube import db
import datetime

class Room(db.Model):
    '''
    self.id : int
    self.user : User
    '''
    id = db.Column(db.Integer, primary_key = True)
    secret = db.Column(db.SmallInteger)
    current_playing_video_ID = db.Column(db.String(24), default = 'QaQdY7iI75c')
    current_isplaying = db.Column(db.Boolean, default = False)
    current_seek = db.Column(db.Float, default=10.0)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    owner = db.relationship('User', foreign_keys=owner_id, backref = db.backref('owned_room', lazy = True, uselist = False), cascade="delete")
    
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def delete_expired(cls):
        expiration_days = 1
        limit = datetime.datetime.now() - datetime.timedelta(days=expiration_days)
        cls.query.filter(cls.timestamp <= limit).delete()
        db.session.commit()

    def __repr__(self):
        return 'Resume ' + str(self.id)

class User(UserMixin, db.Model):
    '''
    self.id : int
    self.userName : str
    self.credentials : str
    self.resume : Resume
    '''
    id = db.Column(db.Integer, primary_key = True)
    session_id = db.Column(db.String(32), unique = True)
    username = db.Column(db.String(32), unique = True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), default=-1)
    room = db.relationship('Room', foreign_keys=room_id, backref = db.backref('users', lazy = True), post_update=True)
    def __repr__(self):
        return 'User ' + str(self.id) 