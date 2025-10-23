from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(64))
    image_path = db.Column(db.String(256))
    segmented_path = db.Column(db.String(256))
    label = db.Column(db.String(32))
    confidence = db.Column(db.Float)
    vision_conf = db.Column(db.Float)
    temp = db.Column(db.Float)
    humidity = db.Column(db.Float)
    moisture = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)