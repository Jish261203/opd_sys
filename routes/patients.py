from flask import Blueprint, request, render_template, redirect, url_for, flash
from extensions import db
from models import Patient
from datetime import datetime

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')

@patients_bp.route('/', methods=['GET'])
def list_patients():
    """List all patients with search functionality"""
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        patients = Patient.query.filter(
            (Patient.name.ilike(f'%{search_query}%')) |
            (Patient.phone.ilike(f'%{search_query}%'))
        ).all()
    else:
        patients = Patient.query.all()
    
    return render_template('patients/list.html', patients=patients, search_query=search_query)

@patients_bp.route('/create', methods=['GET', 'POST'])
def create_patient():
    """Create a new patient"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            gender = request.form.get('gender', '').strip()
            age = request.form.get('age', '')
            phone = request.form.get('phone', '').strip()
            
            # Validation
            if not name:
                flash('Patient name is required', 'error')
                return redirect(url_for('patients.create_patient'))
            
            if not gender:
                flash('Gender is required', 'error')
                return redirect(url_for('patients.create_patient'))
            
            if not age or not age.isdigit() or int(age) < 0 or int(age) > 150:
                flash('Valid age is required (0-150)', 'error')
                return redirect(url_for('patients.create_patient'))
            
            if not phone:
                flash('Phone number is required', 'error')
                return redirect(url_for('patients.create_patient'))
            
            # Create patient
            patient = Patient(
                name=name,
                gender=gender,
                age=int(age),
                phone=phone,
                status='Active',
                created_at=datetime.utcnow()
            )
            
            db.session.add(patient)
            db.session.commit()
            
            flash(f'Patient {name} created successfully!', 'success')
            return redirect(url_for('patients.list_patients'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating patient: {str(e)}', 'error')
            return redirect(url_for('patients.create_patient'))
    
    return render_template('patients/create.html')

@patients_bp.route('/<int:patient_id>', methods=['GET'])
def view_patient(patient_id):
    """View patient details"""
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patients/view.html', patient=patient)

@patients_bp.route('/<int:patient_id>/edit', methods=['GET', 'POST'])
def edit_patient(patient_id):
    """Edit patient status"""
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        try:
            new_status = request.form.get('status', '').strip()
            
            if new_status not in ['Active', 'Inactive']:
                flash('Invalid status', 'error')
                return redirect(url_for('patients.edit_patient', patient_id=patient_id))
            
            patient.status = new_status
            db.session.commit()
            
            flash(f'Patient status updated to {new_status}', 'success')
            return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating patient: {str(e)}', 'error')
    
    return render_template('patients/edit.html', patient=patient)
