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

## Key Interview Questions & Answers

### Q1: Why did you create a separate `extensions.py` file?

**Answer:**

> "We faced a circular import issue where `app.py` needed to import `models.py` (to define database tables), and `models.py` needed to import `db` from `app.py`. To break this cycle, I created a separate `extensions.py` file that contains the SQLAlchemy instance. Now both `app.py` and `models.py` import from `extensions.py`, avoiding the circular dependency."

---

### Q2: Why is status validation done on the backend instead of frontend?

**Answer:**

> "Status validation must be server-side because it's a critical business rule. Frontend validation can be bypassed using browser DevTools. By validating on the backend, we ensure:
>
> 1. No invalid state transitions (e.g., completing a draft consultation)
> 2. Data integrity even if the frontend is compromised
> 3. Consistency across all API clients (web, mobile, etc.)
>
> Example: A user can't manually edit the appointment status to 'Completed' when it's still 'Scheduled'. The server will reject it."

---

### Q3: How does the system ensure only ONE consultation per appointment?

**Answer:**

> "We use a two-layer approach:
>
> **Layer 1 - Database Level:**
> In models.py, the appointment_id in consultations table has a UNIQUE constraint, preventing duplicate records at the database level.
>
> **Layer 2 - Application Level:**
> Before creating a consultation, we query the database:
>
> ```python
> existing = Consultation.query.filter_by(appointment_id=id).first()
> if existing:
>     flash('Consultation already exists', 'error')
> ```
>
> This prevents the application from even attempting a duplicate insert."

---

### Q4: What happens when a doctor marks a consultation as 'Complete'?

**Answer:**

> "When the doctor clicks 'Mark Completed', the system:
>
> 1. Validates that the consultation is in 'Draft' status
> 2. Validates that the appointment is in 'Scheduled' status
> 3. Updates BOTH records in a single transaction:
>    - Sets consultation.status = 'Completed'
>    - Sets appointment.status = 'Completed' (automatically)
>
> This automatic appointment status update is critical because:
>
> - It prevents double-booking the same appointment slot
> - It maintains workflow integrity
> - If any error occurs, both changes are rolled back together"

---

### Q5: How does the "search by name or phone" feature work?

**Answer:**

> "The search uses SQLAlchemy's ILIKE operator for case-insensitive pattern matching:
>
> ```python
> patients = Patient.query.filter(
>     (Patient.name.ilike(f'%{search_query}%')) |
>     (Patient.phone.ilike(f'%{search_query}%'))
> ).all()
> ```
>
> This runs a SQL query with LIKE wildcards on the backend, filtering results before sending to the template. It's more efficient than fetching all patients and filtering in Python."

---

### Q6: Why does the system prevent creating appointments in the past?

**Answer:**

> "Creating past appointments would violate business logic:
>
> 1. **Scheduling violation**: Can't schedule appointments for times already passed
> 2. **Consultation impossibility**: Doctor can't see a patient in the past
> 3. **Data integrity**: Would create historical fake records
>
> We validate using:
>
> ```python
> if appointment_datetime < datetime.now():
>     flash('Cannot create appointment in the past', 'error')
> ```
>
> This check happens on the server, preventing backdating even if someone tries via API."

---

### Q7: Can an inactive patient still view their consultation history?

**Answer:**

> "Yes! Status controls FUTURE actions, not historical access:
>
> - **Active status**: Can CREATE new appointments
> - **Inactive status**: Cannot CREATE new appointments, but CAN:
>   - View their profile
>   - View past consultations
>   - Be viewed by doctors for medical history
>
> This is important because marking a patient Inactive shouldn't erase their medical history. Doctors need to see past consultations even for inactive patients."

---

### Q8: How would you handle concurrent appointments for the same patient?

**Answer:**

> "Currently, the system allows multiple appointments for the same patient (which is realistic - a patient can have multiple appointments with different doctors).
>
> However, if the requirement was 'one appointment per patient at a time', we would:
>
> 1. Query for existing Scheduled appointments
> 2. Check if datetime overlaps
> 3. Prevent booking if overlap found
>
> This would need to consider:
>
> - Appointment duration (currently not stored)
> - Doctor availability
> - Time zones
>
> Would implement as a pre-booking validation in the appointment creation route."

---

### Q9: What if the database connection fails?

**Answer:**

> "Flask-SQLAlchemy handles this with exception catching:
>
> ```python
> try:
>     db.session.commit()
> except Exception as e:
>     db.session.rollback()
>     flash(f'Database error: {str(e)}', 'error')
>     return redirect(...)
> ```
>
> All routes wrap database operations in try-except blocks:
>
> - **On success**: Changes committed
> - **On error**: Rollback ensures no partial updates
> - **User feedback**: Flash message explains what happened
>
> For production, would add:
>
> - Retry logic with exponential backoff
> - Database connection pooling
> - Error logging to external service"

---

### Q10: How does the system achieve ACID properties?

**Answer:**

> "**ACID** = Atomicity, Consistency, Isolation, Durability
>
> 1. **Atomicity**: Transactions (db.session.commit()) - all or nothing
> 2. **Consistency**: Foreign keys + status validations keep data valid
> 3. **Isolation**: MySQL handles concurrent requests with locks
> 4. **Durability**: MySQL persists data to disk
>
> Example: When marking consultation complete, if error occurs mid-transaction, both changes (consultation AND appointment status) are rolled back together, never partial."

---

## Scenario Questions

### Scenario 1: Doctor tries to create consultation for cancelled appointment

```
User: Clicks "Create Consultation" for a Cancelled appointment
System: Checks appointment.status == 'Scheduled'?
Result: NO → Flashes 'Consultation can only be created for scheduled appointments'
Outcome: Request redirected, nothing created
```

**Why this matters:** Prevents creating fake consultation records

---

### Scenario 2: Patient status changed to Inactive while appointment exists

```
Situation: Patient has Scheduled appointment, then marked Inactive
Question: Can the appointment still happen?
Answer: YES! Status change doesn't affect existing appointments
        Only prevents NEW appointments from being booked
Outcome: Appointment can proceed, then consultation recorded
```

---

### Scenario 3: Network fails while marking consultation complete

```
Server receives: POST /consultations/5/complete
Executes: consultation.status = 'Completed'
Executes: appointment.status = 'Completed'
Network fails before: db.session.commit()

Result: db.session.rollback() is triggered
Outcome: Both updates are rolled back, appointment remains Scheduled
Doctor tries again: Next attempt succeeds
```

---

### Scenario 4: Two doctors simultaneously try to create consultations for same appointment

```
Doctor A requests: POST /consultations/new/5
Doctor B requests: POST /consultations/new/5

Database check in Doctor A's code: No consultation exists ✓ Proceeds
Database check in Doctor B's code: No consultation exists ✓ Proceeds

Doctor A executes: INSERT Consultation (appointment_id=5) ✓ Success
Doctor B executes: INSERT Consultation (appointment_id=5) ✗ UNIQUE constraint violation!

Result: Doctor B gets "Consultation already exists for this appointment" error
Outcome: Only one consultation created (database constraint prevents duplicates)
```

---

## Advanced Topics

### 1. Database Indexing

Currently, search queries:

```python
Patient.query.filter(Patient.name.ilike(f'%{search_query}%'))
```

**Optimization for large datasets:**

```sql
CREATE INDEX idx_patient_name ON patients(name);
CREATE INDEX idx_patient_phone ON patients(phone);
```

---

### 2. Query Optimization

**Current (N+1 problem potentially):**

```python
consultations = Consultation.query.all()
for c in consultations:
    print(c.appointment.doctor_name)  # Separate query for each!
```

**Optimized (eager loading):**

```python
consultations = Consultation.query.options(
    joinedload(Consultation.appointment)
).all()
```

---

### 3. Authentication

Currently, no authentication. For production:

```python
from flask_login import LoginManager, login_required

@app.route('/patients/')
@login_required
def list_patients():
    # Only logged-in users can access
```

---

## Deployment with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# With logging
gunicorn -w 4 -b 0.0.0.0:8000 \
  --access-logfile access.log \
  --error-logfile error.log \
  "app:create_app()"
```

**Why 4 workers?** Typical formula: `(2 × CPU cores) + 1`

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

**Ready to explain any part to an interviewer?** You now have the complete picture!
# opd_sys
# opd_sys
# opd_sys
