from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    IntegerField,
    TextAreaField,
)
from wtforms.fields.datetime import DateTimeLocalField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Optional, NumberRange

class LoginForm(FlaskForm):
    identifier = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class PatientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender = SelectField('Gender', choices=[('Male','Male'),('Female','Female'),('Other','Other')])
    phone = StringField('Phone')
    address = TextAreaField('Address')
    submit = SubmitField('Save')

class AppointmentForm(FlaskForm):
    patient_name = StringField('Patient Name', validators=[DataRequired(), Length(min=2, max=150)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=7, max=20)])
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=0, max=120)])
    gender = SelectField('Gender', choices=[('', 'Select'), ('Male','Male'),('Female','Female'),('Other','Other')], validators=[Optional()])
    date = DateTimeLocalField('Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    reason = TextAreaField('Reason')
    submit = SubmitField('Schedule')


class DoctorForm(FlaskForm):
    name = StringField('Doctor Name', validators=[DataRequired(), Length(min=2, max=150)])
    specialization = StringField('Specialization', validators=[DataRequired(), Length(min=2, max=120)])
    problems_treated = StringField('Problems Treated', validators=[Optional(), Length(max=300)])
    photo_url = StringField('Photo URL', validators=[Optional(), Length(max=500)])
    qualification = StringField('Qualification', validators=[Optional(), Length(max=150)])
    experience_years = IntegerField('Experience (Years)', validators=[Optional(), NumberRange(min=0, max=70)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=150)])
    availability = StringField('Availability', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Save')
