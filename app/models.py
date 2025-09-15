from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
db = SQLAlchemy()
login_manager = LoginManager()


# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User unification Model - ADD UserMixin
class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_code = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'), nullable=False)
    full_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    staff_profile = db.relationship('Staff', backref='user', uselist=False, cascade='all, delete-orphan')
    
    # Flask-Login requires get_id() method - ADD THIS
    def get_id(self):
        return str(self.user_id)
    
    def __repr__(self) -> str:
        return f"User: {self.user_code}, Role ID: {self.role_id}"
    
# Profile Models
class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
    register_number = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    parent_name = db.Column(db.String(20), nullable=False)
    parent_contact = db.Column(db.String(10), nullable=False)
    
    # Relationship to behavioural points
    behavioural_points = db.relationship('BehaviouralPoints', backref='student', uselist=False)
    
    def __repr__(self) -> str:
        return f"Student: {self.register_number}"

class Staff(db.Model):
    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
    staff_empid = db.Column(db.String(30), unique=True, nullable=False)
    position = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    
    def __repr__(self) -> str:
        return f"Staff: {self.staff_empid}"
    
# Disciplinary and Behavioural Models
class OffenceType(db.Model):
    offence_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    offence_name = db.Column(db.String(50), unique=True, nullable=False)
    deduct_points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self) -> str:
        return f"Offence: {self.offence_name}, Points: {self.deduct_points}"

class DisciplinaryRecord(db.Model):
    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    offence_id = db.Column(db.Integer, db.ForeignKey('offence_type.offence_id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    action_taken = db.Column(db.String(255), nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationship to offence type
    offence_type = db.relationship('OffenceType', backref='disciplinary_records')
    
    def __repr__(self) -> str:
        return f"Student ID: {self.student_id}, Offence ID: {self.offence_id}"

class BehaviouralPoints(db.Model):
    bpoints_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False, unique=True)
    total_points = db.Column(db.Integer, nullable=False, default=100)  # Starting points
    offence_count = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    def deduct_points(self, offence_id):
        offence = OffenceType.query.get(offence_id)
        if offence:
            self.total_points -= offence.deduct_points
            self.offence_count += 1
            self.last_updated = db.func.now()
            return True
        return False
    
    def __repr__(self) -> str:
        return f"Student ID: {self.student_id}, Points: {self.total_points}"

# Role Management Model
class Role(db.Model):
    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def __repr__(self) -> str:
        return f"Role: {self.role_name}"