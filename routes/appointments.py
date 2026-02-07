from flask import Blueprint, request, render_template, redirect, url_for, flash
from extensions import db
from models import Appointment, Patient, Consultation
from datetime import datetime, date

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('/today', methods=['GET'])
def today_appointments():
    """List all appointments scheduled for today"""
    today = date.today()
    
    appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_datetime) == today
    ).all()
    
    return render_template('appointments/today.html', appointments=appointments, today=today)

@appointments_bp.route('/create', methods=['GET', 'POST'])
def create_appointment():
    """Create a new appointment"""
    if request.method == 'POST':
        try:
            patient_id = request.form.get('patient_id', '')
            doctor_name = request.form.get('doctor_name', '').strip()
            appointment_datetime_str = request.form.get('appointment_datetime', '')
            
            # Validation
            if not patient_id or not patient_id.isdigit():
                flash('Valid patient selection is required', 'error')
                return redirect(url_for('appointments.create_appointment'))
            
            patient = Patient.query.get(int(patient_id))
            if not patient:
                flash('Patient not found', 'error')
                return redirect(url_for('appointments.create_appointment'))
            
            # Check if patient is active
            if patient.status != 'Active':
                flash('Cannot create appointment for inactive patient', 'error')
                return redirect(url_for('appointments.create_appointment'))
            
            if not doctor_name:
                flash('Doctor name is required', 'error')
                return redirect(url_for('appointments.create_appointment'))
            
            if not appointment_datetime_str:
                flash('Appointment date and time is required', 'error')
                return redirect(url_for('appointments.create_appointment'))
            
            try:
                appointment_datetime = datetime.fromisoformat(appointment_datetime_str)
            except ValueError:
                flash('Invalid date/time format', 'error')
                return redirect(url_for('appointments.create_appointment'))
            
            # Check if appointment is in the past
            if appointment_datetime < datetime.now():
                flash('Cannot create appointment in the past', 'error')
                return redirect(url_for('appointments.create_appointment'))
            
            # Create appointment
            appointment = Appointment(
                patient_id=int(patient_id),
                doctor_name=doctor_name,
                appointment_datetime=appointment_datetime,
                status='Scheduled'
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            flash(f'Appointment scheduled successfully for {patient.name}!', 'success')
            return redirect(url_for('appointments.today_appointments'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating appointment: {str(e)}', 'error')
            return redirect(url_for('appointments.create_appointment'))
    
    # Get active patients for dropdown
    active_patients = Patient.query.filter_by(status='Active').all()
    return render_template('appointments/create.html', patients=active_patients)

@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
def view_appointment(appointment_id):
    """View appointment details"""
    appointment = Appointment.query.get_or_404(appointment_id)
    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first()
    
    return render_template('appointments/view.html', appointment=appointment, consultation=consultation)

@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Check if appointment can be cancelled
        if appointment.status == 'Completed':
            flash('Cannot cancel a completed appointment', 'error')
            return redirect(url_for('appointments.view_appointment', appointment_id=appointment_id))
        
        appointment.status = 'Cancelled'
        db.session.commit()
        
        flash('Appointment cancelled successfully', 'success')
        return redirect(url_for('appointments.today_appointments'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling appointment: {str(e)}', 'error')
        return redirect(url_for('appointments.view_appointment', appointment_id=appointment_id))
