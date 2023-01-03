from .auth import login_required
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from lipila.helpers import (
    get_student, get_user, send_email, search_email)
from lipila.db import get_db
import datetime as DT

from lipila.helpers import calculate_amount, calculate_payments, show_recent
from werkzeug.security import generate_password_hash

bp = Blueprint('admin', __name__, url_prefix='/lipila')


@bp.route('/admin/dashboard', methods=('GET', 'POST'))
@login_required
def dashboard():
    conn = get_db()
    db = conn.cursor()
    
    this_month = (DT.date(DT.date.today().isocalendar()[0], 1, 1))
    this_week = (DT.date(DT.date.today().isocalendar()[0], 1, 1))
    this_day = (DT.date(DT.date.today().isocalendar()[0], 1, 1))

    data = show_recent(session['user_id'])
    # select year payments
    data_all = calculate_payments('all', session['user_id'])
    amount_all = calculate_amount('all', session['user_id'])

    # select month payments
    data_month = calculate_payments('month', session['user_id'])
    amount_month = calculate_amount('month', session['user_id'])

    #select week payments
    data_week = calculate_payments('week', session['user_id'])
    amount_week = calculate_amount('week', session['user_id'])

    #select day payments
    data_day = calculate_payments('day', session['user_id'])
    amount_day = calculate_amount('day', session['user_id'])
    
    payments = {'year':data_all, 'month':data_month, 'week':data_week, 'day':data_day}
    total = {'year':amount_all, 'month':amount_month, 'week':amount_week, 'day':amount_day}
    return render_template('admin/dashboard.html', data=data, total=total, payments=payments)

@bp.route('/admin/students', methods=('GET', 'POST'))
@login_required
def show_students():
    conn = get_db()
    db = conn.cursor()
    if request.method == 'GET':
        db.execute(
            "SELECT * from student WHERE school=%s",(session['user_id'],)
        )
        students = db.fetchall()
    return render_template('school/student.html', students=students)

@bp.route('/admin/payments', methods=('GET', 'POST'))
@login_required
def show_payments():
    conn = get_db()
    db = conn.cursor()

    if request.method == 'GET':
        db.execute(
            "SELECT * from school WHERE id=%s",(session['user_id'],)
        )
        school = db.fetchone()

        id = str(school[0])
        db.execute(
                "SELECT * FROM payment WHERE school=%s",(id,)
            )
        payment = db.fetchall()
        
        return render_template('school/payments.html', school=school[3], data=payment)
    

@bp.route('/admin/add', methods = ['GET', 'POST'])
@login_required
def create_student():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        school = session['user_id']
        tuition = request.form.get('tuition')
        program = request.form.get('program')

        conn = get_db()
        db = conn.cursor()
        error = None

        if not firstname:
            error = "firstname is required"
        elif  not lastname:
            error = "lastname is required"
        elif not tuition:
            error = 'tuition is required'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO student (firstname, lastname, school, program,\
                         tuition)\
                             VALUES (%s, %s, %s, %s, %s)",
                    (firstname, lastname, school, program, tuition),
                )
                conn.commit()

            except Exception:
                error = "already registered."
            else:
                flash('student added successfully. Add another')
                return redirect(url_for('admin.create_student'))

        flash(error)
    return render_template('school/create.html')


# Update view
@bp.route('/admin/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def update(id):
    """
        Updates a students information
    """
    student = get_student(id)

    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        school = session['user_id']
        tuition = request.form.get('tuition')
        program = request.form.get('program')

        conn = get_db()
        db = conn.cursor()
        error = None

        if not firstname:
            error = "firstname is required"
        elif  not lastname:
            error = "lastname is required"
        elif not tuition:
            error = 'tuition is required'

        if error is not None:
            flash(error)
        else:
            db.execute(
                "UPDATE student SET firstname = %s,\
                    lastname = %s, school = %s, program = %s,\
                        tuition = %s" 'WHERE id = %s',
                        (firstname, lastname, school, program, tuition,id),
                )
            conn.commit()
            flash('Student Updated Successfully')
            return redirect(url_for('admin.show_students'))

    return render_template('school/update.html', student=student)

# Delete view
@bp.route('/delete/<int:id>', methods=('POST',))
@login_required
def delete(id):
    get_student(id)
    conn = get_db()
    db = conn.cursor()
    db.execute('DELETE FROM student WHERE id = %s', (id,))
    conn.commit()
    flash('Student Deleted Successfully')
    return redirect(url_for('admin.show_students'))

@bp.route('/admin/resetpassword', methods = ['GET', 'POST'])
def reset_password():
    """
        returns a from for the user to confirm registration
    """
    if request.method == 'POST':
        error = None
        email = request.form.get('email')
        if not email:
            error = "Email is required"
        if not error:
            user = search_email(email)
            if user is not None:
                body = "You requested to reset your email"
                msg = "Check your email for a link to reset your password"
                send_email(email, 'Password Reset', body, msg, )
            else:
                flash("User not found!")
            return redirect(url_for('landing'))
    return render_template('admin/reset.html')


# Update admin password view
@bp.route('/admin/changepassword/<int:id>', methods = ['GET', 'POST'])
@login_required
def update_password(id):
    """
        Resets the users password
    """

    if request.method == 'POST':
        password = request.form.get('password')

        conn = get_db()
        db = conn.cursor()
        error = None

        if not password:
            error = "password is required"
    
        if error is not None:
            flash(error)
        else:
            db.execute(
                "UPDATE school SET password = %s" 'WHERE id = %s',
                        (generate_password_hash(password),id),
                )
            conn.commit()
            flash('Password Changed Successfully')
            return redirect(url_for('landing'))
    return render_template('admin/reset_password.html')

@bp.route('/admin/profile', methods = ['GET', 'POST'])
@login_required
def profile():
    """View to edit the users profile"""
    id = session['user_id']
    if request.method == 'POST':
        email = request.form['email']
        mobile = request.form['mobile']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
    
        error = None        
        # admin other detaild
        job = request.form['job']
        school = request.form['school']
        reg_number = request.form['reg_number']

        if not school:
            error = 'School is required.'
        elif not mobile:
            error = 'Mobile is required.'
        elif not firstname:
            error = 'Firstname is required.'
        elif not lastname:
            error = 'Lastname is required.'
        elif not email:
            error = 'Firstname is required.'
        elif not reg_number:
            error = 'Registration number is required.'
        elif not job:
            error = 'Job description is required.'

        if error is None:
            conn = get_db()
            db = conn.cursor()
            db.execute(
                "UPDATE school SET job=%s, school=%s, email=%s, mobile=%s,\
                        reg_number=%s, firstname=%s, lastname=%s" 'WHERE id=%s',
                        (job, school, email, mobile, reg_number, firstname,
                lastname, id),
            )
            conn.commit()
            
            msg = "Profile Updated"
            flash(msg)
            session['school'] = school
            user = get_user(id)
            print(user)
            return render_template('admin/profile.html', user=user)

        flash(error)
    user = get_user(id)
    print(user)
    return render_template('admin/profile.html', user=user)