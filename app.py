from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, send_file, send_from_directory, current_app
from flask_session import Session
from werkzeug.utils import secure_filename
import pymysql
import json
import numpy as np
import re
from datetime import datetime
import face_recognition
from PIL import Image
from functools import wraps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Image as RLImage
import os
import traceback

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Constants
PARTY_LOGO_FOLDER = os.path.join('static', 'party_logos')
FACE_DATA_FOLDER = os.path.join('static','face_data')
ENCODING_DIR = os.path.join('static', 'face_encodings')
os.makedirs(PARTY_LOGO_FOLDER, exist_ok=True)
os.makedirs(FACE_DATA_FOLDER, exist_ok=True)
os.makedirs(ENCODING_DIR, exist_ok=True)

# Upload folder config
app.config['UPLOAD_FOLDER'] = FACE_DATA_FOLDER

# Allowed extensions (define globally)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

TEMP_UPLOAD_FOLDER = os.path.join('static', 'temp_faces')
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)


#-- Database configuration--------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'db': 'voting_system',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if role == 'admin' and 'admin' not in session:
                flash('Please login as admin.', 'warning')
                return redirect(url_for('login'))
            elif role == 'user' and 'user' not in session:
                flash('Please login as user.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

#---------------------home page---------------------
@app.route('/')
def home():
    return render_template('home.html')

#---------------------login page---------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        identifier = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        if role == 'admin':
            cursor.execute('SELECT * FROM admins WHERE username = %s', (identifier,))
            admin = cursor.fetchone()
            if admin and admin['password'] == password:
                session.clear()
                session['admin'] = admin['id']
                session['admin_name'] = admin['username']
                flash('Admin login successful.', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials.', 'danger')
        else:
            cursor.execute('SELECT * FROM users WHERE epic_no = %s OR phone = %s', (identifier, identifier))
            user = cursor.fetchone()
            if user and user['password'] == password:
                session.clear()
                session['user'] = user['id']
                session['user_name'] = user['name']
                flash('User login successful.', 'success')
                return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid user credentials.', 'danger')

        cursor.close()
        conn.close()

    return render_template('login.html')

#---------------------password strength checker---------------------
def is_strong_password(password):
    """Checks if password is at least 12 characters, has uppercase, lowercase, digit, and special character."""
    if (len(password) < 12 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'\d', password) or
        not re.search(r'[\W_]', password)):
        return False
    return True

#---------------------save face encoding---------------------
def save_face_encoding(user_id, image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if not encodings:
            return False, "No face detected in the image."

        encoding = encodings[0]

        # Check against existing encodings
        for file in os.listdir(ENCODING_DIR):
            existing_path = os.path.join(ENCODING_DIR, file)
            existing_encoding = np.load(existing_path)
            matches = face_recognition.compare_faces([existing_encoding], encoding, tolerance=0.6)
            if True in matches:
                return False, "This face is already registered with another user."

        # Save encoding if it's unique
        encoding_path = os.path.join(ENCODING_DIR, f'user_{user_id}.npy')
        np.save(encoding_path, encoding)

        return True, "Face encoding saved successfully."
    except Exception as e:
        return False, f"Error processing face image: {e}"
    

#---------------------user registration---------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        voter_id = request.form.get('voter_id')
        epic_no = request.form.get('epic_no')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Validate date of birth and age
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            today = datetime.today()
            age = (today - dob_date).days // 365
            if age < 18:
                flash('You must be at least 18 years old to register.')
                return redirect(request.url)
        except Exception:
            flash('Invalid date of birth format.')
            return redirect(request.url)

        # Validate phone number
        if not re.fullmatch(r'\d{10}', phone):
            flash('Phone number must be exactly 10 digits.')
            return redirect(request.url)

        # Validate EPIC number (6–12 alphanumeric characters)
        if not re.fullmatch(r'[A-Za-z0-9]{6,12}', epic_no):
            flash('EPIC number must be 6–12 characters long and alphanumeric.')
            return redirect(request.url)

        # Validate password strength
        if not is_strong_password(password):
            flash('Password must be at least 12 characters long and include uppercase, lowercase, number, and special character.')
            return redirect(request.url)

        if 'face_image' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['face_image']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            img = face_recognition.load_image_file(file)
            uploaded_encodings = face_recognition.face_encodings(img)
            if not uploaded_encodings:
                flash('No face detected in the uploaded image.')
                return redirect(request.url)

            uploaded_encoding = uploaded_encodings[0]
            duplicate_found = False
            for existing_file in os.listdir(FACE_DATA_FOLDER):
                if existing_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    existing_img_path = os.path.join(FACE_DATA_FOLDER, existing_file)
                    existing_img = face_recognition.load_image_file(existing_img_path)
                    existing_encodings = face_recognition.face_encodings(existing_img)
                    if existing_encodings:
                        distance = face_recognition.face_distance([existing_encodings[0]], uploaded_encoding)[0]
                        if distance < 0.45:
                            duplicate_found = True
                            break

            if duplicate_found:
                flash('This face image is already registered with another account.')
                return redirect(request.url)

            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # Check for existing voter_id, epic_no or phone
                cursor.execute("SELECT * FROM users WHERE voter_id = %s OR epic_no = %s OR phone = %s",
                               (voter_id, epic_no, phone))
                if cursor.fetchone():
                    flash('A user with the same Voter ID, EPIC number, or phone number already exists.')
                    return redirect(request.url)

                # Insert into DB
                cursor.execute(
                    """
                    INSERT INTO users (name, voter_id, epic_no, dob, phone, password)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (name, voter_id, epic_no, dob, phone, password)
                )
                conn.commit()
                user_id = cursor.lastrowid

                # Save face image
                filename = f"user_{user_id}.jpg"
                filepath = os.path.join(FACE_DATA_FOLDER, filename)
                file.seek(0)
                file.save(filepath)

                # Update DB with image path
                relative_path = os.path.join('face_data', filename)
                cursor.execute("UPDATE users SET face_image=%s WHERE id=%s", (relative_path, user_id))
                conn.commit()

                cursor.close()
                conn.close()

                flash('Registration successful! Please login.')
                return redirect(url_for('login'))

            except Exception as e:
                flash('Database error: ' + str(e))
                if conn:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                return redirect(request.url)
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return redirect(request.url)

    return render_template('register.html')

#---------------------user dashboard---------------------
@app.route('/user/dashboard')
@login_required('user')
def user_dashboard():
    user_id = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM parties')
    parties = cursor.fetchall()

    cursor.execute('SELECT * FROM votes WHERE user_id = %s', (user_id,))
    vote = cursor.fetchone()

    already_voted = vote is not None
    just_voted = session.pop('just_voted', False)  # Only True immediately after voting

    cursor.close()
    conn.close()

    return render_template('user_dashboard.html',  # fixed file name
                           parties=parties,
                           already_voted=already_voted,
                           just_voted=just_voted,
                           user_id=user_id)
    

#---------------------user vote---------------------
@app.route('/vote', methods=['POST'])
@login_required('user')
def vote():
    user_id = session.get('user')  
    if not user_id:
        flash('User not logged in.', 'danger')
        return redirect(url_for('login'))

    party_id = request.form.get('party_id')
    if not party_id:
        flash('No party selected.', 'danger')
        return redirect(url_for('user_dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already voted
        cursor.execute('SELECT * FROM votes WHERE user_id = %s', (user_id,))
        if cursor.fetchone():
            flash('You have already voted.', 'warning')
            return redirect(url_for('user_dashboard'))

        # Record the vote
        cursor.execute('INSERT INTO votes (user_id, party_id) VALUES (%s, %s)', (user_id, party_id))
        conn.commit()

        session['just_voted'] = True  # trigger thank-you message

    except Exception as e:
        conn.rollback()
        flash(f'Database error: {e}', 'danger')

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('user_dashboard'))


#---------------------admin dashboard---------------------
@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM parties')
    parties = cursor.fetchall()

    cursor.execute('SELECT party_id, COUNT(*) as vote_count FROM votes GROUP BY party_id')
    votes = cursor.fetchall()

    votes_count = {v['party_id']: v['vote_count'] for v in votes}

    party_names = [party['name'] for party in parties]
    party_votes = [votes_count.get(party['id'], 0) for party in parties]
    party_colors = [party['color'] for party in parties]

    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html',
                           parties=parties,
                           votes_count=votes_count,
                           party_names=json.dumps(party_names),
                           party_votes=json.dumps(party_votes),
                           party_colors=json.dumps(party_colors))

#---------------------admin login---------------------
@app.route('/admin/register_user', methods=['GET', 'POST'])
@login_required('admin')
def admin_register_user():
    if request.method == 'POST':
        name = request.form['name']
        voter_id = request.form['voter_id']
        epic_no = request.form['epic_no']
        dob = request.form['dob']
        phone = request.form['phone']
        password = request.form['password']

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Check if voter_id, epic_no, or phone already exists
                cursor.execute('SELECT * FROM users WHERE voter_id = %s OR epic_no = %s OR phone = %s',
                               (voter_id, epic_no, phone))
                existing = cursor.fetchone()

                if existing:
                    flash('Voter ID, EPIC No, or Phone already registered.', 'warning')
                    return redirect(url_for('admin_register_user'))

                # Insert new user
                cursor.execute('''
                    INSERT INTO users (name, voter_id, epic_no, dob, phone, password)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (name, voter_id, epic_no, dob, phone, password))

            connection.commit()
            flash('User added successfully.', 'success')
            return redirect(url_for('admin_list_users'))  # ✅ Redirect here after success

        finally:
            connection.close()

    return render_template('admin_register_user.html')



#---------------------update party---------------------
@app.route('/admin/update_party/<int:party_id>', methods=['POST'])
@login_required('admin')
def admin_update_party(party_id):
    connection = get_db_connection()  # Use the same get_db_connection() function as before

    name = request.form['name']
    color = request.form['color']

    logo_file = request.files.get('logo')
    logo_filename = None
    if logo_file and logo_file.filename:
        logo_filename = secure_filename(logo_file.filename)
        save_path = os.path.join(PARTY_LOGO_FOLDER, logo_filename)
        logo_file.save(save_path)

    try:
        with connection.cursor() as cursor:
            if logo_filename:
                cursor.execute('UPDATE parties SET name=%s, color=%s, logo=%s WHERE id=%s',
                               (name, color, logo_filename, party_id))
            else:
                cursor.execute('UPDATE parties SET name=%s, color=%s WHERE id=%s',
                               (name, color, party_id))
        connection.commit()
        flash('Party updated successfully', 'success')
    finally:
        connection.close()

    return redirect(url_for('admin_manage_parties'))

#---------------------delete party---------------------
@app.route('/admin/delete_party/<int:party_id>', methods=['POST'])
@login_required('admin')
def delete_party(party_id):
    connection = get_db_connection()  # your pymysql connection function
    try:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM parties WHERE id = %s', (party_id,))
        connection.commit()
        flash('Party deleted successfully.', 'success')
    finally:
        connection.close()
    return redirect(url_for('admin_manage_parties'))

#---------------------manage parties---------------------
@app.route('/admin/manage_parties', methods=['GET', 'POST'])
@login_required('admin')
def admin_manage_parties():
    connection = get_db_connection()  # your pymysql connection function
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            if request.method == 'POST':
                name = request.form['name']
                color = request.form['color']
                logo = request.files.get('logo')

                logo_filename = ''
                if logo and logo.filename != '':
                    logo_filename = secure_filename(logo.filename)
                    save_path = os.path.join(PARTY_LOGO_FOLDER, logo_filename)
                    logo.save(save_path)

                cursor.execute(
                    'INSERT INTO parties (name, color, logo) VALUES (%s, %s, %s)',
                    (name, color, logo_filename)
                )
                connection.commit()
                flash('Party added successfully.', 'success')
                return redirect(url_for('admin_manage_parties'))

            cursor.execute('SELECT * FROM parties')
            parties = cursor.fetchall()

    finally:
        connection.close()

    return render_template('admin_manage_parties.html', parties=parties)

# --------------------- Admin Live Results ---------------------
@app.route('/admin/live_results')
def admin_live_results():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM parties')
            parties = cursor.fetchall()

            for party in parties:
                cursor.execute('SELECT COUNT(*) AS vote_count FROM votes WHERE party_id = %s', (party['id'],))
                result = cursor.fetchone()
                party['votes'] = result['vote_count'] if result else 0

        dashboard_url = url_for('admin_dashboard')  # <- change this to match your actual admin dashboard route

    finally:
        connection.close()

    return render_template('admin_live_results.html', parties=parties, dashboard_url=dashboard_url)


# --------------------- User Live Results ---------------------
@app.route('/user/live_results')
def user_live_results():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM parties')
            parties = cursor.fetchall()

            for party in parties:
                cursor.execute('SELECT COUNT(*) AS vote_count FROM votes WHERE party_id = %s', (party['id'],))
                result = cursor.fetchone()
                party['votes'] = result['vote_count'] if result else 0

    finally:
        connection.close()

    return render_template('user_live_results.html', parties=parties)

#--------------------- List Users ---------------------
@app.route('/admin/users')
@login_required('admin')
def admin_list_users():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()
    finally:
        connection.close()

    return render_template('admin_list_users.html', users=users)


#--------------------- Edit User ---------------------
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required('admin')
def edit_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        voter_id = request.form['voter_id']
        epic_no = request.form['epic_no']
        dob = request.form['dob']
        phone = request.form['phone']
        face_image = request.files.get('face_image')

        # Get current image name from DB
        cursor.execute("SELECT face_image FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        current_image = user['face_image'] if user else None

        # Save new face image if provided
        if face_image and face_image.filename:
            filename = secure_filename(f"user_{user_id}_" + face_image.filename)
            image_path = os.path.join('static/face_data', filename)
            face_image.save(image_path)
            face_image_name = filename
        else:
            face_image_name = current_image

        # Update user
        cursor.execute("""
            UPDATE users
            SET name=%s, voter_id=%s, epic_no=%s, dob=%s, phone=%s, face_image=%s
            WHERE id=%s
        """, (name, voter_id, epic_no, dob, phone, face_image_name, user_id))

        conn.commit()
        conn.close()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_list_users'))

    # GET request - load form with current data
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    return render_template("edit_user.html", user=user)


#--------------------- Delete User ---------------------
@app.route('/admin/users/delete/<int:user_id>')
@login_required('admin')
def admin_delete_user(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            connection.commit()
            flash('User deleted successfully.', 'success')
    finally:
        connection.close()

    return redirect(url_for('admin_list_users'))

#---------------------reset all users, parties, votes, and admin---------------------
@app.route('/reset_all', methods=['GET', 'POST'])
def reset_all():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete all images from face_data folder
        face_dir = os.path.join(current_app.root_path, 'static', 'face_data')
        if os.path.exists(face_dir):
            for filename in os.listdir(face_dir):
                file_path = os.path.join(face_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)

        # Delete all logos from party_logos folder
        logos_dir = os.path.join(current_app.root_path, 'static', 'party_logos')
        if os.path.exists(logos_dir):
            for filename in os.listdir(logos_dir):
                file_path = os.path.join(logos_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)

        # Delete Flask session files (if using Flask-Session)
        session_dir = current_app.config.get('SESSION_FILE_DIR')
        if session_dir and os.path.exists(session_dir):
            for filename in os.listdir(session_dir):
                file_path = os.path.join(session_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)

        # Clear database tables and reset IDs
        cursor.execute("DELETE FROM votes")
        cursor.execute("ALTER TABLE votes AUTO_INCREMENT = 1")

        cursor.execute("DELETE FROM users")
        cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")

        cursor.execute("DELETE FROM parties")
        cursor.execute("ALTER TABLE parties AUTO_INCREMENT = 1")

        cursor.execute("DELETE FROM admins")
        cursor.execute("ALTER TABLE admins AUTO_INCREMENT = 1")

        # Insert default admin back
        cursor.execute("""
            INSERT INTO admins (id, username, password)
            VALUES (%s, %s, %s)
        """, (1, 'admin', 'admin@123'))

        conn.commit()

        # Clear session and close DB
        session.clear()
        flash('✅ System reset completed. Admin restored. User IDs reset.', 'success')

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'❌ Error during reset: {e}', 'danger')

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Important: ensure dashboard is reloaded
    return redirect(url_for('admin_dashboard'))


# -------------------- API for Chart Votes --------------------
@app.route('/api/votes_data')
def api_votes_data():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM parties')
            parties = cursor.fetchall()

            cursor.execute('SELECT party_id, COUNT(*) AS vote_count FROM votes GROUP BY party_id')
            votes = cursor.fetchall()
            vote_map = {v['party_id']: v['vote_count'] for v in votes}

            names, votes_list, colors, logos = [], [], [], []

            for party in parties:
                names.append(party['name'])
                votes_list.append(vote_map.get(party['id'], 0))
                colors.append(party['color'])  
                logos.append(party['logo'])    
    finally:
        connection.close()

    return jsonify({
        'names': names,
        'votes': votes_list,
        'colors': colors,
        'logos': logos
    })


# -------------------- Face Path API --------------------
@app.route('/get_face_path/<int:user_id>')
def get_face_path(user_id):
    filename = f"user_{user_id}.jpg"
    filepath = os.path.join('static/face_data', filename)
    if os.path.exists(filepath):
        return jsonify({"path": f"/static/face_data/{filename}"})
    else:
        return jsonify({"error": "Face image not found"}), 404

# -------------------- PDF Report Generation --------------------
@app.route('/download_results')
def download_results():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT parties.name, parties.logo, COUNT(votes.id) AS vote_count
            FROM parties
            LEFT JOIN votes ON parties.id = votes.party_id
            GROUP BY parties.id
        """)
        results = cursor.fetchall()

        vote_data = results if results else []

        cursor.close()
        conn.close()

        if not vote_data:
            flash("No voting data available to generate report.")
            return redirect(url_for('admin_dashboard'))

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Voting_Results_{now}.pdf"
        folder_path = os.path.join(current_app.root_path, "static", "reports")
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, filename)

        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 50, "Live Voting Results Report")

        table_data = [["Party Logo", "Party Name", "Votes"]]

        for item in vote_data:
            # Access as dictionary keys:
            party_name = item.get('name', 'N/A')
            logo_filename = item.get('logo', '')
            vote_count = item.get('vote_count', 0)

            full_logo_path = os.path.join(current_app.root_path, "static", "party_logos", logo_filename)

            if logo_filename and os.path.exists(full_logo_path):
                logo_img = RLImage(full_logo_path, width=30, height=30)
            else:
                logo_img = ""

            table_data.append([logo_img, party_name, str(vote_count)])

        table = Table(table_data, colWidths=[100, 200, 100], hAlign='LEFT')

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
        ])
        table.setStyle(style)

        table_width, table_height = table.wrap(0, 0)
        x = (width - table_width) / 2
        y = height - 100 - table_height

        table.drawOn(c, x, y)

        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, 30, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        c.save()

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        import traceback
        print("Error generating PDF:", e)
        traceback.print_exc()
        flash(f"Error generating PDF: {e}")
        return redirect(url_for('admin_dashboard'))

    
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
