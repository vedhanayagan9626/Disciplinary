from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_login import LoginManager

# Initialize extensions
from app.models import db, login_manager

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.api.auth import main_bp, auth_bp
    from app.api.routes import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default roles if they don't exist
        from app.models import Role
        default_roles = ['admin', 'staff', 'student']
        for role_name in default_roles:
            if not Role.query.filter_by(role_name=role_name).first():
                role = Role(role_name=role_name, description=f'{role_name.capitalize()} role')
                db.session.add(role)
        
        # Create default offence types if they don't exist
        from app.models import OffenceType
        default_offences = [
            ('Latecoming', 5, 'Arriving late to class or activities'),
            ('Uniform Violation', 10, 'Not wearing proper uniform'),
            ('Disruptive Behavior', 15, 'Disrupting class or activities'),
            ('Academic Dishonesty', 20, 'Cheating or plagiarism'),
            ('Bullying', 25, 'Harassment or bullying behavior')
        ]
        
        for offence_name, points, description in default_offences:
            if not OffenceType.query.filter_by(offence_name=offence_name).first():
                offence = OffenceType(
                    offence_name=offence_name,
                    deduct_points=points,
                    description=description
                )
                db.session.add(offence)
        
        db.session.commit()
    
    return app