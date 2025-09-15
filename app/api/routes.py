from flask import Blueprint, request, jsonify, redirect, flash, send_file
from app.models import db, User, Student, Staff, Role, OffenceType, BehaviouralPoints, DisciplinaryRecord
from werkzeug.security import generate_password_hash
from flask_login import current_user
import os
from utils.qr_generator import generate_student_qr_code
from io import BytesIO
import base64

api_bp = Blueprint('api', __name__)

@api_bp.route('/add_student', methods=['POST'])
def add_student():
    try:
        # Get form data
        user_data = {
            'user_code': request.form['username'],
            'password': request.form['password'],
            'full_name': request.form['full_name'],
            'gender': request.form['gender'],
            'contact_number': request.form['contact_number'],
            'address': request.form['address'],
            'image_url': request.form.get('image_url', '')
        }
        
        profile_data = {
            'register_number': request.form['register_number'],
            'department': request.form['department'],
            'student_class': request.form['student_class'],
            'parent_name': request.form['parent_name'],
            'parent_contact': request.form['parent_contact']
        }
        
        # Create the student
        success, message, student_id = create_user(user_data, profile_data, 'student')
        
        if success:
            # Generate QR code for the new student
            filename, qr_base64 = generate_student_qr_code(student_id, profile_data['register_number'])
            
            flash(f'Student created successfully: {message}', 'success')
            
            # Return both success message and QR code data
            return jsonify({
                'success': True,
                'message': f'Student created successfully: {message}',
                'qr_code': qr_base64,
                'filename': f'qr_{profile_data["register_number"]}.png',
                'register_number': profile_data['register_number']
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Error creating student: {message}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing student form: {str(e)}'
        }), 500


@api_bp.route('/add_staff', methods=['POST'])
def add_staff():
    try:
        user_data = {
            'user_code': request.form['username'],
            'password': request.form['password'],
            'full_name': request.form['full_name'],
            'gender': request.form['gender'],
            'contact_number': request.form['contact_number'],
            'address': request.form['address'],
            'image_url': request.form.get('image_url', '')
        }
        
        profile_data = {
            'staff_empid': request.form['empid'],
            'position': request.form['position'],
            'department': request.form['department']
        }
        
        success, message = create_user(user_data, profile_data, 'staff')
        
        if success:
            flash(f'Staff created successfully: {message}', 'success')
        else:
            flash(f'Error creating staff: {message}', 'error')
            
    except Exception as e:
        flash(f'Error processing staff form: {str(e)}', 'error')
    
    return redirect('/staff')

@api_bp.route('/record_offence', methods=['POST'])
def record_offence_route():
    try:
        # Get form data
        student_id = request.form['student_id']
        offence_id = request.form['offence_id']
        description = request.form['description']
        action_taken = request.form['action_taken']
        
        # Get staff ID from current logged-in user (assuming staff is logged in)
        if not current_user.is_authenticated:
            flash('You must be logged in to record an offence', 'error')
            return redirect('/login')
        
        # Get the staff ID from the user's staff profile
        staff = Staff.query.filter_by(user_id=current_user.user_id).first()
        if not staff:
            flash('Only staff members can record offences', 'error')
            return redirect('/disciplinary')
        
        staff_id = staff.staff_id
        
        # Record the offence
        record = record_offence(student_id, offence_id, description, action_taken, staff_id)
        
        flash(f'Offence recorded successfully. Points deducted from student.', 'success')
        
    except Exception as e:
        flash(f'Error recording offence: {str(e)}', 'error')
    
    return redirect('/disciplinary')

def create_user(user_data, profile_data, role_name):
    try:
        # Check if username already exists
        if User.query.filter_by(user_code=user_data['user_code']).first():
            return False, "Username already exists", None
        
        # Get role ID
        role = Role.query.filter_by(role_name=role_name).first()
        if not role:
            return False, "Role does not exist", None
        
        # Validate password confirmation if provided
        if 'confirm_password' in request.form and user_data['password'] != request.form['confirm_password']:
            return False, "Passwords do not match", None
        
        # Create user
        user = User(
            user_code=user_data['user_code'],
            password_hash=generate_password_hash(user_data['password']),
            role_id=role.role_id,
            full_name=user_data['full_name'],
            gender=user_data['gender'],
            contact_number=user_data['contact_number'],
            address=user_data['address'],
            image_url=user_data.get('image_url')
        )
        
        db.session.add(user)
        db.session.flush()  # Get the user ID without committing
        
        # Create specific profile based on role
        if role_name == 'student':
            # Check if register number already exists
            if Student.query.filter_by(register_number=profile_data['register_number']).first():
                db.session.rollback()
                return False, "Register number already exists", None
                
            profile = Student(
                user_id=user.user_id,
                register_number=profile_data['register_number'],
                department=profile_data['department'],
                student_class=profile_data['student_class'],
                parent_name=profile_data['parent_name'],
                parent_contact=profile_data['parent_contact']
            )
            
            db.session.add(profile)
            db.session.flush()  # Get the student ID
            
            # Initialize behavioural points with default 100 points
            behavioural_points = BehaviouralPoints(
                student_id=profile.student_id,
                total_points=100,
                offence_count=0
            )
            db.session.add(behavioural_points)
            
            student_id = profile.student_id
            
        elif role_name == 'staff':
            # Check if employee ID already exists
            if Staff.query.filter_by(staff_empid=profile_data['staff_empid']).first():
                db.session.rollback()
                return False, "Employee ID already exists", None
                
            profile = Staff(
                user_id=user.user_id,
                staff_empid=profile_data['staff_empid'],
                position=profile_data['position'],
                department=profile_data['department']
            )
            db.session.add(profile)
            student_id = None
        
        db.session.commit()
        
        return True, f"{user_data['full_name']} ({profile_data['register_number' if role_name == 'student' else 'staff_empid']})", student_id
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating user: {str(e)}", None

@api_bp.route('/download_qr/<filename>', methods=['GET'])
def download_qr(filename):
    qr_path = os.path.join('static', 'qrcodes', filename)
    if os.path.exists(qr_path):
        return send_file(qr_path, as_attachment=True)
    else:
        return jsonify({'error': 'QR code not found'}), 404
    
def record_offence(student_id, offence_id, description, action_taken, staff_id):
    try:
        # Create disciplinary record
        record = DisciplinaryRecord(
            student_id=student_id,
            offence_id=offence_id,
            description=description,
            action_taken=action_taken,
            recorded_by=staff_id
        )
        
        db.session.add(record)
        
        # Deduct points
        behavioural_points = BehaviouralPoints.query.filter_by(student_id=student_id).first()
        if behavioural_points:
            # Get offence details to know how many points to deduct
            offence = OffenceType.query.get(offence_id)
            if offence:
                behavioural_points.total_points -= offence.deduct_points
                behavioural_points.offence_count += 1
            else:
                raise Exception("Offence type not found")
        else:
            raise Exception("Student behavioural record not found")
        
        db.session.commit()
        
        return record
        
    except Exception as e:
        db.session.rollback()
        raise e

# Additional helper endpoint to get student and offence data for forms
@api_bp.route('/api/students', methods=['GET'])
def get_students():
    students = Student.query.join(User).all()
    student_list = [{
        'student_id': s.student_id,
        'name': s.user.full_name,
        'register_number': s.register_number,
        'class': s.student_class
    } for s in students]
    return jsonify(student_list)

@api_bp.route('/api/offences', methods=['GET'])
def get_offences():
    offences = OffenceType.query.all()
    offence_list = [{
        'offence_id': o.offence_id,
        'offence_name': o.offence_name,
        'deduct_points': o.deduct_points,
        'description': o.description
    } for o in offences]
    return jsonify(offence_list)

@api_bp.route('/api/student/<int:student_id>/all_details', methods=['GET'])
def get_student_points(student_id):
    points = BehaviouralPoints.query.filter_by(student_id=student_id).first()
    student_details = Student.query.get(student_id)
    user_details = User.query.get(student_details.user_id) if student_details else None
    if student_details and points:

        return jsonify({
            'student_name': user_details.full_name if user_details else "Unknown",
            'register_number': student_details.register_number if student_details else "Unknown",
            'student_class': student_details.student_class if student_details else "Unknown",
            'department': student_details.department if student_details else "Unknown",
            'parent_name': student_details.parent_name if student_details else "Unknown",
            'parent_contact': student_details.parent_contact if student_details else "Unknown",
            'total_points': points.total_points if student_details else "Unknown",
            'offence_count': points.offence_count if student_details else "Unknown"
        })
    return jsonify({'error': 'Student points not found'}), 404