from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# initialize elsewhere
db = SQLAlchemy()

import uuid

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    client_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='user')

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    problems_treated = db.Column(db.String(300), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    qualification = db.Column(db.String(150), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    availability = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))


class SOSAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='awaiting_patient_response')
    hospital_name = db.Column(db.String(150))
    hospital_phone = db.Column(db.String(20))
    patient_message_sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_deadline = db.Column(db.DateTime)
    patient_responded_at = db.Column(db.DateTime, nullable=True)
    ambulance_dispatched_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OTTrainingMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    procedure_title = db.Column(db.String(200), nullable=False)
    treatment_step = db.Column(db.String(300), nullable=False)
    notes = db.Column(db.String(500), nullable=True)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending|approved|rejected
    consent_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    anonymized_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
