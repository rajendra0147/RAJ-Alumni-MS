# ./app.py

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from flask_pymongo import PyMongo
from bson import ObjectId
from pymongo import MongoClient
from flask_uploads import UploadSet, configure_uploads, IMAGES
from datetime import datetime
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)


# Secret key for session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


# Database configuration
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
# client = MongoClient('mongodb+srv://rajendra_thakur:chandthakur@cluster0.fcvwo.mongodb.net/alumni?retryWrites=true&w=majority&appName=Cluster0')
mongo = PyMongo(app)
# mongo = client['alumni']


# Upload configuration
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def create_admin_user():
    admin_username = 'admin'
    admin_password = 'admin'
    admin_role = 'Admin'

    # Check if admin user already exists
    existing_admin = mongo.db.users.find_one({"username": admin_username, "role": admin_role})
    
    if existing_admin:
        print("Admin user already exists. Skipping creation.")
    else:
        # Hash the password before storing it
        # hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        admin_user = {
            "username": admin_username,
            "password": hashed_password,
            "role": admin_role
        }
        mongo.db.users.insert_one(admin_user)
        print("Admin user created successfully.")


# Define User model for authentication
class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict.get('_id')
        self.username = user_dict.get('username')
        self.password = user_dict.get('password')
        self.role = user_dict.get('role', 'User')
        self.alumni_id = user_dict.get('alumni_id')

    def is_admin(self):
        return self.role == 'Admin' 

@login_manager.user_loader
def load_user(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})  # Convert to ObjectId
        print(f"load_user: user_id={ObjectId(user_id)}, user={user}")  # Debugging statement
        if user:
            return User(user)
    except Exception as e:
        print(f"Error loading user: {e}")  # Add error logging
    return None

# Routes and view functions
@app.route('/')
def home():
    notifications = mongo.db.notifications.find({}).sort("_id", -1).limit(5)
    upcoming_events = mongo.db.events.find({"date": {"$gte": datetime.today()}}).sort("date", 1).limit(5)
    recent_discussions = mongo.db.discussions.find().sort("_id", -1).limit(5)
    job_posts = mongo.db.job_posts.find().sort("_id", -1).limit(5)
    mentorships = mongo.db.mentorships.find().sort("_id", -1).limit(5)
    return render_template('home.html', upcoming_events=upcoming_events, recent_discussions=recent_discussions, notifications=notifications, job_posts=job_posts, mentorships=mentorships)

@app.route('/dashboard')
@login_required
def dashboard():
    notifications = mongo.db.notifications.find({
        "$or": [
            {"recipients": "all"},
            {"recipients": current_user.username}
        ]
    }).sort("created_at", -1)
    alumni = mongo.db.alumni.find_one({"_id": ObjectId(current_user.alumni_id)})
    print(alumni)
    upcoming_events = mongo.db.events.find({"date": {"$gte": datetime.today()}}).sort("date", 1).limit(5)
    recent_discussions = mongo.db.discussions.find({"author": current_user.username}).sort("_id", -1).limit(5)
    user_jobs = mongo.db.job_posts.find({"posted_by": current_user.username})
    # user_mentorships = mongo.db.mentorships.find({"$or": [{"mentor_name": current_user.username}, {"mentee_name": current_user.username}]})
    user_mentorships = mongo.db.mentorships.find({"posted_by": current_user.username})
    user_events = mongo.db.events.find({"posted_by": current_user.username})
    return render_template('dashboard.html',notifications=notifications, user=current_user, alumni=alumni, upcoming_events=upcoming_events, recent_discussions=recent_discussions, user_jobs=user_jobs, user_mentorships=user_mentorships,user_events=user_events)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        # password = request.form.get('password')
        password = request.form.get('password').encode('utf-8')
        role = request.form.get('role', 'User')
        existing_user = mongo.db.users.find_one({"username": username})
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        elif username and password:
            # hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            new_user = {"username": username, "password": hashed_password, "role":role}
            mongo.db.users.insert_one(new_user)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username and password are required.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        # password = request.form.get('password')
        password = request.form.get('password').encode('utf-8')
        user = mongo.db.users.find_one({"username": username})
        # if user and check_password_hash(user['password'], password):
        if user and bcrypt.checkpw(password, user['password']):
            print(f"login: username={username}, user={user}")  # Debugging statement
            user_obj = User(user)
            login_user(user_obj)
            if user_obj.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    if current_user.is_authenticated:
        user = mongo.db.users.find_one({'username':current_user.username})
        print(user)
        if request.method == 'POST':
            old_password = request.form['old_password'].encode('utf-8')
            # old_hashed_password = generate_password_hash(old_password, method='pbkdf2:sha256')
            if bcrypt.checkpw(old_password, user['password']):
            # if check_password_hash(old_hashed_password, user['password']):
                new_password = request.form['new_password'].encode('utf-8')
                hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt())
                # hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {"password":hashed_password}})
                flash('Password updated successfully!', 'success')
                return redirect(url_for('logout'))
            else:       
                flash('Old password is incorrect.', 'danger')
                return redirect(url_for('update_password'))
        return render_template('change_password.html')
    else:
        return redirect(url_for('index'))



@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('admin.html')

@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def admin_create_user():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        # password = request.form.get('password')
        password = request.form.get('password').encode('utf-8')
        role = request.form.get('role')
        # hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        new_user = {"username": username, "password": hashed_password, "role": role}
        mongo.db.users.insert_one(new_user)
        flash('User created successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('create_user.html')

@app.route('/admin/create_event', methods=['GET', 'POST'])
@login_required
def admin_create_event():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        date = request.form.get('date')
        new_event = {
            "title": title,
            "description": description,
            "date": datetime.strptime(date, '%Y-%m-%d'),
            "location":location
        }
        mongo.db.events.insert_one(new_event)
        flash('Event created successfully!', 'success')
        return redirect(url_for('list_events'))
    return render_template('create_event.html')


@app.route('/admin/create_discussion', methods=['GET', 'POST'])
@login_required
def admin_create_discussion():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        topic = request.form.get('topic')
        content = request.form.get('content')
        category = request.form.get('category')
        new_discussion = {
            "topic": topic,
            "content": content,
            "author": current_user.username,
            "category": category,
            "created_at": datetime.now()
        }
        mongo.db.discussions.insert_one(new_discussion)
        flash('Discussion created successfully!', 'success')
        return redirect(url_for('list_discussions'))
    return render_template('create_discussion.html')

@app.route('/admin/create_job', methods=['GET', 'POST'])
@login_required
def admin_create_job():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        company = request.form.get('company')
        location = request.form.get('location')
        new_job = {
            "title": title,
            "description": description,
            "company": company,
            "location":location,
            "posted_by": current_user.username
        }
        mongo.db.job_posts.insert_one(new_job)
        flash('Job created successfully!', 'success')
        return redirect(url_for('list_jobs'))
    return render_template('create_job.html')

@app.route('/admin/create_mentorship', methods=['GET', 'POST'])
@login_required
def admin_create_mentorship():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        mentor_name = request.form.get('mentor_name')
        mentee_name = request.form.get('mentee_name')
        contact_info = request.form.get('contact_info')
        details = request.form.get('details')
        posted_by = request.form.get('posted_by')
        new_mentorship = {
            "mentor_name": mentor_name,
            "mentee_name": mentee_name,
            "details": details,
            "contact_info": contact_info,
            "posted_by":posted_by
        }
        mongo.db.mentorships.insert_one(new_mentorship)
        flash('Mentorship created successfully!', 'success')
        return redirect(url_for('list_mentorships'))
    return render_template('create_mentorship.html')

@app.route('/admin/view_logs')
@login_required
def admin_view_logs():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    # Logic to view logs goes here
    logs = []  # This should be replaced with actual log fetching logic
    return render_template('view_logs.html', logs=logs)

@app.route('/admin/generate_reports')
@login_required
def admin_generate_reports():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    # Logic to generate reports goes here
    reports = []  # This should be replaced with actual report generation logic
    return render_template('generate_reports.html', reports=reports)

@app.route('/admin/manage_users')
@login_required
def admin_manage_users():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    users = mongo.db.users.find()
    return render_template('manage_users.html', users=users)

@app.route('/admin/manage_events')
@login_required
def admin_manage_events():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    events = mongo.db.events.find()
    return render_template('manage_events.html', events=events)

@app.route('/admin/manage_jobs')
@login_required
def admin_manage_jobs():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    jobs = mongo.db.job_posts.find()
    return render_template('manage_jobs.html', jobs=jobs)

@app.route('/admin/manage_discussions')
@login_required
def admin_manage_discussions():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    discussions = mongo.db.discussions.find()
    return render_template('manage_discussions.html', discussions=discussions)

@app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_manage_users'))

    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role')
        mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"username": username, "role": role}})
        flash('User updated successfully', 'success')
        return redirect(url_for('admin_manage_users'))

    return render_template('edit_user.html', user=user)

@app.route('/admin/delete_user/<user_id>', methods=['POST', 'GET'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('admin_manage_users'))

        if user.username == 'admin':
            flash('Admin Cannot be deleted', 'danger')
        else:
            mongo.db.users.delete_one({"_id": ObjectId(user_id)})
            flash('User deleted successfully', 'success')
    return redirect(url_for('admin_manage_users'))

@app.route('/admin/delete_users', methods=['POST'])
@login_required
def admin_delete_users():
    if not current_user.is_admin():
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('admin_manage_users'))
    user_ids = request.form.getlist('user_ids')
    if user_ids:
        # Convert user_ids to ObjectId and remove the users from the database
        admin_id = ObjectId(current_user.id)

        # mongo.db.users.delete_many({'_id': {'$in': [ObjectId(user_id)  for user_id in user_ids  ]}})
        # flash(f'{len(user_ids)} user(s) deleted successfully.', 'success')

        ids = []
        for user_id in user_ids:
            if ObjectId(user_id) != admin_id:
                ids.append(ObjectId(user_id))
            else:
                flash('Admin Cannot be deleted', 'danger')
                return redirect(url_for('admin_manage_users'))
        
        mongo.db.users.delete_many({'_id': {'$in': ids}})
        flash(f'{len(user_ids)} user(s) deleted successfully.', 'success')
    else:
        flash('No users selected for deletion.', 'warning')

    return redirect(url_for('admin_manage_users'))

@app.route('/admin/delete_event/<event_id>', methods=['POST', 'GET'])
@login_required
def admin_delete_event(event_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            flash('Event not found', 'danger')
            return redirect(url_for('admin_manage_events'))

        mongo.db.events.delete_one({"_id": ObjectId(event_id)})
        flash('Event deleted successfully', 'success')
    return redirect(url_for('admin_manage_events'))

@app.route('/admin/delete_job/<job_id>', methods=['POST', 'GET'])
@login_required
def admin_delete_job(job_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        job = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            flash('Job not found', 'danger')
            return redirect(url_for('admin_manage_jobs'))

        mongo.db.jobs.delete_one({"_id": ObjectId(job_id)})
        flash('Job deleted successfully', 'success')
    return redirect(url_for('admin_manage_jobs'))

@app.route('/admin/edit_discussion/<discussion_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_discussion(discussion_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    discussion = mongo.db.discussions.find_one({"_id": ObjectId(discussion_id)})
    if not discussion:
        flash('Discussion not found', 'danger')
        return redirect(url_for('admin_manage_discussions'))

    if request.method == 'POST':
        topic = request.form.get('topic')
        content = request.form.get('content')
        category = request.form.get('category')
        mongo.db.discussions.update_one({"_id": ObjectId(discussion_id)}, {"$set": {"topic": topic, "content": content, "category": category}})
        flash('Discussion updated successfully', 'success')
        return redirect(url_for('admin_manage_discussions'))

    return render_template('edit_discussion.html', discussion=discussion)

@app.route('/admin/delete_discussion/<discussion_id>', methods=['POST', 'GET'])
@login_required
def admin_delete_discussion(discussion_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        discussion = mongo.db.discussions.find_one({"_id": ObjectId(discussion_id)})
        if not discussion:
            flash('Discussion not found', 'danger')
            return redirect(url_for('admin_manage_discussions'))

        mongo.db.discussions.delete_one({"_id": ObjectId(discussion_id)})
        flash('Discussion deleted successfully', 'success')
    return redirect(url_for('admin_manage_discussions'))




@app.route('/profile')
@login_required
def view_profile():
    alumni = mongo.db.alumni.find_one({"_id": ObjectId(current_user.alumni_id)})
    if alumni:
        return render_template('profile.html', alumni=alumni)
    else:
        return redirect(url_for('create_profile'))

@app.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        graduation_year = request.form.get('graduation_year')
        industry = request.form.get('industry')
        contact_details = request.form.get('contact_details')
        new_alumni = {
            "name": name,
            "graduation_year": graduation_year,
            "industry": industry,
            "contact_details": contact_details
        }
        mongo.db.alumni.insert_one(new_alumni)
        mongo.db.users.update_one({"_id": ObjectId(current_user.id)}, {"$set": {"alumni_id": new_alumni["_id"]}})
        flash('Profile created successfully!', 'success')
        return redirect(url_for('view_profile'))
    return render_template('create_profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    alumni = mongo.db.alumni.find_one({"_id": ObjectId(current_user.alumni_id)})
    if not alumni:
        return redirect(url_for('create_profile'))
    if request.method == 'POST':
        updated_alumni = {
            "name": request.form.get('name'),
            "graduation_year": request.form.get('graduation_year'),
            "industry": request.form.get('industry'),
            "contact_details": request.form.get('contact_details')
        }
        mongo.db.alumni.update_one({"_id": alumni["_id"]}, {"$set": updated_alumni})
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('view_profile'))
    return render_template('edit_profile.html', alumni=alumni)

@app.route('/admin/manage_notifications')
@login_required
def admin_manage_notifications():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    user_notifications = mongo.db.notifications.find()
    return render_template('manage_notifications.html', notifications=user_notifications)



@app.route('/mark_as_read/<notification_id>')
@login_required
def mark_as_read(notification_id):
    notification = mongo.db.notifications.find_one({"_id": ObjectId(notification_id)})
    if notification:
        mongo.db.notifications.update_one({"_id": ObjectId(notification_id)}, {"$set": {"is_read": True}})
    else:
        flash('Notification not found or you do not have permission to mark it as read.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/admin/create_notification', methods=['GET', 'POST'])
@login_required
def admin_create_notification():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        recipients = request.form.getlist('recipients')
        message = request.form.get('message')
        if recipients == "all":
            recipients = "all"
        else:
            recipients = recipients

        notification = {
                "recipients": recipients,
                'message': message,
                'is_read': False,
                'created_at': datetime.utcnow(),
                'created_by': current_user.username
            }
        mongo.db.notifications.insert_one(notification)
        flash('Notification created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    users = mongo.db.users.find()
    return render_template('create_notification.html', users=users)


@app.route('/admin/edit_notification/<notification_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_notification(notification_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    notification = mongo.db.notifications.find_one({"_id": ObjectId(notification_id)})
    if not notification:
        flash('Notification not found', 'danger')
        return redirect(url_for('admin_manage_notifications'))

    if request.method == 'POST':
        message = request.form.get('message')
        recipients = request.form.getlist('recipients')
        if recipients == "all":
            recipients = "all"
        else:
            recipients = recipients

        notification = {
                "recipients": recipients,
                'message': message,
                'is_read': False,
                'created_at': datetime.utcnow(),
                'created_by': current_user.username
            }
        
        mongo.db.notifications.update_one({"_id": ObjectId(notification_id)}, {"$set": notification})
        flash('Notification updated successfully', 'success')
        return redirect(url_for('admin_manage_notifications'))
    users = mongo.db.users.find()
    return render_template('edit_notification.html', notification=notification, users=users)


@app.route('/admin/delete_notification/<notification_id>', methods=['POST', 'GET'])
@login_required
def admin_delete_notification(notification_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        notification = mongo.db.notifications.find_one({"_id": ObjectId(notification_id)})
        if not notification:
            flash('Notification not found', 'danger')
            return redirect(url_for('admin_manage_discussions'))

        mongo.db.notifications.delete_one({"_id": ObjectId(notification_id)})
        flash('Notification deleted successfully', 'success')
    return redirect(url_for('admin_manage_notifications'))

@app.route('/admin/delete_notifications', methods=['POST'])
@login_required
def admin_delete_notifications():
    if not current_user.is_admin():
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('admin_manage_users'))
    notification_ids = request.form.getlist('notification_ids')
    if notification_ids:
        # Convert notification_ids to ObjectId and remove the notifications from the database
        mongo.db.notifications.delete_many({'_id': {'$in': [ObjectId(notification_id) for notification_id in notification_ids]}})
        flash(f'{len(notification_ids)} notification(s) deleted successfully.', 'success')
    else:
        flash('No Notification selected for deletion.', 'warning')

    return redirect(url_for('admin_manage_notifications'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        current_user_profile = mongo.db.users.find_one({'_id': ObjectId(current_user.get_id())})
        mongo.db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$set': {'profile_pic': filename}})
        flash('Profile picture uploaded successfully!', 'success')
    return redirect(url_for('view_profile'))


@app.route('/create_discussion', methods=['GET', 'POST'])
@login_required
def create_discussion():
    if request.method == 'POST':
        topic = request.form.get('topic')
        content = request.form.get('content')
        category = request.form.get('category')
        new_discussion = {
            "topic": topic,
            "content": content,
            "category": category,
            "author": current_user.username,
            "created_at": datetime.now()
        }
        mongo.db.discussions.insert_one(new_discussion)
        flash('Discussion created successfully!', 'success')
        return redirect(url_for('list_discussions'))
    return render_template('create_discussion.html')

@app.route('/discussions')
@login_required
def list_discussions():
    user_discussions = mongo.db.discussions.find({"author":current_user.username})
    all_discussions = mongo.db.discussions.find().sort("_id", -1)
    return render_template('discussions.html', discussions=all_discussions, user_discussions=user_discussions)

@app.route('/discussion/<discussion_id>', methods=['GET', 'POST'])
@login_required
def view_discussion(discussion_id):
    discussion = mongo.db.discussions.find_one({"_id": ObjectId(discussion_id)})
    if not discussion:
        flash('Discussion not found.', 'danger')
        return redirect(url_for('list_discussions'))

    if request.method == 'POST':
        content = request.form.get('content')
        new_reply = {
            "content": content,
            "author": current_user.username,
            "discussion_id": ObjectId(discussion_id),
            "created_at": datetime.utcnow()
        }
        try:
            mongo.db.replies.insert_one(new_reply)
            flash('Reply posted successfully!', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    replies = list(mongo.db.replies.find({"discussion_id": ObjectId(discussion_id)}))
    return render_template('discussion.html', discussion=discussion, replies=replies)

@app.route('/edit_discussion/<discussion_id>', methods=['GET', 'POST'])
@login_required
def edit_discussion(discussion_id):
    discussion = mongo.db.discussions.find_one({"_id": ObjectId(discussion_id)})
    if not discussion:
        flash('Discussion not found.', 'danger')
        return redirect(url_for('list_discussions'))
    if request.method == 'POST':
        updated_discussion = {
            "topic": request.form.get('topic'),
            "content": request.form.get('content'),
        }
        mongo.db.discussions.update_one({"_id": ObjectId(discussion_id)}, {"$set": updated_discussion})
        flash('Discussion updated successfully!', 'success')
        return redirect(url_for('view_discussion', discussion_id=ObjectId(discussion_id)))
    return render_template('edit_discussion.html', discussion=discussion)

@app.route('/events')
@login_required
def list_events():
    all_events = mongo.db.events.find()
    user_events = mongo.db.events.find({"posted_by": current_user.username})
    print(user_events)
    return render_template('events.html', events=all_events, user_events=user_events)

@app.route('/event/<event_id>')
@login_required
def view_event(event_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    if event:
        return render_template('view_event.html', event=event)
    else:
        flash('Event not found.', 'danger')
        return redirect(url_for('list_events'))

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        date = request.form.get('date')
        new_event = {
            "title": title,
            "description": description,
            "date": datetime.strptime(date, '%Y-%m-%d'),
            "location":location,
            "posted_by":current_user.username
        }
        mongo.db.events.insert_one(new_event)
        flash('Event created successfully!', 'success')
        return redirect(url_for('list_events'))
    return render_template('create_event.html')

@app.route('/edit_event/<event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('list_events'))
    if request.method == 'POST':
        updated_event = {
            "title": request.form.get('title'),
            "description": request.form.get('description'),
            "date": datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            "location": request.form.get('location'),
        }
        mongo.db.events.update_one({"_id": ObjectId(event_id)}, {"$set": updated_event})
        flash('Event updated successfully!', 'success')
        return redirect(url_for('view_event', event_id=ObjectId(event_id)))
    return render_template('edit_event.html', event=event)

@app.route('/event/rsvp/<event_id>')
@login_required
def rsvp_event(event_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('list_events'))

    user = mongo.db.users.find_one({"_id": ObjectId(current_user.get_id())})

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('list_events'))

    # Check if the event is already in the user's RSVP list
    if ObjectId(event_id) not in user.get('events', []):
        mongo.db.users.update_one(
            {"_id": ObjectId(current_user.get_id())},
            {"$push": {"events": ObjectId(event_id)}}
        )
        flash(f'You have successfully RSVP\'d to {event["title"]}', 'success')
    else:
        flash(f'You have already RSVP\'d to {event["title"]}', 'info')
        
    return redirect(url_for('list_events'))

@app.route('/jobs')
@login_required
def list_jobs():
    user_jobs = mongo.db.job_posts.find({"posted_by":current_user.username})
    all_jobs = mongo.db.job_posts.find()
    return render_template('jobs.html', jobs=all_jobs,user_jobs=user_jobs)

@app.route('/job/<job_id>')
@login_required
def view_job(job_id):
    job = mongo.db.job_posts.find_one({"_id": ObjectId(job_id)})
    if job:
        return render_template('view_job.html', job=job)
    else:
        flash('Job not found.', 'danger')
        return redirect(url_for('list_jobs'))

@app.route('/create_job', methods=['GET', 'POST'])
@login_required
def create_job():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        company = request.form.get('company')
        location = request.form.get('location')
        new_job = {
            "title": title,
            "description": description,
            "company": company,
            "location":location,
            "posted_by": current_user.username
        }
        mongo.db.job_posts.insert_one(new_job)
        flash('Job created successfully!', 'success')
        return redirect(url_for('list_jobs'))
    return render_template('create_job.html')

@app.route('/edit_job/<job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = mongo.db.job_posts.find_one({"_id": ObjectId(job_id)})
    if not job:
        flash('Job not found.', 'danger')
        return redirect(url_for('list_jobs'))
    if request.method == 'POST':
        updated_job = {
            "title": request.form.get('title'),
            "description": request.form.get('description'),
            "company": request.form.get('company'),
            "location":request.form.get('location')
        }
        mongo.db.job_posts.update_one({"_id": ObjectId(job_id)}, {"$set": updated_job})
        flash('Job updated successfully!', 'success')
        return redirect(url_for('view_job', job_id=ObjectId(job_id)))
    return render_template('edit_job.html', job=job)

@app.route('/mentorships')
@login_required
def list_mentorships():
    user_mentorships = mongo.db.mentorships.find({"posted_by":current_user.username})
    all_mentorships = mongo.db.mentorships.find()
    return render_template('mentorships.html', mentorships=all_mentorships, user_mentorships=user_mentorships)

@app.route('/mentorship/<mentorship_id>')
@login_required
def view_mentorship(mentorship_id):
    mentorship = mongo.db.mentorships.find_one({"_id": ObjectId(mentorship_id)})
    if mentorship:
        return render_template('view_mentorship.html', mentorship=mentorship)
    else:
        flash('Mentorship not found.', 'danger')
        return redirect(url_for('list_mentorships'))

@app.route('/create_mentorship', methods=['GET', 'POST'])
@login_required
def create_mentorship():
    if request.method == 'POST':
        mentor_name = request.form.get('mentor_name')
        mentee_name = request.form.get('mentee_name')
        contact_info = request.form.get('contact_info')
        details = request.form.get('details')
        new_mentorship = {
            "mentor_name": mentor_name,
            "mentee_name": mentee_name,
            "details": details,
            "contact_info": contact_info,
            "posted_by": current_user.username
        }
        mongo.db.mentorships.insert_one(new_mentorship)
        flash('Mentorship created successfully!', 'success')
        return redirect(url_for('list_mentorships'))
    return render_template('create_mentorship.html')

@app.route('/edit_mentorship/<mentorship_id>', methods=['GET', 'POST'])
@login_required
def edit_mentorship(mentorship_id):
    mentorship = mongo.db.mentorships.find_one({"_id": ObjectId(mentorship_id)})
    if not mentorship:
        flash('Mentorship not found.', 'danger')
        return redirect(url_for('list_mentorships'))
    if request.method == 'POST':
        updated_mentorship = {
            "mentor_name": request.form.get('mentor_name'),
            "mentee_name": request.form.get('mentee_name'),
            "details": request.form.get('details'),
            "contact_info": request.form.get('contact_info')
        }
        mongo.db.mentorships.update_one({"_id": ObjectId(mentorship_id)}, {"$set": updated_mentorship})
        flash('Mentorship updated successfully!', 'success')
        return redirect(url_for('view_mentorship', mentorship_id=ObjectId(mentorship_id)))
    return render_template('edit_mentorship.html', mentorship=mentorship)

if __name__ == "__main__":
    create_admin_user()
    app.secret_key = os.urandom(24)
    app.run(debug=True)
