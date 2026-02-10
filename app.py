import os
from flask import Flask, flash, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import mysql.connector
from datetime import datetime



app = Flask(__name__)
app.secret_key = 'randomsecretkeyfornow'

bcrypt = Bcrypt(app)

def getdb():

    conn = mysql.connector.connect(
        host = "softwarefinal.cd2am0uc4s40.us-east-2.rds.amazonaws.com",
        user = "admin",
        password  = "SoftwareFinal1!",
        database ="softwarefinal",
        port = 3306
    )

    return conn

from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, password_hash, points, email, role, fil):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.points = points
        self.filepath = fil

    def get_id(self):
        return self.username

login_manager = LoginManager()
login_manager.init_app(app)
#if a user tries to access a login_required page, redirect to login page
login_manager.login_view = 'login'

@login_manager.user_loader  
def load_user(username):
    db = getdb()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM login WHERE username= %s", (username,))
    row = cursor.fetchone()
    if row:
        return User(*row) 
    return None
    

@app.route('/')
def home():

    print(bcrypt.generate_password_hash("manager").decode('utf-8'))
    db = getdb()
    cursor = db.cursor(dictionary=True)

    user_role = None
    if current_user.is_authenticated:
        user_role = current_user.role

    if user_role == 'admin' or user_role == 'manager':

         cursor.execute("""
          select * from jobs join login on jobs.username = login.username
          order by jobs.date ASC             
        """)

    else:
        cursor.execute("""
            SELECT 
                jobs.jobid,
                jobs.username,
                jobs.imagepath,
                jobs.title,
                jobs.description,
                jobs.status,
                jobs.date,
                jobs.type,
                login.filepath AS user_icon
            FROM jobs
            JOIN login ON jobs.username = login.username
            WHERE jobs.status = 'active'
            ORDER BY jobs.date ASC
        """)
    
    name = current_user.username if current_user.is_authenticated else None
    jobs = cursor.fetchall()
    
    return render_template('homepage.html', jobs=jobs, user_role = user_role, name= name)

@app.route('/loginuser', methods=['GET', 'POST'])
def loginuser():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        db = getdb()

        querey = "select * from login where username = %s"
    
        cursor = db.cursor()
        cursor.execute(querey, (username,))

        results = cursor.fetchall()

        
        if results and bcrypt.check_password_hash(results[0][1], password):
            
            user = User(
                results[0][0],
                results[0][1],
                results[0][2],
                results[0][3],
                results[0][4],
                results[0][5],
            )

            login_user(user)

            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and/or password')

            return render_template('login.html')


@app.route('/registeruser', methods=['GET', 'POST'])
def registeruser():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()
        file = request.files.get('pic')

        file_path = os.path.join('static','user icons', file.filename)
        dbfile = f"user icons/{file.filename}"
        file.save(file_path)

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))
        

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        

        db = getdb()

        cursor = db.cursor()

        cursor.execute("select * from login where username = %s", (username,))

        results = cursor.fetchone()

        if not results:

            querey = "insert into login(username, password, email, role, filepath, points) values (%s, %s, %s, %s, %s, %s)"

            cursor.execute(querey, (username, hashed_password, email, 'user', dbfile, 0))
            db.commit()

            user = User(username, hashed_password, 0, email, 'user',file )
            login_user(user)
            return redirect(url_for('home'))

        else:
        
            flash("username taken try another")
        
            return render_template('register.html')



@app.route('/approve/<int:job_id>')
@login_required
def approve(job_id):

    db = getdb()
    cusor = db.cursor()

    querey = "update jobs set status = 'active' where jobid = %s"

    cusor.execute(querey, (job_id,))
    db.commit()

    return redirect(url_for('home'))

@app.route('/delete/<int:job_id>')
@login_required
def delete(job_id):

    db = getdb()
    cusor = db.cursor()

    querey = "update jobs set status = 'archived' where jobid = %s"

    cusor.execute(querey, (job_id,))
    db.commit()

    return redirect(url_for('home'))



@app.route('/post')
@login_required
def create_post():
    return render_template('post.html')


@app.route('/search')
@login_required
def search():
    query = request.args.get('q') # Get the search term from the URL
    results = []
    
    if query:
        db = getdb()
        cursor = db.cursor(dictionary=True)
        
        # Search for jobs (actions) that match the title or description
        # Using %s with LIKE for partial matches
        search_term = f"%{query}%"
        
        sql = """
            SELECT 
                jobs.jobid,
                jobs.username,
                jobs.imagepath,
                jobs.title,
                jobs.description,
                jobs.status,
                jobs.date,
                jobs.type,
                login.filepath AS user_icon
            FROM jobs
            JOIN login ON jobs.username = login.username
            WHERE (jobs.title LIKE %s OR jobs.description LIKE %s)
            AND jobs.status = 'active'
            ORDER BY jobs.date DESC
        """
        
        cursor.execute(sql, (search_term, search_term))
        results = cursor.fetchall()
        
        cursor.close()
        db.close()
    
    return render_template('search.html', results=results, query=query)

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/rewards')
@login_required
def rewards():
    return render_template('rewards.html', points = current_user.points)

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/postjob', methods = ["POST"])
@login_required
def postjob():

    file = request.files.get('image')
    title  = request.form.get('Title')
    description = request.form.get('description')
    type = request.form.get('category')
    status = "pending"
    date = datetime.today()
    file_path = os.path.join('static', 'uploads', file.filename)
    dbfile = f"uploads/{file.filename}"

    file.save(file_path)

    db = getdb()    
    cursor = db.cursor()
    querey = "insert into jobs(username, imagepath, title, description, status,date, type) values (%s,%s,%s,%s,%s,%s,%s)"

    cursor.execute(querey, (current_user.get_id(), dbfile, title ,description, status, date, type,))
    db.commit()
    return redirect(url_for('home'))

@app.route('/deleteuser/<username>')
@login_required
def deleteuser(username):
    db = getdb()
    cursor = db.cursor()

    querey = "delete from login where username = %s"

    cursor.execute(querey, (username,))

    querey = "delete from jobs where username = %s"

    cursor.execute(querey, (username,))
    db.commit()

    return redirect(url_for('home'))


@app.route('/getpoints/<int:jobid>')
@login_required
def getpoints(jobid):
    
    db = getdb()
    cursor = db.cursor(dictionary= True)

    querey = "select points from login where username = %s"

    cursor.execute(querey, (current_user.get_id(),))
    
    results = cursor.fetchone()

    points = results['points']

    points = points +10

    cursor.execute("UPDATE login SET points = %s WHERE username = %s", (points, current_user.get_id()))

    cursor.execute("update jobs set status = 'archived' where jobid = %s", (jobid,))

    db.commit()

    return redirect(url_for('home'))
    
if __name__ == '__main__':
    app.run(debug=True)

