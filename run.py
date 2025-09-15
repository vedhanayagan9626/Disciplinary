from app import create_app
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

app = create_app()

# Import models and routes after creating app to avoid circular imports
from app.models import db, User, Student, Staff, Role, OffenceType, BehaviouralPoints, DisciplinaryRecord

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/students')
@login_required
def students():
    students = Student.query.join(User).all()
    return render_template('students.html', students=students)

@app.route('/add-students')
@login_required
def add_students():
    return render_template('add-students.html', students=students)

@app.route('/staff')
@login_required
def staff():
    staff_members = Staff.query.join(User).all()
    return render_template('staff.html', staff_members=staff_members)

@app.route('/add-staff')
@login_required
def add_staff():
    staff_members = Staff.query.join(User).all()
    return render_template('add-staff.html', staff_members=staff_members)

@app.route('/disciplinary')
@login_required
def disciplinary():
    offences = OffenceType.query.all()
    students = Student.query.join(User).all()
    records = DisciplinaryRecord.query.all()
    return render_template('disciplinary.html', 
                         offences=offences, 
                         students=students, 
                         records=records)

@app.route('/behavioral_points')
@login_required
def behavioral_points():
    points = BehaviouralPoints.query.join(Student).join(User).all()
    return render_template('behavioral_points.html', points=points)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)