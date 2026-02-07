# OPD System - Quick Reference & Cheat Sheet

## 🎯 Project Overview (One-Liner)

Flask-based OPD management system with relational database, status-driven workflows, and server-side validation enforcing business rules.

---

## 📊 Database Schema Quick View

```
PATIENTS (id, name, gender, age, phone, status, created_at)
    ↓ 1-to-Many relationship
APPOINTMENTS (id, patient_id, doctor_name, appointment_datetime, status)
    ↓ 1-to-1 relationship
CONSULTATIONS (id, appointment_id, patient_id, vitals, notes, status, created_at)
```

---

## 🔗 Key Relationships

| Relationship               | Purpose                              | Constraint                  |
| -------------------------- | ------------------------------------ | --------------------------- |
| Patient → Appointment      | One patient has many appointments    | FK: patient_id              |
| Appointment → Consultation | One appointment has one consultation | FK: appointment_id + UNIQUE |
| Patient → Consultation     | Denormalized for quick access        | FK: patient_id              |

---

## 📍 All Endpoints (20 Total)

### Patient Routes (`/patients`)

```
GET  /patients/                    List all patients (searchable)
POST /patients/create              Create new patient
GET  /patients/<id>                View patient details
GET  /patients/<id>/edit           Show edit form
POST /patients/<id>/edit           Update patient status
```

### Appointment Routes (`/appointments`)

```
GET  /appointments/today           List today's appointments
GET  /appointments/create          Show booking form
POST /appointments/create          Create appointment
GET  /appointments/<id>            View appointment
POST /appointments/<id>/cancel     Cancel appointment
```

### Consultation Routes (`/consultations`)

```
GET  /consultations/new/<appt_id>  Show consultation form
POST /consultations/new/<appt_id>  Create consultation
GET  /consultations/<id>           View consultation
POST /consultations/<id>/complete  Mark completed (⭐ auto-updates appointment)
GET  /consultations/<id>/edit      Show edit form
POST /consultations/<id>/edit      Update consultation
GET  /consultations/patient/<id>   View completed consultations for patient
```

---

## ✅ All Business Rules

| #   | Rule                                                | Validates                           | Level       |
| --- | --------------------------------------------------- | ----------------------------------- | ----------- |
| 1   | Only Active patients can book appointments          | `patient.status == 'Active'`        | Application |
| 2   | Appointments cannot be in the past                  | `appointment_datetime > now()`      | Application |
| 3   | One consultation per appointment                    | UNIQUE(appointment_id)              | Database    |
| 4   | Consultations only for Scheduled appointments       | `appointment.status == 'Scheduled'` | Application |
| 5   | Cannot cancel Completed appointments                | `appointment.status != 'Completed'` | Application |
| 6   | Can only edit Draft consultations                   | `consultation.status == 'Draft'`    | Application |
| 7   | Auto-update appointment when consultation completes | Transaction                         | Application |
| 8   | Patient registration requires all fields            | Validation                          | Application |
| 9   | Age must be 0-150                                   | Validation                          | Application |

---

## 🔐 Validation Layers

```
Layer 1: Frontend (HTML5)
  ├─ Type validation (number, text, datetime)
  └─ Required field checks

Layer 2: Backend/Application (Python)
  ├─ Business logic validation (status checks)
  ├─ Data format validation (age range)
  ├─ Logical validation (future dates)
  └─ Constraint checks (one consultation per appointment)

Layer 3: Database (MySQL)
  ├─ Foreign key constraints
  ├─ UNIQUE constraints
  ├─ NOT NULL constraints
  └─ Data type validation
```

**Key**: All layers necessary. Backend is mandatory (can't be bypassed).

---

## 🔄 State Machines

### Patient Status

```
Active ←→ Inactive
```

**Controls**: Can book appointments

### Appointment Status

```
Scheduled ─→ Completed
         ↓
      Cancelled (terminal)
```

**Controls**: Can create/cancel consultation

### Consultation Status

```
Draft ──→ Completed (terminal)
```

**Controls**: Can edit, can mark complete

---

## 📁 File Organization

```
opd_app/
├── app.py                    # Flask app, blueprints registration
├── config.py                 # Database config
├── extensions.py             # SQLAlchemy db instance
├── models.py                 # Patient, Appointment, Consultation models
├── requirements.txt          # Dependencies list
├── .env                      # DATABASE_URL
├── routes/
│   ├── patients.py           # Patient routes (70 lines)
│   ├── appointments.py       # Appointment routes (95 lines)
│   └── consultations.py      # Consultation routes (140 lines)
└── templates/
    ├── base.html             # Base layout + CSS
    ├── index.html            # Home page
    ├── patients/             # 4 patient templates
    ├── appointments/         # 3 appointment templates
    └── consultations/        # 4 consultation templates
```

---

## 🎨 Template Hierarchy

```
base.html (navigation, CSS, footer)
  ├── index.html (home)
  ├── patients/list.html
  ├── patients/create.html
  ├── patients/view.html
  ├── patients/edit.html
  ├── appointments/today.html
  ├── appointments/create.html
  ├── appointments/view.html
  ├── consultations/create.html
  ├── consultations/view.html
  ├── consultations/edit.html
  └── consultations/patient_history.html
```

All inherit from `base.html` for consistent styling.

---

## 🚀 How to Run

### Development

```bash
python app.py
# Visit http://localhost:5000
```

### Production

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### With Logging

```bash
gunicorn -w 4 -b 0.0.0.0:8000 \
  --access-logfile access.log \
  --error-logfile error.log \
  "app:create_app()"
```

---

## 🔧 Key Architecture Decisions

| Decision                   | Why                                         | File               |
| -------------------------- | ------------------------------------------- | ------------------ |
| **Extensions.py**          | Circular import prevention                  | extensions.py      |
| **Blueprints**             | Modular routes                              | routes/\*.py       |
| **SQLAlchemy ORM**         | Type-safe queries, SQL injection prevention | models.py          |
| **Jinja2 Templates**       | Server-rendered HTML, SEO-friendly          | templates/\*       |
| **Status-Driven**          | Clear state transitions                     | models.py + routes |
| **Server-Side Validation** | Security (can't be bypassed)                | routes/\*.py       |

---

## ⚡ Critical Features

### Feature 1: Search Patients

```python
# Case-insensitive LIKE search on name or phone
Patient.query.filter(
    (Patient.name.ilike(f'%{query}%')) |
    (Patient.phone.ilike(f'%{query}%'))
)
```

### Feature 2: Today's Appointments

```python
# Filter by date (not datetime)
from sqlalchemy import func
Appointment.query.filter(
    func.date(Appointment.appointment_datetime) == date.today()
)
```

### Feature 3: Auto-Update Appointment

```python
# Transaction: both succeed or both fail
consultation.status = 'Completed'
appointment.status = 'Completed'
db.session.commit()  # Both updated together
```

### Feature 4: One Consultation Per Appointment

```python
# Check in application
existing = Consultation.query.filter_by(appointment_id=id).first()
if existing:
    flash('Consultation already exists')

# Plus UNIQUE constraint at database level
# appointment_id UNIQUE in consultations table
```

---

## 📋 Common Queries

### Get active patients

```python
Patient.query.filter_by(status='Active').all()
```

### Get today's appointments

```python
from datetime import date
Appointment.query.filter(
    func.date(Appointment.appointment_datetime) == date.today()
).all()
```

### Get completed consultations for patient

```python
Consultation.query.filter_by(
    patient_id=patient_id,
    status='Completed'
).all()
```

### Get consultation for appointment

```python
Consultation.query.filter_by(appointment_id=appointment_id).first()
```

---

## 🐛 Common Error Messages

| Error                                              | Cause                                 | Solution                                  |
| -------------------------------------------------- | ------------------------------------- | ----------------------------------------- |
| "Cannot create appointment for inactive patient"   | Patient status is Inactive            | Change status to Active first             |
| "Cannot create appointment in the past"            | Past datetime selected                | Choose future date/time                   |
| "Cannot create consultation for this appointment"  | Appointment not Scheduled             | Appointment must be Scheduled             |
| "Consultation already exists for this appointment" | Second consultation attempted         | Only one per appointment allowed          |
| "Can only edit consultations in Draft status"      | Trying to edit completed consultation | Consultations are locked after completion |

---

## 🎯 Interview Talking Points

### Topic 1: Architecture

> "I used Flask with modular blueprints for scalability, SQLAlchemy ORM for type-safe queries, and Jinja2 for server-rendered templates."

### Topic 2: Business Logic

> "All business rules are enforced server-side because frontend validation can be bypassed. Database constraints provide an additional safety layer."

### Topic 3: Status Machines

> "Status fields drive allowed operations. A patient with status=Inactive can't book appointments. An appointment with status=Scheduled can have a consultation, but a Completed appointment cannot."

### Topic 4: Transaction Handling

> "When marking a consultation complete, both the consultation and appointment statuses are updated in a single transaction, ensuring atomicity—either both succeed or both rollback."

### Topic 5: Uniqueness

> "The UNIQUE constraint on appointment_id in the consultations table prevents duplicate consultations. I added an application-level check too for better error messages."

---

## 📊 Database Constraints

```sql
-- FOREIGN KEY constraints
ALTER TABLE appointments
  ADD CONSTRAINT fk_patient
  FOREIGN KEY (patient_id) REFERENCES patients(id);

ALTER TABLE consultations
  ADD CONSTRAINT fk_appointment
  FOREIGN KEY (appointment_id) REFERENCES appointments(id);

ALTER TABLE consultations
  ADD CONSTRAINT fk_consultation_patient
  FOREIGN KEY (patient_id) REFERENCES patients(id);

-- UNIQUE constraint
ALTER TABLE consultations
  ADD CONSTRAINT uk_one_consultation_per_appointment
  UNIQUE(appointment_id);
```

---

## 🔍 Quick Debugging

### Check if patient exists

```python
patient = Patient.query.get(patient_id)
print(patient.status, patient.name)
```

### Check if appointment is scheduled

```python
appointment = Appointment.query.get(appointment_id)
print(f"Status: {appointment.status}, DateTime: {appointment.appointment_datetime}")
```

### Check if consultation exists

```python
consultation = Consultation.query.filter_by(appointment_id=id).first()
print(f"Exists: {consultation is not None}")
```

---

## 🎓 Learning Points

1. **Circular Imports**: Create `extensions.py` to initialize shared objects
2. **Blueprints**: Organize routes by feature, not by HTTP method
3. **Validation**: Always validate on backend, frontend is UX only
4. **Transactions**: Use `db.session.commit()` for multi-step operations
5. **Constraints**: Use database constraints as safety nets
6. **Status Machines**: Model workflows with explicit states
7. **Error Handling**: Wrap database operations in try-except with rollback
8. **Relationships**: Use proper foreign keys for referential integrity

---

## 📚 Documentation Files

1. **README.md** - Complete project documentation (20 pages)
2. **INTERVIEW_PREP.md** - Interview Q&A and explanations (15 pages)
3. **PROJECT_SUMMARY.md** - What was built and decisions (10 pages)
4. **This file** - Quick reference and cheat sheet (2 pages)

---

## ✨ Key Takeaways

✅ **Modular**: Blueprints make code organized and scalable
✅ **Secure**: Server-side validation prevents bypass
✅ **Consistent**: Status machines prevent invalid states
✅ **Reliable**: Transactions ensure atomicity
✅ **Maintainable**: Clear separation of concerns
✅ **Documented**: Everything is explained in detail

**You're fully prepared to:**

- ✅ Explain the project to anyone
- ✅ Answer technical questions
- ✅ Defend design decisions
- ✅ Discuss improvements
- ✅ Run and demo the application
