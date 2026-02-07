from flask import Blueprint, request, render_template, redirect, url_for, flash
from extensions import db
from models import Consultation, Appointment, Patient
from datetime import datetime

consultations_bp = Blueprint('consultations', __name__, url_prefix='/consultations')

@consultations_bp.route('/new/<int:appointment_id>', methods=['GET', 'POST'])
def create_consultation(appointment_id):
    """Create a new consultation for an appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    patient = Patient.query.get(appointment.patient_id)
    
    # Check if appointment status is Scheduled
    if appointment.status != 'Scheduled':
        flash('Consultation can only be created for scheduled appointments', 'error')
        return redirect(url_for('appointments.view_appointment', appointment_id=appointment_id))
    
    # Check if consultation already exists
    existing_consultation = Consultation.query.filter_by(appointment_id=appointment_id).first()
    if existing_consultation:
        flash('A consultation already exists for this appointment', 'error')
        return redirect(url_for('appointments.view_appointment', appointment_id=appointment_id))
    
    if request.method == 'POST':
        try:
            vitals = request.form.get('vitals', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validation
            if not vitals:
                flash('Vitals information is required', 'error')
                return redirect(url_for('consultations.create_consultation', appointment_id=appointment_id))
            
            # Create consultation (always starts in Draft)
            consultation = Consultation(
                appointment_id=appointment_id,
                patient_id=appointment.patient_id,
                vitals=vitals,
                notes=notes,
                status='Draft',
                created_at=datetime.utcnow()
            )
            
            db.session.add(consultation)
            db.session.commit()
            
            flash('Consultation created successfully in Draft status', 'success')
            return redirect(url_for('consultations.view_consultation', consultation_id=consultation.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating consultation: {str(e)}', 'error')
            return redirect(url_for('consultations.create_consultation', appointment_id=appointment_id))
    
    return render_template('consultations/create.html', appointment=appointment, patient=patient)

@consultations_bp.route('/<int:consultation_id>', methods=['GET'])
def view_consultation(consultation_id):
    """View consultation details"""
    consultation = Consultation.query.get_or_404(consultation_id)
    appointment = Appointment.query.get(consultation.appointment_id)
    patient = Patient.query.get(consultation.patient_id)
    
    return render_template('consultations/view.html', consultation=consultation, appointment=appointment, patient=patient)

@consultations_bp.route('/<int:consultation_id>/complete', methods=['POST'])
def complete_consultation(consultation_id):
    """Mark consultation as completed and update appointment status"""
    try:
        consultation = Consultation.query.get_or_404(consultation_id)
        appointment = Appointment.query.get(consultation.appointment_id)
        
        # Check if consultation is already completed
        if consultation.status == 'Completed':
            flash('Consultation is already completed', 'error')
            return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))
        
        # Update consultation status to Completed
        consultation.status = 'Completed'
        
        # Update appointment status to Completed (business rule)
        appointment.status = 'Completed'
        
        db.session.commit()
        
        flash('Consultation marked as completed and appointment updated', 'success')
        return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error completing consultation: {str(e)}', 'error')
        return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))

@consultations_bp.route('/patient/<int:patient_id>', methods=['GET'])
def patient_consultations(patient_id):
    """View all completed consultations for a patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Get all completed consultations for this patient
    consultations = Consultation.query.filter_by(
        patient_id=patient_id,
        status='Completed'
    ).order_by(Consultation.created_at.desc()).all()
    
    return render_template('consultations/patient_history.html', patient=patient, consultations=consultations)

@consultations_bp.route('/<int:consultation_id>/edit', methods=['GET', 'POST'])
def edit_consultation(consultation_id):
    """Edit consultation (only in Draft status)"""
    consultation = Consultation.query.get_or_404(consultation_id)
    appointment = Appointment.query.get(consultation.appointment_id)
    patient = Patient.query.get(consultation.patient_id)
    
    # Check if consultation is in Draft status
    if consultation.status != 'Draft':
        flash('Can only edit consultations in Draft status', 'error')
        return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))
    
    if request.method == 'POST':
        try:
            vitals = request.form.get('vitals', '').strip()
            notes = request.form.get('notes', '').strip()
            
            if not vitals:
                flash('Vitals information is required', 'error')
                return redirect(url_for('consultations.edit_consultation', consultation_id=consultation_id))
            
            consultation.vitals = vitals
            consultation.notes = notes
            db.session.commit()
            
            flash('Consultation updated successfully', 'success')
            return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating consultation: {str(e)}', 'error')
    
    return render_template('consultations/edit.html', consultation=consultation, appointment=appointment, patient=patient)
