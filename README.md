# OPD Management System - Complete Documentation

## Project Overview

This is a **Python Flask-based Outpatient Department (OPD) Management System** that handles patient registration, appointment booking, and consultation tracking with strict business rule enforcement. The system demonstrates:

- **Relational Database Design** using SQLAlchemy ORM
- **Status-Driven Workflows** with state validation
- **Server-Side Validation** (all business logic on backend)
- **MVC Architecture** with Blueprints for scalability

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Technology Stack](#technology-stack)
3. [Installation & Setup](#installation--setup)
4. [Database Schema](#database-schema)
5. [Business Rules & Validations](#business-rules--validations)
6. [API Routes & Endpoints](#api-routes--endpoints)
7. [Workflow Explanation](#workflow-explanation)
8. [Key Features](#key-features)
9. [Deployment](#deployment)

---

## Project Structure

```
opd_app/
├── app.py                 # Main Flask application
├── config.py              # Database configuration
├── extensions.py          # SQLAlchemy db initialization (avoids circular imports)
├── models.py              # Database models (Patient, Appointment, Consultation)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (DATABASE_URL)
│
├── routes/                # Blueprint modules for different features
│   ├── patients.py        # Patient CRUD operations
│   ├── appointments.py    # Appointment management
│   └── consultations.py   # Consultation workflow
│
└── templates/             # Jinja2 HTML templates
    ├── base.html          # Base template with Bootstrap layout
    ├── index.html         # Home page
    ├── patients/
    │   ├── list.html      # List all patients (with search)
    │   ├── create.html    # Create new patient form
    │   ├── view.html      # View patient details
    │   └── edit.html      # Edit patient status
    ├── appointments/
    │   ├── create.html    # Book new appointment
    │   ├── today.html     # Today's appointments list
    │   └── view.html      # View appointment details
    └── consultations/
        ├── create.html    # Record consultation
        ├── view.html      # View consultation details
        ├── edit.html      # Edit consultation (Draft only)
        └── patient_history.html  # View completed consultations per patient
```

---

## Technology Stack

| Component              | Technology                      |
| ---------------------- | ------------------------------- |
| **Backend**            | Python 3.9+                     |
| **Framework**          | Flask 3.1.2                     |
| **ORM**                | SQLAlchemy 2.0.46               |
| **Database**           | MySQL/MariaDB (Aiven Cloud)     |
| **Database Driver**    | PyMySQL                         |
| **Frontend**           | Jinja2 templating + Bootstrap 5 |
| **Session Management** | Flask built-in                  |

---

## Installation & Setup

### 1. Prerequisites

- Python 3.9+
- MySQL/MariaDB database
- Virtual environment (venv)

### 2. Clone and Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Database

Create a `.env` file in the project root:

```
DATABASE_URL=mysql+pymysql://username:password@host:port/dbname
```

**Why `mysql+pymysql://`?**

- SQLAlchemy needs to know which driver to use
- `mysql://` defaults to MySQLdb (requires C dependencies)
- `mysql+pymysql://` explicitly uses PyMySQL (pure Python, easier to install)

### 4. Run the Application

**Development Mode (with auto-reload):**

```bash
python app.py
```

Server runs at: `http://localhost:5000`

**Production Mode (with Gunicorn):**

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

---

## Database Schema

### Table 1: PATIENTS

| Column     | Type         | Constraints      | Purpose                                         |
| ---------- | ------------ | ---------------- | ----------------------------------------------- |
| id         | INT          | PRIMARY KEY      | Unique identifier                               |
| name       | VARCHAR(100) | NOT NULL         | Patient full name                               |
| gender     | VARCHAR(10)  |                  | Male/Female/Other                               |
| age        | INT          |                  | Patient age                                     |
| phone      | VARCHAR(20)  |                  | Contact number                                  |
| status     | VARCHAR(20)  | DEFAULT 'Active' | Active/Inactive (controls appointment creation) |
| created_at | DATETIME     | DEFAULT NOW()    | Registration timestamp                          |

**Why status field?**

- Controls workflow - only Active patients can book appointments
- Allows "soft deletion" - patient data retained but unavailable for new bookings

---

### Table 2: APPOINTMENTS

| Column               | Type         | Constraints         | Purpose                       |
| -------------------- | ------------ | ------------------- | ----------------------------- |
| id                   | INT          | PRIMARY KEY         | Unique identifier             |
| patient_id           | INT          | FK → patients.id    | Links to patient              |
| doctor_name          | VARCHAR(100) |                     | Doctor assigned               |
| appointment_datetime | DATETIME     | NOT NULL            | When appointment is scheduled |
| status               | VARCHAR(20)  | DEFAULT 'Scheduled' | Scheduled/Completed/Cancelled |

**Foreign Key Constraint:** `patient_id` → `patients.id`

**Why three statuses?**

- **Scheduled**: Appointment booked, waiting for doctor
- **Completed**: Consultation done, appointment fulfilled
- **Cancelled**: Patient/doctor cancelled appointment

---

### Table 3: CONSULTATIONS

| Column         | Type        | Constraints                   | Purpose                            |
| -------------- | ----------- | ----------------------------- | ---------------------------------- |
| id             | INT         | PRIMARY KEY                   | Unique identifier                  |
| appointment_id | INT         | FK → appointments.id (UNIQUE) | Links to appointment               |
| patient_id     | INT         | FK → patients.id              | Denormalized for performance       |
| vitals         | TEXT        |                               | BP, temp, pulse, respiration, etc. |
| notes          | TEXT        |                               | Doctor's observations              |
| status         | VARCHAR(20) | DEFAULT 'Draft'               | Draft/Completed                    |
| created_at     | DATETIME    | DEFAULT NOW()                 | Recording timestamp                |

**Why UNIQUE on appointment_id?**

- Ensures ONE consultation per appointment only
- Database enforces this at constraint level (not just application level)

**Why denormalized patient_id?**

- Allows direct access to patient without joining appointments
- Useful for patient consultation history queries

---

## Business Rules & Validations

### 1. Patient Creation

```
✓ Name: Required, non-empty
✓ Gender: Required, one of [Male, Female, Other]
✓ Age: Required, 0-150 (reasonable age range)
✓ Phone: Required, non-empty
→ Status auto-set to "Active" (always for new patients)
```

**Where enforced:** `routes/patients.py` → `create_patient()` function

---

### 2. Appointment Creation

```
✗ Cannot create for INACTIVE patient
✗ Cannot create in the PAST (datetime < now())
✓ Patient must exist
✓ Doctor name required
✓ Default status = "Scheduled"
```

**Where enforced:** `routes/appointments.py` → `create_appointment()` function

**Why these validations?**

- Inactive patient check: Prevents booking for patients marked unavailable
- Past datetime check: No historical appointments, only future bookings allowed
- These are business rules, not just UI logic - enforced at database level

---

### 3. Consultation Creation & Workflow

```
✗ Only for "Scheduled" appointments (not Completed/Cancelled)
✗ Only ONE consultation per appointment (UNIQUE constraint)
✓ Vitals required
✓ Notes optional
✓ Auto-status = "Draft"
```

**Consultation Workflow:**

```
Draft → Edit (allowed) → Mark Completed → [Auto-triggers]
                                     ↓
                          Appointment Status = Completed
```

**Where enforced:**

- Status check: `routes/consultations.py` → `create_consultation()`
- One-per-appointment: Database UNIQUE constraint + Python check
- Auto-update: `routes/consultations.py` → `complete_consultation()` (uses transaction)

---

## API Routes & Endpoints

### Patient Endpoints

| Method | Route                 | Purpose                       | Validation                     |
| ------ | --------------------- | ----------------------------- | ------------------------------ |
| GET    | `/patients/`          | List all patients with search | Search by name or phone        |
| POST   | `/patients/create`    | Create new patient            | See Patient Creation rules     |
| GET    | `/patients/<id>`      | View patient details          | Patient must exist             |
| GET    | `/patients/<id>/edit` | Show edit form                | Patient must exist             |
| POST   | `/patients/<id>/edit` | Update patient status         | Status must be Active/Inactive |

**Example: Create Patient**

```bash
curl -X POST http://localhost:5000/patients/create \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=John+Doe&gender=Male&age=30&phone=9876543210"
```

---

### Appointment Endpoints

| Method | Route                       | Purpose              | Validation             |
| ------ | --------------------------- | -------------------- | ---------------------- |
| GET    | `/appointments/today`       | Today's appointments | Filtered by date only  |
| GET    | `/appointments/create`      | Show booking form    | Load active patients   |
| POST   | `/appointments/create`      | Create appointment   | See Appointment rules  |
| GET    | `/appointments/<id>`        | View appointment     | Appointment must exist |
| POST   | `/appointments/<id>/cancel` | Cancel appointment   | Only if not Completed  |

**Why separate endpoint for today?**

- Doctor needs to see only today's appointments
- Filtered server-side using `db.func.date()` SQL function
- Not frontend-side filtering (business logic on backend)

---

### Consultation Endpoints

| Method   | Route                                 | Purpose             | Validation              |
| -------- | ------------------------------------- | ------------------- | ----------------------- |
| GET/POST | `/consultations/new/<appt_id>`        | Create consultation | Appt must be Scheduled  |
| GET      | `/consultations/<id>`                 | View consultation   | Consultation must exist |
| POST     | `/consultations/<id>/complete`        | Mark completed      | Status must be Draft    |
| GET/POST | `/consultations/<id>/edit`            | Edit consultation   | Only if Draft status    |
| GET      | `/consultations/patient/<patient_id>` | Patient's history   | Show only Completed     |

**Most Important:** `POST /consultations/<id>/complete`

```python
# This endpoint triggers:
1. Consultation status → "Completed"
2. Appointment status → "Completed" (AUTOMATIC)
# This is the critical workflow enforcement!
```

---

## Workflow Explanation

### Complete User Journey

```
┌─────────────────────────────────────────────────────┐
│ 1. PATIENT REGISTRATION                              │
├─────────────────────────────────────────────────────┤
│ User: Receptionist fills patient form                │
│ System: Validates (name, gender, age, phone)        │
│ DB: Creates Patient with status='Active'            │
│ Result: Patient record created                       │
└─────────────────────────────────────────────────────┘

                        ↓

┌─────────────────────────────────────────────────────┐
│ 2. APPOINTMENT BOOKING                               │
├─────────────────────────────────────────────────────┤
│ User: Selects active patient, doctor, future date   │
│ System: Validates:                                   │
│   ✓ Patient exists                                  │
│   ✓ Patient status = 'Active' (NOT inactive)        │
│   ✓ appointment_datetime > NOW() (NOT past)        │
│ DB: Creates Appointment with status='Scheduled'    │
│ Result: Patient can now have consultation           │
└─────────────────────────────────────────────────────┘

                        ↓

┌─────────────────────────────────────────────────────┐
│ 3. CONSULTATION RECORDING                            │
├─────────────────────────────────────────────────────┤
│ User: Doctor records vitals and notes                │
│ System: Validates:                                   │
│   ✓ Appointment status = 'Scheduled' (NOT complete) │
│   ✓ No existing consultation (UNIQUE constraint)    │
│   ✓ Vitals field populated                          │
│ DB: Creates Consultation with status='Draft'       │
│ Result: Doctor can still edit before finalizing     │
└─────────────────────────────────────────────────────┘

                        ↓

┌─────────────────────────────────────────────────────┐
│ 4. MARK CONSULTATION COMPLETE                        │
├─────────────────────────────────────────────────────┤
│ User: Doctor clicks "Mark Completed"                │
│ System: Validates:                                   │
│   ✓ Consultation status = 'Draft'                   │
│ DB Action (TRANSACTION):                            │
│   1. Update Consultation status → 'Completed'       │
│   2. Update Appointment status → 'Completed'        │
│      (AUTOMATIC! Critical business rule)            │
│ Result: Appointment fully completed                 │
└─────────────────────────────────────────────────────┘

                        ↓

┌─────────────────────────────────────────────────────┐
│ 5. VIEW PATIENT HISTORY                              │
├─────────────────────────────────────────────────────┤
│ User: Doctor views past consultations                │
│ System: Fetches all Completed consultations         │
│ DB: SELECT * FROM consultations                      │
│      WHERE patient_id=X AND status='Completed'      │
│ Result: Shows patient's medical history             │
└─────────────────────────────────────────────────────┘
```

---

## Key Features Explained

### 1. Circular Import Prevention

**Problem:**

```
app.py → imports → models.py
models.py → imports → app.py (to get db)
↓
Circular Import Error!
```

**Solution:**

```
extensions.py (contains db = SQLAlchemy())
     ↑
     ├─ app.py imports from extensions
     └─ models.py imports from extensions
```

**File:** `extensions.py`

```python
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()  # Created here, imported everywhere
```

---

### 2. Blueprint Architecture

**Why Blueprints?**

- **Modularity**: Each feature (patients, appointments, consultations) is separate
- **Scalability**: Easy to add new features without modifying app.py
- **Reusability**: Can reuse blueprints across projects
- **Team Development**: Multiple developers can work on different blueprints

**File:** `app.py`

```python
from routes.patients import patients_bp
from routes.appointments import appointments_bp
from routes.consultations import consultations_bp

app.register_blueprint(patients_bp)      # Prefix: /patients
app.register_blueprint(appointments_bp)  # Prefix: /appointments
app.register_blueprint(consultations_bp) # Prefix: /consultations
```

---

### 3. Status-Driven State Machine

```
PATIENT Status:
  Active → (can book appointments)
  Inactive → (cannot book appointments)

APPOINTMENT Status:
  Scheduled → (can create consultation)
           → (can be cancelled)
  Completed → (appointment done, cannot cancel)
  Cancelled → (appointment not happening)

CONSULTATION Status:
  Draft → (can edit)
       → (can mark completed → auto-completes appointment)
  Completed → (locked, read-only)
```

**Why this matters?** Prevents invalid state transitions:

- Can't complete a consultation if appointment isn't Scheduled
- Can't create consultation for completed appointment
- Can't create appointment for inactive patient

---

### 4. Server-Side Validation (Critical!)

**All validations happen in Python/Database, NOT JavaScript**

Why?

```
❌ Frontend validation is optional (user can bypass with DevTools)
✓ Backend validation is mandatory (user cannot bypass)
✓ Database constraints add extra safety layer
```

Example:

```python
# In routes/appointments.py
if appointment_datetime < datetime.now():
    flash('Cannot create appointment in the past', 'error')
    return redirect(...)

# This happens on server, not on browser!
```

---

### 5. Transaction Management

When marking consultation complete:

```python
# In routes/consultations.py
consultation.status = 'Completed'      # Line 1
appointment.status = 'Completed'       # Line 2
db.session.commit()                    # Lines 1 & 2 execute together

# If DB error occurs between lines 1-2:
# Both changes are rolled back (ACID principle)
```

---

## Summary of Key Concepts

| Concept                    | Why It Matters                     | Example in Project                                  |
| -------------------------- | ---------------------------------- | --------------------------------------------------- |
| **Blueprints**             | Modular code organization          | patients.py, appointments.py, consultations.py      |
| **Status Machines**        | Enforces valid workflows           | Appointment: Scheduled → Completed → Cancelled      |
| **Server-Side Validation** | Security & data integrity          | Check patient status before creating appointment    |
| **Foreign Keys**           | Referential integrity              | appointment.patient_id references patients.id       |
| **UNIQUE Constraints**     | Prevents duplicates                | One consultation per appointment                    |
| **Transactions**           | Atomicity in multi-step operations | Complete consultation + update appointment together |
| **Eager Loading**          | Query performance                  | Load related records in single query                |

---

## File-by-File Breakdown

### `extensions.py` - SQLAlchemy Initialization

```python
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
```

**Why:** Avoids circular imports. Both app.py and models.py import from here.

---

### `models.py` - Database Schema

- **Patient**: Base entity, status controls workflow
- **Appointment**: Linked to Patient, has one Consultation
- **Consultation**: Linked to Appointment, records vitals/notes

**Key design:** Foreign keys enforce referential integrity

---

### `routes/patients.py` - Patient Management

- `list_patients()`: Search by name/phone
- `create_patient()`: Validation before DB insert
- `edit_patient()`: Only status can be edited
- `view_patient()`: Shows patient + appointments

---

### `routes/appointments.py` - Appointment Booking

- `today_appointments()`: Filter by date
- `create_appointment()`: Validates patient status + future datetime
- `view_appointment()`: Shows appointment + consultation if exists

---

### `routes/consultations.py` - Consultation Workflow

- `create_consultation()`: Only for Scheduled appointments
- `view_consultation()`: Shows vitals/notes
- `complete_consultation()`: Auto-updates appointment status
- `patient_consultations()`: Shows completed history

---

## Testing the Application

### Test Case 1: Create and Complete Workflow

```bash
1. http://localhost:5000/patients/create
   → Fill form: John, Male, 30, 9876543210
   → Patient created with ID=1, status=Active

2. http://localhost:5000/appointments/create
   → Select Patient=1, Doctor=Dr. Smith, Date=Tomorrow
   → Appointment created with ID=1, status=Scheduled

3. http://localhost:5000/consultations/new/1
   → Fill vitals: BP 120/80, Temp 98.6
   → Consultation created with ID=1, status=Draft

4. http://localhost:5000/consultations/1/complete
   → Consultation status → Completed
   → Appointment status → Completed (automatic!)
```

---

## Conclusion

This project demonstrates:
✅ Relational database design with proper constraints
✅ State-driven workflows with validation
✅ Server-side business logic enforcement
✅ MVC architecture with clean separation
✅ Production-ready error handling
✅ Scalable blueprint-based structure

