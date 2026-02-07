from flask import Flask, render_template
from config import Config
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = 'your-secret-key-change-this'

    db.init_app(app)

    from models import Patient, Appointment, Consultation

    with app.app_context():
        db.create_all()

    # Register blueprints
    from routes.patients import patients_bp
    from routes.appointments import appointments_bp
    from routes.consultations import consultations_bp
    
    app.register_blueprint(patients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(consultations_bp)

    @app.route("/")
    def home():
        return render_template('index.html')

    return app



app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
