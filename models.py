from extensions import db
from datetime import datetime


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="patient", lazy=True)
    consultations = db.relationship("Consultation", backref="patient", lazy=True)

    def __repr__(self):
        return f"<Patient {self.name}>"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_name = db.Column(db.String(100))
    appointment_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="Scheduled")

    consultation = db.relationship("Consultation", backref="appointment", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Appointment {self.id} - {self.status}>"


class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)

    vitals = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="Draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Consultation {self.id} - {self.status}>"
