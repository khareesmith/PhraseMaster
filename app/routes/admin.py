from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from app.models.db import get_db_connection, User, Submission, Challenge, get_user_by_email, create_user, update_username
from app.utils.auth import admin_required
from app.utils.email import is_valid_email
from app.utils.auth import is_strong_password
from app.utils.vote import format_category_name
import bleach
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    session_db = get_db_connection()
    try:
        user_count = session_db.query(User).count()
        submission_count = session_db.query(Submission).count()
        challenge_count = session_db.query(Challenge).count()
        recent_submissions = session_db.query(Submission).order_by(Submission.date.desc()).limit(5).all()
        
        # Format categories for recent submissions
        for submission in recent_submissions:
            submission.formatted_category = format_category_name(submission.category)
            
        return render_template('admin/dashboard.html', 
                                user_count=user_count, 
                                submission_count=submission_count, 
                                challenge_count=challenge_count,
                                recent_submissions=recent_submissions)
    finally:
        session_db.close()

@admin_bp.route('/users')
@admin_required
def list_users():
    session_db = get_db_connection()
    try:
        users = session_db.query(User).all()
        return render_template('admin/users.html', users=users)
    finally:
        session_db.close()

@admin_bp.route('/create_user', methods=['GET', 'POST'])
@admin_required
def create_new_user():
    if request.method == 'POST':
        email = bleach.clean(request.form['email'])
        name = bleach.clean(request.form['name'])
        password = bleach.clean(request.form['password'])
        
        if not is_valid_email(email):
            flash('Invalid email address.', 'error')
            return render_template('admin/create_user.html')
        
        password_result = is_strong_password(password)
        if password_result['score'] < 3:
            flash('Password is not strong enough.', 'error')
            return render_template('admin/create_user.html')
        
        session_db = get_db_connection()
        try:
            existing_user = get_user_by_email(session_db, email)
            if existing_user:
                flash('A user with this email already exists.', 'error')
                return render_template('admin/create_user.html')
            
            new_user = User(email=email, name=name)
            new_user.set_password(password)
            session_db.add(new_user)
            session_db.commit()
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.list_users'))
        finally:
            session_db.close()
    
    return render_template('admin/create_user.html')

@admin_bp.route('/update_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def update_user(user_id):
    session_db = get_db_connection()
    try:
        user = session_db.query(User).get(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin.list_users'))
        
        if request.method == 'POST':
            new_name = bleach.clean(request.form['name'])
            new_email = bleach.clean(request.form['email'])
            
            user.name = new_name
            user.email = new_email
            user.login_streak = int(request.form['login_streak'])
            user.submission_streak = int(request.form['submission_streak'])
            user.voting_streak = int(request.form['voting_streak'])
            user.is_admin = 'is_admin' in request.form
            user.email_verified = 'email_verified' in request.form
            
            # Handle votes_per_category (JSONB field)
            try:
                votes_per_category = json.loads(request.form['votes_per_category'])
                user.votes_per_category = votes_per_category
            except json.JSONDecodeError:
                flash('Invalid JSON for votes per category', 'error')
                return render_template('admin/update_user.html', user=user)

            update_username(session_db, user.id, new_name)
            session_db.commit()
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.list_users'))
        
        return render_template('admin/update_user.html', user=user)
    finally:
        session_db.close()

@admin_bp.route('/submissions')
@admin_required
def list_submissions():
    session_db = get_db_connection()
    try:
        submissions = session_db.query(Submission).all()
        for submission in submissions:
            submission.formatted_category = format_category_name(submission.category)
        
        return render_template('admin/submissions.html', submissions=submissions)
    finally:
        session_db.close()

@admin_bp.route('/challenges')
@admin_required
def list_challenges():
    session_db = get_db_connection()
    try:
        challenges = session_db.query(Challenge).all()
        for challenge in challenges:
            challenge.formatted_category = format_category_name(challenge.category)
        
        return render_template('admin/challenges.html', challenges=challenges)
    finally:
        session_db.close()

@admin_bp.route('/edit_submission/<int:submission_id>', methods=['GET', 'POST'])
@admin_required
def edit_submission(submission_id):
    session_db = get_db_connection()
    try:
        submission = session_db.query(Submission).get(submission_id)
        if not submission:
            flash('Submission not found.', 'error')
            return redirect(url_for('admin.list_submissions'))
        
        if request.method == 'POST':
            submission.user_phrase = bleach.clean(request.form['user_phrase'])
            submission.votes = int(request.form['votes'])
            
            # Handle date editing with MM/DD/YYYY format
            try:
                new_date = datetime.strptime(request.form['date'], '%m/%d/%Y').date()
                submission.date = new_date
            except ValueError:
                flash('Invalid date format. Please use MM/DD/YYYY.', 'error')
                return render_template('admin/edit_submission.html', submission=submission)
            
            session_db.commit()
            flash('Submission updated successfully.', 'success')
            return redirect(url_for('admin.list_submissions'))
        
        return render_template('admin/edit_submission.html', submission=submission)
    finally:
        session_db.close()

@admin_bp.route('/edit_challenge/<int:challenge_id>', methods=['GET', 'POST'])
@admin_required
def edit_challenge(challenge_id):
    session_db = get_db_connection()
    try:
        challenge = session_db.query(Challenge).get(challenge_id)
        if not challenge:
            flash('Challenge not found.', 'error')
            return redirect(url_for('admin.list_challenges'))
        
        if request.method == 'POST':
            challenge.original_challenge = bleach.clean(request.form['original_challenge'])
            challenge.category = bleach.clean(request.form['category'])
            
            # Handle date editing with MM/DD/YYYY format
            try:
                new_date = datetime.strptime(request.form['date'], '%m/%d/%Y').date()
                challenge.date = new_date
            except ValueError:
                flash('Invalid date format. Please use MM/DD/YYYY.', 'error')
                return render_template('admin/edit_challenge.html', challenge=challenge)
            
            session_db.commit()
            flash('Challenge updated successfully.', 'success')
            return redirect(url_for('admin.list_challenges'))
        
        return render_template('admin/edit_challenge.html', challenge=challenge)
    finally:
        session_db.close()