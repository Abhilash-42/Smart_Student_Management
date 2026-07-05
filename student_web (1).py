"""
Smart Student Academic Management System
Professional Role-Based Dashboard
Compatible with MongoDB Atlas and Vercel Deployment
Python 3.12
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import os
from datetime import datetime
import json
from functools import wraps
import secrets
import hashlib
from io import BytesIO
from flask import send_file

# Initialize Flask App
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# MongoDB Atlas Connection
MONGO_URI = os.getenv('MONGO_URI', 'your_mongodb_atlas_connection_string_here')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    db = client['student_management']
    students_collection = db['students']
    users_collection = db['users']
    print("✅ MongoDB Atlas Connected Successfully")
except ServerSelectionTimeoutError:
    print("❌ MongoDB Atlas Connection Failed")
    print("Please check your connection string")
    exit(1)

# =================================================
# USER AUTHENTICATION AND ROLE MANAGEMENT
# =================================================

def create_default_admin():
    """
    Create default admin account if it doesn't exist
    """
    try:
        # Check if admin exists
        admin_exists = users_collection.find_one({"username": "admin"})
        
        if not admin_exists:
            # Create default admin
            admin_data = {
                "username": "admin",
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "role": "admin",
                "created_at": datetime.now()
            }
            users_collection.insert_one(admin_data)
            print("✅ Default admin account created")
        
        # Check if default user exists
        user_exists = users_collection.find_one({"username": "student"})
        
        if not user_exists:
            # Create default user
            user_data = {
                "username": "student",
                "password": hashlib.sha256("student123".encode()).hexdigest(),
                "role": "user",
                "created_at": datetime.now()
            }
            users_collection.insert_one(user_data)
            print("✅ Default user account created")
            
    except Exception as e:
        print(f"❌ Error creating default accounts: {e}")

# Create default admin account on startup
create_default_admin()

def login_required(f):
    """
    Decorator to require login for routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator to require admin role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    """
    Decorator to require user role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['admin', 'user']:
            flash('Access denied', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =================================================
# ROUTES
# =================================================

@app.route('/')
def index():
    """
    Redirect to login or dashboard
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter username and password', 'error')
            return render_template('login.html')
        
        # Find user in database
        user = users_collection.find_one({"username": username})
        
        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
            # Set session variables
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash(f'Welcome {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    User logout route
    """
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Main dashboard route
    """
    try:
        # Fetch all students
        students = list(students_collection.find())
        
        # Calculate statistics
        total_students = len(students)
        
        if total_students > 0:
            # Calculate percentages
            for student in students:
                marks = [
                    student.get('math', 0),
                    student.get('science', 0),
                    student.get('english', 0),
                    student.get('hindi', 0),
                    student.get('social_studies', 0)
                ]
                total_marks = sum(marks)
                percentage = (total_marks / 500) * 100 if total_marks > 0 else 0
                student['percentage'] = round(percentage, 2)
                
                # Calculate rank
                student['rank'] = calculate_rank(students, student)
                
                # Determine status
                student['status'] = get_performance_status(percentage)
            
            # Sort by percentage for ranking
            students.sort(key=lambda x: x.get('percentage', 0), reverse=True)
            
            # Calculate statistics
            total_percentage = sum(s.get('percentage', 0) for s in students)
            class_average = round(total_percentage / total_students, 2)
            
            top_performers = len([s for s in students if s.get('percentage', 0) >= 90])
            weak_students = len([s for s in students if s.get('percentage', 0) < 40])
        else:
            class_average = 0
            top_performers = 0
            weak_students = 0
        
        # Prepare chart data
        student_names = [s.get('name', '') for s in students]
        student_percentages = [s.get('percentage', 0) for s in students]
        
        subjects = ['Math', 'Science', 'English', 'Hindi', 'Social Studies']
        subject_averages = []
        
        for subject in subjects:
            subject_key = subject.lower().replace(' ', '_')
            total = sum(s.get(subject_key, 0) for s in students)
            avg = round(total / total_students, 2) if total_students > 0 else 0
            subject_averages.append(avg)
        
        performance_distribution = {
            'Excellent': len([s for s in students if s.get('percentage', 0) >= 75]),
            'Average': len([s for s in students if 50 <= s.get('percentage', 0) < 75]),
            'Poor': len([s for s in students if s.get('percentage', 0) < 50])
        }
        
        return render_template('home.html',
                             students=students,
                             total_students=total_students,
                             class_average=class_average,
                             top_performers=top_performers,
                             weak_students=weak_students,
                             student_names=json.dumps(student_names),
                             student_percentages=json.dumps(student_percentages),
                             subject_names=json.dumps(subjects),
                             subject_averages=json.dumps(subject_averages),
                             performance_distribution=json.dumps([
                                performance_distribution['Excellent'],
                                performance_distribution['Average'],
                                performance_distribution['Poor']
                             ]),
                             user_role=session.get('role'),
                             username=session.get('username'))
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('home.html', students=[], total_students=0, 
                             class_average=0, top_performers=0, weak_students=0,
                             user_role=session.get('role'), username=session.get('username'))

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    """
    Add student route - Admin only
    """
    if request.method == 'POST':
        try:
            student_data = {
                'name': request.form.get('name', '').strip(),
                'roll_number': request.form.get('roll_number', '').strip(),
                'math': float(request.form.get('math', 0)),
                'science': float(request.form.get('science', 0)),
                'english': float(request.form.get('english', 0)),
                'hindi': float(request.form.get('hindi', 0)),
                'social_studies': float(request.form.get('social_studies', 0)),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Validate input
            if not student_data['name'] or not student_data['roll_number']:
                flash('Name and Roll Number are required', 'error')
                return render_template('home.html')
            
            # Check if roll number already exists
            existing = students_collection.find_one({'roll_number': student_data['roll_number']})
            if existing:
                flash('Roll number already exists', 'error')
                return render_template('home.html')
            
            # Insert student
            students_collection.insert_one(student_data)
            flash('Student added successfully!', 'success')
            
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
        
        return redirect(url_for('dashboard'))
    
    return render_template('home.html')

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    """
    Edit student route - Admin only
    """
    try:
        from bson.objectid import ObjectId
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        
        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            updated_data = {
                'name': request.form.get('name', '').strip(),
                'roll_number': request.form.get('roll_number', '').strip(),
                'math': float(request.form.get('math', 0)),
                'science': float(request.form.get('science', 0)),
                'english': float(request.form.get('english', 0)),
                'hindi': float(request.form.get('hindi', 0)),
                'social_studies': float(request.form.get('social_studies', 0)),
                'updated_at': datetime.now()
            }
            
            # Validate input
            if not updated_data['name'] or not updated_data['roll_number']:
                flash('Name and Roll Number are required', 'error')
                return render_template('edit_student.html', student=student)
            
            # Check if roll number already exists (excluding current student)
            existing = students_collection.find_one({
                'roll_number': updated_data['roll_number'],
                '_id': {'$ne': ObjectId(student_id)}
            })
            if existing:
                flash('Roll number already exists', 'error')
                return render_template('edit_student.html', student=student)
            
            # Update student
            students_collection.update_one(
                {'_id': ObjectId(student_id)},
                {'$set': updated_data}
            )
            flash('Student updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('edit_student.html', student=student)
        
    except Exception as e:
        flash(f'Error editing student: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete_student/<student_id>')
@login_required
@admin_required
def delete_student(student_id):
    """
    Delete student route - Admin only
    """
    try:
        from bson.objectid import ObjectId
        students_collection.delete_one({'_id': ObjectId(student_id)})
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/search_students')
@login_required
def search_students():
    """
    Search students route
    """
    search_term = request.args.get('q', '')
    
    try:
        students = list(students_collection.find({
            '$or': [
                {'name': {'$regex': search_term, '$options': 'i'}},
                {'roll_number': {'$regex': search_term, '$options': 'i'}}
            ]
        }))
        
        return render_template('home.html', 
                             students=students,
                             user_role=session.get('role'),
                             username=session.get('username'),
                             search_term=search_term)
        
    except Exception as e:
        flash(f'Error searching: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/generate_report/<student_id>')
@login_required
@admin_required
def generate_report(student_id):
    """
    Generate PDF report for student - Admin only
    """
    try:
        from bson.objectid import ObjectId
        student = students_collection.find_one({'_id': ObjectId(student_id)})
        
        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Calculate metrics
        marks = [
            student.get('math', 0),
            student.get('science', 0),
            student.get('english', 0),
            student.get('hindi', 0),
            student.get('social_studies', 0)
        ]
        total_marks = sum(marks)
        percentage = round((total_marks / 500) * 100, 2)
        
        # Get all students for ranking
        all_students = list(students_collection.find())
        
        # Calculate ranks for all students
        ranked_students = []
        for s in all_students:
            s_marks = [
                s.get('math', 0),
                s.get('science', 0),
                s.get('english', 0),
                s.get('hindi', 0),
                s.get('social_studies', 0)
            ]
            s_total = sum(s_marks)
            s_percentage = round((s_total / 500) * 100, 2) if s_total > 0 else 0
            ranked_students.append({
                'student': s,
                'percentage': s_percentage
            })
        
        # Sort and find rank
        ranked_students.sort(key=lambda x: x['percentage'], reverse=True)
        rank = 1
        for rs in ranked_students:
            if rs['student']['_id'] == student['_id']:
                break
            rank += 1
        
        status = get_performance_status(percentage)
        
        # Generate PDF
        pdf_buffer = BytesIO()
        elements = []
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4F46E5'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#6366F1'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Add title
        elements.append(Paragraph("Student Academic Report", title_style))
        elements.append(Spacer(1, 0.5 * inch))
        
        # Student Info
        info_data = [
            ['Student Name:', student['name']],
            ['Roll Number:', student['roll_number']],
            ['Rank:', f'#{rank}'],
            ['Percentage:', f'{percentage}%'],
            ['Status:', status]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4F46E5')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Marks Table
        marks_data = [
            ['Subject', 'Marks', 'Maximum Marks'],
            ['Mathematics', student.get('math', 0), 100],
            ['Science', student.get('science', 0), 100],
            ['English', student.get('english', 0), 100],
            ['Hindi', student.get('hindi', 0), 100],
            ['Social Studies', student.get('social_studies', 0), 100],
            ['Total', total_marks, 500]
        ]
        
        marks_table = Table(marks_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        marks_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ]))
        
        elements.append(marks_table)
        
        # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'student_report_{student["roll_number"]}.pdf'
)
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# =================================================
# HELPER FUNCTIONS
# =================================================

def calculate_rank(students, current_student):
    """
    Calculate rank for a student
    """
    try:
        # Calculate percentages for all students
        student_percentages = []
        for s in students:
            marks = [
                s.get('math', 0),
                s.get('science', 0),
                s.get('english', 0),
                s.get('hindi', 0),
                s.get('social_studies', 0)
            ]
            total = sum(marks)
            percentage = (total / 500) * 100 if total > 0 else 0
            student_percentages.append({
                'student': s,
                'percentage': percentage
            })
        
        # Sort by percentage
        student_percentages.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Find rank
        rank = 1
        for sp in student_percentages:
            if sp['student']['_id'] == current_student['_id']:
                return rank
            rank += 1
        
        return 0
        
    except Exception:
        return 0

def get_performance_status(percentage):
    """
    Get performance status based on percentage
    """
    if percentage >= 75:
        return 'Excellent'
    elif percentage >= 50:
        return 'Average'
    else:
        return 'Poor'

# =================================================
# MAIN EXECUTION
# =================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
