from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Patient, Doctor, Appointment, SOSAlert, OTTrainingMedia
from forms import LoginForm, RegisterForm, PatientForm, DoctorForm, AppointmentForm
import os
import math
import threading
import time
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024

# init extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

OT_MEDIA_DIR = os.path.join(app.instance_path, 'ot_media')
ALLOWED_OT_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
os.makedirs(OT_MEDIA_DIR, exist_ok=True)
DEFAULT_DOCTOR_IMAGE = 'https://images.unsplash.com/photo-1582750433449-648ed127bb54?auto=format&fit=crop&w=800&q=80'

HOSPITAL_DIRECTORY = [
    {
        'name': 'King George Hospital (KGH)',
        'phone': '0891-2564891',
        'emergency_phone': '108',
        'address': 'Maharanipeta',
        'city': 'Visakhapatnam',
        'state': 'Andhra Pradesh',
        'services': 'Emergency Medicine, Trauma Care, ICU, General Medicine',
        'availability': '24x7 Emergency',
        'ambulance_eta': '8-12 mins',
        'image_url': 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1600&q=80',
        'latitude': 17.7220,
        'longitude': 83.3150
    },
    {
        'name': 'RK Hospital',
        'phone': '0866-2488888',
        'emergency_phone': '108',
        'address': 'Ring Road',
        'city': 'Vijayawada',
        'state': 'Andhra Pradesh',
        'services': 'Emergency, Orthopedics, Surgery, Critical Care',
        'availability': '24x7 Emergency',
        'ambulance_eta': '10-15 mins',
        'image_url': 'https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=1600&q=80',
        'latitude': 16.5062,
        'longitude': 80.6480
    },
    {
        'name': 'KIMS Hospital',
        'phone': '040-44885000',
        'emergency_phone': '108',
        'address': 'Minister Road, Secunderabad',
        'city': 'Hyderabad',
        'state': 'Telangana',
        'services': 'Emergency, Cardiology, Neurology, Trauma ICU',
        'availability': '24x7 Emergency',
        'ambulance_eta': '7-11 mins',
        'image_url': 'https://images.unsplash.com/photo-1538108149393-fbbd81895907?auto=format&fit=crop&w=1600&q=80',
        'latitude': 17.4344,
        'longitude': 78.4962
    },
    {
        'name': 'Apollo Hospitals (Jubilee Hills)',
        'phone': '040-23607777',
        'emergency_phone': '108',
        'address': 'Jubilee Hills',
        'city': 'Hyderabad',
        'state': 'Telangana',
        'services': 'Emergency, Cardiac Care, Oncology, ICU',
        'availability': '24x7 Emergency',
        'ambulance_eta': '9-14 mins',
        'image_url': 'https://images.unsplash.com/photo-1586773860418-d37222d8fce3?auto=format&fit=crop&w=1600&q=80',
        'latitude': 17.4156,
        'longitude': 78.4347
    },
    {
        'name': 'Manipal Hospital (Old Airport Road)',
        'phone': '080-25024444',
        'emergency_phone': '108',
        'address': 'HAL Old Airport Road',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'services': 'Emergency, Cardiology, Neurology, Critical Care',
        'availability': '24x7 Emergency',
        'ambulance_eta': '7-11 mins',
        'image_url': 'https://images.unsplash.com/photo-1631815588090-d4bfec5b1ccb?auto=format&fit=crop&w=1600&q=80',
        'latitude': 12.9589,
        'longitude': 77.6481
    },
    {
        'name': 'CARE Hospitals (Banjara Hills)',
        'phone': '040-61656565',
        'emergency_phone': '108',
        'address': 'Banjara Hills',
        'city': 'Hyderabad',
        'state': 'Telangana',
        'services': 'Emergency, Cardiology, Trauma, Critical Care',
        'availability': '24x7 Emergency',
        'ambulance_eta': '10-16 mins',
        'image_url': 'https://images.unsplash.com/photo-1551190822-a9333d879b1f?auto=format&fit=crop&w=1600&q=80',
        'latitude': 17.4239,
        'longitude': 78.4431
    },
    {
        'name': 'Fortis Hospital (Bannerghatta Road)',
        'phone': '080-66214444',
        'emergency_phone': '108',
        'address': 'Bannerghatta Road',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'services': 'Emergency, Cardiology, Neuro Care, Trauma',
        'availability': '24x7 Emergency',
        'ambulance_eta': '8-13 mins',
        'image_url': 'https://images.unsplash.com/photo-1564732005956-20420ebdab60?auto=format&fit=crop&w=1600&q=80',
        'latitude': 12.8930,
        'longitude': 77.5976
    },
    {
        'name': 'Aster CMI Hospital',
        'phone': '080-43420100',
        'emergency_phone': '108',
        'address': 'Hebbal, Sahakara Nagar',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'services': 'Emergency, Organ Transplant, ICU, Trauma',
        'availability': '24x7 Emergency',
        'ambulance_eta': '9-15 mins',
        'image_url': 'https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=1600&q=80',
        'latitude': 13.0395,
        'longitude': 77.5916
    },
    {
        'name': 'Narayana Institute of Cardiac Sciences',
        'phone': '080-71222222',
        'emergency_phone': '108',
        'address': 'Narayana Health City, Bommasandra',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'services': 'Cardiac Emergency, ICU, Cardiology, Surgery',
        'availability': '24x7 Emergency',
        'ambulance_eta': '11-17 mins',
        'image_url': 'https://images.unsplash.com/photo-1530026405186-ed1f139313f8?auto=format&fit=crop&w=1600&q=80',
        'latitude': 12.8238,
        'longitude': 77.6882
    },
    {
        'name': 'M.S. Ramaiah Memorial Hospital',
        'phone': '080-23601742',
        'emergency_phone': '108',
        'address': 'New BEL Road, MSR Nagar',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'services': 'Emergency, Multi-speciality Care, ICU, Trauma',
        'availability': '24x7 Emergency',
        'ambulance_eta': '8-12 mins',
        'image_url': 'https://images.unsplash.com/photo-1504813184591-01572f98c85f?auto=format&fit=crop&w=1600&q=80',
        'latitude': 13.0301,
        'longitude': 77.5646
    }
]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def get_nearest_hospital(lat, lon):
    return min(
        HOSPITAL_DIRECTORY,
        key=lambda h: haversine_km(lat, lon, h['latitude'], h['longitude'])
    )


def has_role(*roles):
    if not current_user.is_authenticated:
        return False
    return (current_user.role or '').lower() in {r.lower() for r in roles}


def ensure_doctor_or_admin():
    if not has_role('doctor', 'admin'):
        flash('Doctor-only training module. Access denied.', 'danger')
        return False
    return True


def ensure_doctor_management_access():
    if not has_role('doctor', 'admin'):
        flash('Only doctor/admin can manage doctor details.', 'danger')
        return False
    return True


def compute_doctor_rating(doctor):
    exp = doctor.experience_years or 0
    has_qualification = bool((doctor.qualification or '').strip())
    has_specialization = bool((doctor.specialization or '').strip())
    has_problems = bool((doctor.problems_treated or '').strip())

    # Heuristic rating tuned to keep realistic display values.
    base = 3.9 + min(exp, 20) * 0.045
    if has_qualification:
        base += 0.15
    if has_specialization:
        base += 0.1
    if has_problems:
        base += 0.05

    return round(min(5.0, max(3.8, base)), 1)


def allowed_ot_file(filename):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_OT_IMAGE_EXTENSIONS


def upsert_patient_from_sos(payload):
    if not isinstance(payload, dict):
        return None

    name = (payload.get('name') or '').strip()
    phone = (payload.get('phone') or '').strip()
    gender = (payload.get('gender') or '').strip()
    address = (payload.get('address') or '').strip()
    raw_age = payload.get('age')

    if not name:
        return None

    age = None
    try:
        if raw_age is not None and str(raw_age).strip() != '':
            age = int(raw_age)
            if age < 0:
                age = None
    except (TypeError, ValueError):
        age = None

    patient = None
    if phone:
        patient = Patient.query.filter_by(phone=phone).first()
    if not patient:
        patient = Patient.query.filter(Patient.name.ilike(name)).first()

    if patient:
        patient.name = name
        if phone:
            patient.phone = phone
        if gender:
            patient.gender = gender
        if address:
            patient.address = address
        if age is not None:
            patient.age = age
    else:
        patient = Patient(
            name=name,
            age=age if age is not None else 0,
            gender=gender or None,
            phone=phone or None,
            address=address or None
        )
        db.session.add(patient)

    db.session.flush()
    return patient


def upsert_patient_from_appointment(name, phone, age=None, gender=None):
    safe_name = (name or '').strip()
    safe_phone = (phone or '').strip()
    safe_gender = (gender or '').strip()
    if not safe_name:
        return None

    parsed_age = None
    try:
        if age is not None and str(age).strip() != '':
            parsed_age = int(age)
            if parsed_age < 0:
                parsed_age = None
    except (TypeError, ValueError):
        parsed_age = None

    patient = None
    if safe_phone:
        patient = Patient.query.filter_by(phone=safe_phone).first()
    if not patient:
        patient = Patient.query.filter(Patient.name.ilike(safe_name)).first()

    if patient:
        patient.name = safe_name
        if safe_phone:
            patient.phone = safe_phone
        if parsed_age is not None:
            patient.age = parsed_age
        if safe_gender:
            patient.gender = safe_gender
    else:
        patient = Patient(
            name=safe_name,
            age=parsed_age if parsed_age is not None else 0,
            gender=safe_gender or None,
            phone=safe_phone or None,
            address=None
        )
        db.session.add(patient)

    db.session.flush()
    return patient


SUPPORTED_AI_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'te': 'Telugu',
    'ta': 'Tamil',
    'kn': 'Kannada',
    'mr': 'Marathi',
    'bn': 'Bengali',
}


def normalize_ai_language(lang_value):
    value = (lang_value or '').strip().lower()
    if not value:
        return ''
    if value in SUPPORTED_AI_LANGUAGES:
        return SUPPORTED_AI_LANGUAGES[value]
    for name in SUPPORTED_AI_LANGUAGES.values():
        if value == name.lower():
            return name
    return ''


def generate_ai_reply(user_query, response_language=None):
    query = (user_query or '').strip()
    if not query:
        return None, 'Please enter a message.'

    api_key = os.environ.get('OPENAI_API_KEY', '')
    model_name = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

    if not api_key:
        return None, 'OpenAI API key is missing. Set OPENAI_API_KEY in your environment or .env file.'
    if not OpenAI:
        return None, 'OpenAI package not available. Run: pip install -U openai'

    lang_hint = normalize_ai_language(response_language)
    language_instruction = (
        (
            f"Respond only in {lang_hint}. "
            "Do not switch to English unless the user explicitly asks for English."
        )
        if lang_hint
        else (
            "Detect the user's language and respond in that same language. "
            "If the user mixes languages, prefer the primary non-English language used."
        )
    )

    try:
        client = OpenAI(api_key=api_key)
        ai_resp = client.responses.create(
            model=model_name,
            input=[
                {
                    'role': 'system',
                    'content': (
                        'You are a hospital management assistant. '
                        'Give concise, practical answers for appointments, patient workflows, and emergencies. '
                        'For emergency questions, always prioritize ambulance activation and evidence-based first aid steps. '
                        'Ayurveda guidance must be supportive only after stabilization, not as emergency replacement. '
                        'Format all treatment guidance as numbered steps in plain text. '
                        'Use short, clear action lines that can be read aloud by voice assistants. '
                        f'{language_instruction}'
                    ),
                },
                {'role': 'user', 'content': query},
            ],
        )
        output_text = (getattr(ai_resp, 'output_text', '') or '').strip()
        if not output_text:
            return None, 'No response received from AI model.'
        return output_text, None
    except Exception as e:
        return None, f'AI error: {e}'


def process_sos_after_timeout(alert_id):
    time.sleep(10)
    with app.app_context():
        alert = SOSAlert.query.get(alert_id)
        if not alert:
            return
        # If patient has responded, treat as fake alert and do not dispatch.
        if alert.patient_responded_at:
            alert.status = 'fake_alert'
            alert.notes = 'Patient responded to verification message. Alert marked fake.'
            db.session.commit()
            return
        # No response within 10s => dispatch ambulance immediately.
        alert.status = 'ambulance_dispatched'
        alert.ambulance_dispatched_at = datetime.utcnow()
        alert.notes = f'Ambulance dispatched from {alert.hospital_name}.'
        db.session.commit()

# Create database tables when the app starts
with app.app_context():
    # create tables if missing
    db.create_all()
    # simple migration: add missing columns if they do not exist
    from sqlalchemy import text
    conn = db.engine.connect()
    inspector = db.inspect(db.engine)
    user_cols = [c['name'] for c in inspector.get_columns('user')]
    appointment_cols = [c['name'] for c in inspector.get_columns('appointment')]
    doctor_cols = [c['name'] for c in inspector.get_columns('doctor')] if inspector.has_table('doctor') else []
    try:
        if 'email' not in user_cols:
            conn.execute(text('ALTER TABLE user ADD COLUMN email VARCHAR(150);'))
        if 'client_id' not in user_cols:
            conn.execute(text('ALTER TABLE user ADD COLUMN client_id VARCHAR(36);'))
        if 'role' not in user_cols:
            conn.execute(text("ALTER TABLE user ADD COLUMN role VARCHAR(50) DEFAULT 'user';"))
        if 'patient_name' not in appointment_cols:
            conn.execute(text('ALTER TABLE appointment ADD COLUMN patient_name VARCHAR(150);'))
        if 'phone' not in appointment_cols:
            conn.execute(text('ALTER TABLE appointment ADD COLUMN phone VARCHAR(20);'))
        if inspector.has_table('doctor') and 'problems_treated' not in doctor_cols:
            conn.execute(text('ALTER TABLE doctor ADD COLUMN problems_treated VARCHAR(300);'))
        if inspector.has_table('doctor') and 'photo_url' not in doctor_cols:
            conn.execute(text('ALTER TABLE doctor ADD COLUMN photo_url VARCHAR(500);'))
    except Exception:
        pass
    finally:
        conn.close()

    # bootstrap one admin account if none exists
    try:
        admin_exists = User.query.filter(User.role == 'admin').first()
        if not admin_exists:
            first_user = User.query.order_by(User.id.asc()).first()
            if first_user:
                first_user.role = 'admin'
                db.session.commit()
    except Exception:
        db.session.rollback()

    # seed doctor directory and add missing default doctors by name
    try:
        seed_doctors_data = [
            {
                'name': 'Dr. Ananya Rao',
                'specialization': 'Cardiology',
                'problems_treated': 'Chest pain, high BP, palpitations, heart disease follow-up',
                'photo_url': 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=800&q=80',
                'qualification': 'MD, DM Cardiology',
                'experience_years': 12,
                'phone': '+91-90000-10001',
                'email': 'ananya.rao@hospital.local',
                'availability': 'Mon-Sat 10:00 AM - 4:00 PM'
            },
            {
                'name': 'Dr. Vikram Nair',
                'specialization': 'Neurology',
                'problems_treated': 'Headache, seizures, stroke recovery, nerve pain',
                'photo_url': 'https://commons.wikimedia.org/wiki/Special:FilePath/Doctor_examines_patient.jpg',
                'qualification': 'MD, DM Neurology',
                'experience_years': 10,
                'phone': '+91-90000-10002',
                'email': 'vikram.nair@hospital.local',
                'availability': 'Mon-Fri 11:00 AM - 5:00 PM'
            },
            {
                'name': 'Dr. Meera Iyer',
                'specialization': 'Orthopedics',
                'problems_treated': 'Fractures, joint pain, back pain, sports injuries',
                'photo_url': 'https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=800&q=80',
                'qualification': 'MS Orthopedics',
                'experience_years': 14,
                'phone': '+91-90000-10003',
                'email': 'meera.iyer@hospital.local',
                'availability': 'Mon-Sat 9:00 AM - 2:00 PM'
            },
            {
                'name': 'Dr. Arjun Patel',
                'specialization': 'General Surgery',
                'problems_treated': 'Appendix pain, hernia, wound care, emergency surgical consult',
                'photo_url': 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=800&q=80',
                'qualification': 'MS General Surgery',
                'experience_years': 11,
                'phone': '+91-90000-10004',
                'email': 'arjun.patel@hospital.local',
                'availability': 'Mon-Fri 8:00 AM - 2:00 PM'
            },
            {
                'name': 'Dr. Kavya Menon',
                'specialization': 'Dermatology',
                'problems_treated': 'Skin rashes, acne, eczema, fungal infections',
                'photo_url': 'https://images.unsplash.com/photo-1651008376811-b90baee60c1f?auto=format&fit=crop&w=800&q=80',
                'qualification': 'MD Dermatology',
                'experience_years': 9,
                'phone': '+91-90000-10005',
                'email': 'kavya.menon@hospital.local',
                'availability': 'Tue-Sun 1:00 PM - 7:00 PM'
            },
            {
                'name': 'Dr. Rahul Sharma',
                'specialization': 'Pediatrics',
                'problems_treated': 'Fever in children, cough/cold, growth monitoring, vaccinations',
                'photo_url': 'https://images.unsplash.com/photo-1582750433449-648ed127bb54?auto=format&fit=crop&w=800&q=80',
                'qualification': 'MD Pediatrics',
                'experience_years': 13,
                'phone': '+91-90000-10006',
                'email': 'rahul.sharma@hospital.local',
                'availability': 'Mon-Sat 10:00 AM - 6:00 PM'
            },
            {
                'name': 'Dr. Sneha Kulkarni',
                'specialization': 'Gynecology',
                'problems_treated': 'Pregnancy care, menstrual issues, PCOS, women health checkups',
                'photo_url': 'https://images.unsplash.com/photo-1551601651-2a8555f1a136?auto=format&fit=crop&w=800&q=80',
                'qualification': 'MS Obstetrics & Gynecology',
                'experience_years': 15,
                'phone': '+91-90000-10007',
                'email': 'sneha.kulkarni@hospital.local',
                'availability': 'Mon-Fri 9:30 AM - 3:30 PM'
            },
            {
                'name': 'Dr. Imran Khan',
                'specialization': 'ENT',
                'problems_treated': 'Ear pain, sinus issues, throat infection, hearing problems',
                'photo_url': 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=800&q=80',
                'qualification': 'MS ENT',
                'experience_years': 8,
                'phone': '+91-90000-10008',
                'email': 'imran.khan@hospital.local',
                'availability': 'Mon-Sat 12:00 PM - 6:00 PM'
            },
            {
                'name': 'Dr. Priya Desai',
                'specialization': 'Endocrinology',
                'problems_treated': 'Diabetes, thyroid disorders, hormonal imbalance',
                'photo_url': 'https://randomuser.me/api/portraits/women/68.jpg',
                'qualification': 'MD, DM Endocrinology',
                'experience_years': 10,
                'phone': '+91-90000-10009',
                'email': 'priya.desai@hospital.local',
                'availability': 'Mon-Fri 10:00 AM - 5:00 PM'
            },
            {
                'name': 'Dr. Neel Varma',
                'specialization': 'Pulmonology',
                'problems_treated': 'Asthma, COPD, lung infection, sleep apnea',
                'photo_url': 'https://randomuser.me/api/portraits/men/52.jpg',
                'qualification': 'MD Pulmonology',
                'experience_years': 9,
                'phone': '+91-90000-10010',
                'email': 'neel.varma@hospital.local',
                'availability': 'Mon-Sat 11:00 AM - 6:00 PM'
            },
            {
                'name': 'Dr. Aditi Joshi',
                'specialization': 'Ophthalmology',
                'problems_treated': 'Blurred vision, cataract consult, eye infections, glaucoma screening',
                'photo_url': 'https://randomuser.me/api/portraits/women/44.jpg',
                'qualification': 'MS Ophthalmology',
                'experience_years': 11,
                'phone': '+91-90000-10011',
                'email': 'aditi.joshi@hospital.local',
                'availability': 'Tue-Sun 9:00 AM - 2:00 PM'
            },
            {
                'name': 'Dr. Harish Reddy',
                'specialization': 'Urology',
                'problems_treated': 'Kidney stones, urinary infection, prostate issues',
                'photo_url': 'https://randomuser.me/api/portraits/men/46.jpg',
                'qualification': 'MS, MCh Urology',
                'experience_years': 12,
                'phone': '+91-90000-10012',
                'email': 'harish.reddy@hospital.local',
                'availability': 'Mon-Fri 2:00 PM - 8:00 PM'
            },
            {
                'name': 'Dr. Pooja Bhat',
                'specialization': 'Psychiatry',
                'problems_treated': 'Anxiety, depression, sleep problems, stress counseling',
                'photo_url': 'https://randomuser.me/api/portraits/women/63.jpg',
                'qualification': 'MD Psychiatry',
                'experience_years': 8,
                'phone': '+91-90000-10013',
                'email': 'pooja.bhat@hospital.local',
                'availability': 'Mon-Sat 3:00 PM - 8:00 PM'
            },
            {
                'name': 'Dr. Karan Malhotra',
                'specialization': 'Oncology',
                'problems_treated': 'Cancer screening, chemotherapy follow-up, pain management',
                'photo_url': 'https://randomuser.me/api/portraits/men/41.jpg',
                'qualification': 'MD, DM Oncology',
                'experience_years': 13,
                'phone': '+91-90000-10014',
                'email': 'karan.malhotra@hospital.local',
                'availability': 'Mon-Fri 10:30 AM - 4:30 PM'
            }
        ]

        existing_names = {(d.name or '').strip().lower() for d in Doctor.query.all()}
        to_add = [Doctor(**d) for d in seed_doctors_data if d['name'].strip().lower() not in existing_names]
        if to_add:
            db.session.add_all(to_add)
            db.session.commit()
    except Exception:
        db.session.rollback()

    # backfill image URLs for existing doctor rows if missing
    try:
        default_images = {
            'dr. ananya rao': 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=800&q=80',
            'dr. vikram nair': 'https://commons.wikimedia.org/wiki/Special:FilePath/Doctor_examines_patient.jpg',
            'dr. meera iyer': 'https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=800&q=80',
            'dr. arjun patel': 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=800&q=80',
            'dr. kavya menon': 'https://images.unsplash.com/photo-1651008376811-b90baee60c1f?auto=format&fit=crop&w=800&q=80',
            'dr. rahul sharma': 'https://images.unsplash.com/photo-1582750433449-648ed127bb54?auto=format&fit=crop&w=800&q=80',
            'dr. sneha kulkarni': 'https://images.unsplash.com/photo-1551601651-2a8555f1a136?auto=format&fit=crop&w=800&q=80',
            'dr. imran khan': 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=800&q=80',
            'dr. priya desai': 'https://randomuser.me/api/portraits/women/68.jpg',
            'dr. neel varma': 'https://randomuser.me/api/portraits/men/52.jpg',
            'dr. aditi joshi': 'https://randomuser.me/api/portraits/women/44.jpg',
            'dr. harish reddy': 'https://randomuser.me/api/portraits/men/46.jpg',
            'dr. pooja bhat': 'https://randomuser.me/api/portraits/women/63.jpg',
            'dr. karan malhotra': 'https://randomuser.me/api/portraits/men/41.jpg'
        }
        changed = False
        for d in Doctor.query.all():
            key = (d.name or '').strip().lower()
            mapped_image = default_images.get(key)
            if mapped_image:
                # Keep default seed doctors in sync with curated image map.
                if d.photo_url != mapped_image:
                    d.photo_url = mapped_image
                    changed = True
            elif not d.photo_url:
                d.photo_url = DEFAULT_DOCTOR_IMAGE
                changed = True
        if changed:
            db.session.commit()
    except Exception:
        db.session.rollback()

@app.route('/')
def index():
    doctors_preview = Doctor.query.order_by(Doctor.id.desc()).limit(6).all()
    return render_template('index.html', doctors_preview=doctors_preview)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        ident = form.identifier.data
        try:
            # try username first, then email
            user = User.query.filter((User.username == ident) | (User.email == ident)).first()
        except Exception as e:
            from sqlalchemy.exc import OperationalError
            if isinstance(e, OperationalError):
                # attempt migration then retry once
                with app.app_context():
                    from sqlalchemy import text
                    conn = db.engine.connect()
                    cols = [c['name'] for c in db.inspect(db.engine).get_columns('user')]
                    try:
                        if 'email' not in cols:
                            conn.execute(text('ALTER TABLE user ADD COLUMN email VARCHAR(150);'))
                        if 'client_id' not in cols:
                            conn.execute(text('ALTER TABLE user ADD COLUMN client_id VARCHAR(36);'))
                        if 'role' not in cols:
                            conn.execute(text("ALTER TABLE user ADD COLUMN role VARCHAR(50) DEFAULT 'user';"))
                    except Exception:
                        pass
                    finally:
                        conn.close()
                user = User.query.filter((User.username == ident) | (User.email == ident)).first()
            else:
                raise
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # ensure username/email unique
        existing = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        if existing:
            flash('Username or email already in use.', 'danger')
        else:
            hashed = generate_password_hash(form.password.data)
            user = User(username=form.username.data, email=form.email.data, password=hashed)
            db.session.add(user)
            db.session.commit()
            flash(f'Registration successful. Your client ID is {user.client_id}', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    hospitals_preview = HOSPITAL_DIRECTORY[:3]
    return render_template('dashboard.html', hospitals_preview=hospitals_preview)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# patient routes
@app.route('/patients')
@login_required
def patients():
    name = request.args.get('name', '').strip()
    if name:
        all_patients = Patient.query.filter(Patient.name.ilike(f"%{name}%")).order_by(Patient.id.desc()).all()
    else:
        all_patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template('patients.html', patients=all_patients, filter_name=name)

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(
            name=form.name.data,
            age=form.age.data,
            gender=form.gender.data,
            phone=form.phone.data,
            address=form.address.data
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient added', 'success')
        return redirect(url_for('patients'))
    return render_template('add_patient.html', form=form)

@app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        patient.name = form.name.data
        patient.age = form.age.data
        patient.gender = form.gender.data
        patient.phone = form.phone.data
        patient.address = form.address.data
        try:
            db.session.commit()
            flash('Patient updated successfully.', 'success')
            return redirect(url_for('patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating patient: {e}', 'danger')
    return render_template('edit_patient.html', form=form, patient=patient)

@app.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    try:
        # Keep historical appointment records even if patient profile is deleted.
        Appointment.query.filter_by(patient_id=patient.id).update({'patient_id': None})
        db.session.delete(patient)
        db.session.commit()
        flash('Patient deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting patient: {e}', 'danger')
    return redirect(url_for('patients'))


# doctor routes
@app.route('/doctors')
def doctors():
    name = request.args.get('name', '').strip()
    problem = request.args.get('problem', '').strip()
    base_query = Doctor.query
    if name:
        base_query = base_query.filter(Doctor.name.ilike(f"%{name}%"))
    if problem:
        base_query = base_query.filter(
            (Doctor.specialization.ilike(f"%{problem}%")) |
            (Doctor.problems_treated.ilike(f"%{problem}%"))
        )
    all_doctors = base_query.order_by(Doctor.id.desc()).all()
    ratings = {d.id: compute_doctor_rating(d) for d in all_doctors}
    can_manage = has_role('doctor', 'admin')
    return render_template(
        'doctors.html',
        doctors=all_doctors,
        ratings=ratings,
        filter_name=name,
        filter_problem=problem,
        can_manage=can_manage
    )


@app.route('/doctors/add', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if not ensure_doctor_management_access():
        return redirect(url_for('doctors'))
    form = DoctorForm()
    if form.validate_on_submit():
        doctor = Doctor(
            name=form.name.data,
            specialization=form.specialization.data,
            problems_treated=form.problems_treated.data,
            photo_url=form.photo_url.data,
            qualification=form.qualification.data,
            experience_years=form.experience_years.data,
            phone=form.phone.data,
            email=form.email.data,
            availability=form.availability.data
        )
        db.session.add(doctor)
        db.session.commit()
        flash('Doctor details added.', 'success')
        return redirect(url_for('doctors'))
    return render_template('add_doctor.html', form=form)


@app.route('/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if not ensure_doctor_management_access():
        return redirect(url_for('doctors'))
    doctor = Doctor.query.get_or_404(doctor_id)
    form = DoctorForm(obj=doctor)
    if form.validate_on_submit():
        doctor.name = form.name.data
        doctor.specialization = form.specialization.data
        doctor.problems_treated = form.problems_treated.data
        doctor.photo_url = form.photo_url.data
        doctor.qualification = form.qualification.data
        doctor.experience_years = form.experience_years.data
        doctor.phone = form.phone.data
        doctor.email = form.email.data
        doctor.availability = form.availability.data
        try:
            db.session.commit()
            flash('Doctor details updated.', 'success')
            return redirect(url_for('doctors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating doctor: {e}', 'danger')
    return render_template('edit_doctor.html', form=form, doctor=doctor)


@app.route('/doctors/<int:doctor_id>/delete', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    if not ensure_doctor_management_access():
        return redirect(url_for('doctors'))
    doctor = Doctor.query.get_or_404(doctor_id)
    try:
        db.session.delete(doctor)
        db.session.commit()
        flash('Doctor removed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing doctor: {e}', 'danger')
    return redirect(url_for('doctors'))

# appointment routes
@app.route('/appointments')
@login_required
def appointments():
    # optional name filter from query string
    name = request.args.get('name', '').strip()
    base_query = Appointment.query.outerjoin(Patient)
    if name:
        all_appointments = base_query.filter(
            (Appointment.patient_name.ilike(f"%{name}%")) | (Patient.name.ilike(f"%{name}%"))
        ).order_by(Appointment.date.desc()).all()
    else:
        all_appointments = base_query.order_by(Appointment.date.desc()).all()
    return render_template('appointments.html', appointments=all_appointments, filter_name=name)

@app.route('/appointments/schedule', methods=['GET', 'POST'])
@login_required
def schedule_appointment():
    form = AppointmentForm()
    if form.validate_on_submit():
        dt = form.date.data
        # check if slot already taken
        existing = Appointment.query.filter_by(date=dt).first()
        if existing:
            flash('Appointment slot is already filled. Please choose another time.', 'warning')
            return render_template('schedule_appointment.html', form=form)

        entered_name = (form.patient_name.data or '').strip()
        entered_phone = (form.phone.data or '').strip()
        entered_age = form.age.data
        entered_gender = (form.gender.data or '').strip()
        matched_patient = upsert_patient_from_appointment(entered_name, entered_phone, entered_age, entered_gender)

        appt = Appointment(
            patient_id=matched_patient.id if matched_patient else None,
            patient_name=entered_name,
            phone=entered_phone,
            date=dt,
            reason=form.reason.data
        )
        try:
            db.session.add(appt)
            db.session.commit()
            flash('Appointment scheduled', 'success')
            return redirect(url_for('appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error scheduling appointment: {e}', 'danger')
    else:
        # if POST and not valid, show errors
        if form.errors:
            for field, errs in form.errors.items():
                for err in errs:
                    flash(f'{field}: {err}', 'danger')
    return render_template('schedule_appointment.html', form=form)

@app.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    form = AppointmentForm(obj=appointment)
    if request.method == 'GET' and appointment.patient:
        if appointment.patient.age is not None and appointment.patient.age > 0:
            form.age.data = appointment.patient.age
        form.gender.data = appointment.patient.gender or ''
    if form.validate_on_submit():
        dt = form.date.data
        existing = Appointment.query.filter(
            Appointment.date == dt,
            Appointment.id != appointment.id
        ).first()
        if existing:
            flash('Appointment slot is already filled. Please choose another time.', 'warning')
            return render_template('edit_appointment.html', form=form, appointment=appointment)

        entered_name = (form.patient_name.data or '').strip()
        entered_phone = (form.phone.data or '').strip()
        entered_age = form.age.data
        entered_gender = (form.gender.data or '').strip()
        matched_patient = upsert_patient_from_appointment(entered_name, entered_phone, entered_age, entered_gender)

        appointment.patient_id = matched_patient.id if matched_patient else None
        appointment.patient_name = entered_name
        appointment.phone = entered_phone
        appointment.date = dt
        appointment.reason = form.reason.data
        try:
            db.session.commit()
            flash('Appointment updated successfully.', 'success')
            return redirect(url_for('appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating appointment: {e}', 'danger')
    return render_template('edit_appointment.html', form=form, appointment=appointment)

@app.route('/appointments/<int:appointment_id>/delete', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    try:
        db.session.delete(appointment)
        db.session.commit()
        flash('Appointment deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting appointment: {e}', 'danger')
    return redirect(url_for('appointments'))

# Simple SOS page returning nearby hospitals
@app.route('/sos', methods=['GET'])
@login_required
def sos():
    hospitals = HOSPITAL_DIRECTORY
    return render_template('sos.html', hospitals=hospitals)


@app.route('/hospitals', methods=['GET'])
def hospitals():
    hospital_list = sorted(HOSPITAL_DIRECTORY, key=lambda h: h.get('name', ''))
    return render_template('hospitals.html', hospitals=hospital_list)


@app.route('/emergency-guide', methods=['GET'])
@login_required
def emergency_guide():
    return render_template('emergency_guide.html')


@app.route('/ot-training', methods=['GET'])
@login_required
def ot_training():
    if not ensure_doctor_or_admin():
        return redirect(url_for('dashboard'))

    if has_role('admin'):
        media_items = OTTrainingMedia.query.order_by(OTTrainingMedia.created_at.desc()).all()
    else:
        media_items = OTTrainingMedia.query.filter(
            (OTTrainingMedia.status == 'approved') | (OTTrainingMedia.uploader_id == current_user.id)
        ).order_by(OTTrainingMedia.created_at.desc()).all()

    return render_template(
        'ot_training.html',
        media_items=media_items,
        is_admin=has_role('admin')
    )


@app.route('/ot-training/upload', methods=['POST'])
@login_required
def ot_training_upload():
    if not ensure_doctor_or_admin():
        return redirect(url_for('dashboard'))

    procedure_title = (request.form.get('procedure_title') or '').strip()
    treatment_step = (request.form.get('treatment_step') or '').strip()
    notes = (request.form.get('notes') or '').strip()
    consent_confirmed = request.form.get('consent_confirmed') == 'on'
    anonymized_confirmed = request.form.get('anonymized_confirmed') == 'on'
    file_obj = request.files.get('media_file')

    if not procedure_title or not treatment_step:
        flash('Procedure title and treatment step are required.', 'danger')
        return redirect(url_for('ot_training'))
    if not consent_confirmed or not anonymized_confirmed:
        flash('Consent and anonymization confirmations are mandatory.', 'danger')
        return redirect(url_for('ot_training'))
    if not file_obj or not file_obj.filename:
        flash('Please attach an image file.', 'danger')
        return redirect(url_for('ot_training'))
    if not allowed_ot_file(file_obj.filename):
        flash('Invalid file type. Allowed: jpg, jpeg, png, webp.', 'danger')
        return redirect(url_for('ot_training'))

    original_name = secure_filename(file_obj.filename)
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    save_path = os.path.join(OT_MEDIA_DIR, stored_name)
    file_obj.save(save_path)

    record = OTTrainingMedia(
        procedure_title=procedure_title,
        treatment_step=treatment_step,
        notes=notes or None,
        stored_filename=stored_name,
        original_filename=original_name,
        mime_type=file_obj.mimetype,
        status='pending',
        consent_confirmed=True,
        anonymized_confirmed=True,
        uploader_id=current_user.id
    )
    db.session.add(record)
    db.session.commit()
    flash('OT training image uploaded and sent for admin approval.', 'success')
    return redirect(url_for('ot_training'))


@app.route('/ot-training/<int:media_id>/review', methods=['POST'])
@login_required
def ot_training_review(media_id):
    if not has_role('admin'):
        abort(403)

    record = OTTrainingMedia.query.get_or_404(media_id)
    action = (request.form.get('action') or '').strip().lower()
    review_notes = (request.form.get('review_notes') or '').strip()

    if action not in {'approve', 'reject'}:
        flash('Invalid review action.', 'danger')
        return redirect(url_for('ot_training'))

    record.status = 'approved' if action == 'approve' else 'rejected'
    record.reviewed_by_id = current_user.id
    record.reviewed_at = datetime.utcnow()
    record.review_notes = review_notes or None
    db.session.commit()

    flash(f'Item {record.id} marked as {record.status}.', 'success')
    return redirect(url_for('ot_training'))


@app.route('/ot-training/media/<int:media_id>', methods=['GET'])
@login_required
def ot_training_media(media_id):
    record = OTTrainingMedia.query.get_or_404(media_id)
    if not has_role('doctor', 'admin'):
        abort(403)

    if record.status != 'approved' and not has_role('admin') and record.uploader_id != current_user.id:
        abort(403)

    return send_from_directory(OT_MEDIA_DIR, record.stored_filename)

# API to receive location data from frontend
@app.route('/api/sos', methods=['POST'])
@login_required
def api_sos():
    data = request.json or {}
    try:
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid location'}), 400

    # Prevent accidental double-submit of SOS in a short window.
    recent_active = SOSAlert.query.filter(
        SOSAlert.user_id == current_user.id,
        SOSAlert.status == 'awaiting_patient_response',
        SOSAlert.created_at >= datetime.utcnow() - timedelta(seconds=20)
    ).order_by(SOSAlert.id.desc()).first()
    if recent_active:
        return jsonify({
            'status': recent_active.status,
            'alert_id': recent_active.id,
            'hospital_name': recent_active.hospital_name,
            'hospital_phone': recent_active.hospital_phone,
            'verification_seconds': max(0, int((recent_active.verification_deadline - datetime.utcnow()).total_seconds())) if recent_active.verification_deadline else 0,
            'patient_saved': False,
            'patient_id': None,
            'message': 'SOS already active. Continuing existing alert.'
        }), 200

    sos_patient = upsert_patient_from_sos(data.get('patient') or {})

    nearest = get_nearest_hospital(lat, lon)
    alert = SOSAlert(
        user_id=current_user.id,
        latitude=lat,
        longitude=lon,
        status='awaiting_patient_response',
        hospital_name=nearest['name'],
        hospital_phone=nearest['phone'],
        patient_message_sent_at=datetime.utcnow(),
        verification_deadline=datetime.utcnow() + timedelta(seconds=10),
        notes='Verification message sent to patient. Waiting for 10 seconds.'
    )
    db.session.add(alert)
    db.session.commit()

    t = threading.Thread(target=process_sos_after_timeout, args=(alert.id,), daemon=True)
    t.start()

    return jsonify({
        'status': alert.status,
        'alert_id': alert.id,
        'hospital_name': alert.hospital_name,
        'hospital_phone': alert.hospital_phone,
        'verification_seconds': 10,
        'patient_saved': bool(sos_patient),
        'patient_id': sos_patient.id if sos_patient else None,
        'message': 'Verification message sent. If no response in 10 seconds, ambulance will be dispatched.'
    })


@app.route('/api/sos/respond', methods=['POST'])
@login_required
def api_sos_respond():
    data = request.json or {}
    alert_id = data.get('alert_id')
    if not alert_id:
        return jsonify({'status': 'error', 'message': 'alert_id is required'}), 400

    alert = SOSAlert.query.get(alert_id)
    if not alert or alert.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Alert not found'}), 404

    if alert.status == 'ambulance_dispatched':
        return jsonify({'status': alert.status, 'message': 'Ambulance already dispatched.'}), 409

    alert.patient_responded_at = datetime.utcnow()
    alert.status = 'fake_alert'
    alert.notes = 'Patient responded to verification. Treated as fake alert.'
    db.session.commit()
    return jsonify({'status': alert.status, 'message': 'Alert marked as fake based on patient response.'})


@app.route('/api/sos/location', methods=['POST'])
@login_required
def api_sos_location_update():
    data = request.json or {}
    alert_id = data.get('alert_id')
    if not alert_id:
        return jsonify({'status': 'error', 'message': 'alert_id is required'}), 400

    try:
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid location'}), 400

    alert = SOSAlert.query.get(alert_id)
    if not alert or alert.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Alert not found'}), 404

    if alert.status == 'fake_alert':
        return jsonify({'status': alert.status, 'message': 'Alert already closed.'}), 409

    nearest = get_nearest_hospital(lat, lon)
    alert.latitude = lat
    alert.longitude = lon
    alert.hospital_name = nearest['name']
    alert.hospital_phone = nearest['phone']
    db.session.commit()

    return jsonify({
        'status': alert.status,
        'alert_id': alert.id,
        'hospital_name': alert.hospital_name,
        'hospital_phone': alert.hospital_phone,
        'message': 'SOS location refreshed.'
    })


@app.route('/api/sos/status/<int:alert_id>', methods=['GET'])
@login_required
def api_sos_status(alert_id):
    alert = SOSAlert.query.get_or_404(alert_id)
    if alert.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Not allowed'}), 403

    remaining = 0
    if alert.verification_deadline and alert.status == 'awaiting_patient_response':
        remaining = max(0, int((alert.verification_deadline - datetime.utcnow()).total_seconds()))

    return jsonify({
        'status': alert.status,
        'alert_id': alert.id,
        'hospital_name': alert.hospital_name,
        'hospital_phone': alert.hospital_phone,
        'remaining_seconds': remaining,
        'notes': alert.notes
    })

# AI chat page
@app.route('/ai', methods=['GET'])
@login_required
def ai_chat():
    has_api_key = bool(os.environ.get('OPENAI_API_KEY', '').strip())
    return render_template('ai_chat.html', has_api_key=has_api_key)


@app.route('/api/ai/chat', methods=['POST'])
@login_required
def api_ai_chat():
    data = request.json or {}
    query = (data.get('query') or '').strip()
    response_language = normalize_ai_language(data.get('language'))
    response_text, error = generate_ai_reply(query, response_language=response_language)
    if error:
        return jsonify({'ok': False, 'error': error}), 400
    return jsonify({'ok': True, 'response': response_text})

if __name__ == '__main__':
    app.run(debug=True)
