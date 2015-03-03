# -*- coding: utf-8 -*-
import os, sqlite3
from itertools import izip_longest
from datetime import datetime as dt
from calendar import monthrange
from flask import Flask, render_template, request, redirect, url_for, abort, \
                    session, send_from_directory, jsonify, g, flash
from werkzeug import secure_filename
from werkzeug.security import check_password_hash
app = Flask(__name__, template_folder="html")
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), "pears.db")
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

'''
    Used for finding environment variables through configuration
    if a default is not given, the site will raise an exception
'''
def get_env_variable(var_name, default=-1):
    try:
        return os.environ[var_name]
    except KeyError:
        if default != -1:
            return default
        error_msg = "Set the %s os.environment variable" % var_name
        raise Exception(error_msg)

app.config['SECRET_KEY'] = get_env_variable("PEARS_SECRET_KEY")

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_db()
    return db

def query_db(query, args=(), one=False, update=False):
    cur = get_db().execute(query, args)
    if update:
        return get_db().commit()
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(table, fields=(), args=()):
    # g.db is the database connection
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (
        table,
        ', '.join(fields),
        ', '.join(['?'] * len(args))
    )
    cur = get_db().execute(query, args)
    get_db().commit()
    id = cur.lastrowid
    cur.close()
    return id

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))
        
def user_exists(user):
    return query_db("""SELECT EXISTS(SELECT * FROM user WHERE name = ?)""", [user], one=True)[0]

def email_exists(user):
    return query_db("""SELECT EXISTS(SELECT * FROM user WHERE email = ?)""",[user], one=True)[0]

@app.before_request
def before_request():
  g.user = session.get('user')

'''Access to static files'''
@app.route('/uploads/<user>/<path:filename>')
def uploaded_file(user, filename):
    photo_dir = os.path.join(app.config['UPLOAD_FOLDER'], user)
    ''' need to use this send_from_directory function so that the proper HTTP
        headers are set and HTML audio API can work properly'''
    return send_from_directory(photo_dir, filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/photophoto/')
def home():
    
    as_imgs = query_db("SELECT * FROM img WHERE month in (2, 3) and user=? ORDER BY month DESC, day DESC", ("alexandersimoes@gmail.com",))
    jb_imgs = query_db("SELECT * FROM img WHERE month in (2, 3) and user=? ORDER BY month DESC, day DESC", ("jnoelbasil@gmail.com",))
    # raise Exception(list(izip_longest(as_imgs, jb_imgs)))
    
    pears = []
    for pear in izip_longest(as_imgs, jb_imgs):
        new_pear = []
        for p in pear:
            if p:
                p = dict(p)
                p['date'] = custom_strftime('%B {S}', dt(2015, p['month'], p['day']))
            new_pear.append(p)
        pears.append(new_pear)
    
    return render_template('pears.html', imgs=pears)

@app.route('/photophoto2/')
def home2():
    
    as_imgs = query_db("SELECT * FROM img WHERE month=2 and user=? ORDER BY day DESC", ("alexandersimoes@gmail.com",))
    jb_imgs = query_db("SELECT * FROM img WHERE month=2 and user=? ORDER BY day DESC", ("jnoelbasil@gmail.com",))
    # raise Exception(list(izip_longest(as_imgs, jb_imgs)))
    
    pears = []
    for pear in izip_longest(as_imgs, jb_imgs):
        new_pear = []
        for p in pear:
            if p:
                p = dict(p)
                p['date'] = custom_strftime('%B {S}', dt(2015, p['month'], p['day']))
            new_pear.append(p)
        pears.append(new_pear)
    
    return render_template('pears2.html', imgs=pears)

@app.route('/photophoto/toc/')
def toc():
    months = [(2, "February"),]
    imgs = {}
    for m_id, m_name in months:
        first_day, days_in_month = monthrange(2015, m_id)
        imgs[m_name] = [None] * (days_in_month+1)
        
        month_imgs = query_db("SELECT * FROM img WHERE month=? ORDER BY day DESC", (m_id,))
        for i in month_imgs:
            initials = "as" if "alex" in i["user"] else "jb"
            if not imgs[m_name][i["day"]-1]:
                imgs[m_name][i["day"]-1] = {}
            imgs[m_name][i["day"]-1][initials] = i
    return render_template('toc.html', imgs=imgs)

@app.route('/photophoto/login/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == "POST":
        '''try to find user'''
        user = query_db("SELECT email, password FROM user WHERE email=?", [request.form["email"].lower()], one=True)
        if not user:
            error = "Woopsie wrong username"
            flash(error, "error")
        elif not check_password_hash(user["password"], request.form["pw"]):
            error = "Woopsie wrong password"
            flash(error, "error")
        else:
            session["logged_in"] = True
            session["user"] = user["email"]
            flash("You're so logged in right now", "success")
            return redirect(url_for("home"))
    return render_template("login.html", error=error)

@app.route("/photophoto/logout/")
def logout():
    session.pop("logged_in", None)
    session.pop("user", None)
    flash("yup... you're logged out PEACE", "success")
    return redirect(url_for("home"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ("jpg", "jpeg", "png")

@app.route('/photophoto/upload/', methods=['GET', 'POST'])
@app.route('/photophoto/upload/<int:img>/delete/', defaults={'delete': True}, methods=['GET', 'POST'])
@app.route('/photophoto/upload/<int:img>/', defaults={'delete': False}, methods=['GET', 'POST'])
def upload(img=None, delete=False):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if delete:
        old_img = query_db("SELECT * FROM img WHERE id=?", (img,), one=True)
        if old_img:
            if old_img["slug"]:
                initials = "as" if "alex" in session.get("user") else "jb"
                user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], initials)
                old_img_path = os.path.join(user_upload_dir, old_img["slug"])
                if os.path.isfile(old_img_path):
                    os.remove(old_img_path)
            query_db('DELETE FROM img WHERE id=?', (img,), update=True)
            flash('so sad, you deleted a perfectly good image')
        return redirect(url_for("home"))
    if request.method == 'POST':
        file = request.files.get('file')
        id = int(request.form.get('id', 0))
        day = int(request.form.get('day'))
        month = int(request.form.get('month'))
        title = request.form.get('title')
        
        initials = "as" if "alex" in session.get("user") else "jb"
        user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], initials)
        
        if id:
            query_db("UPDATE img SET title=?, day=?, month=? WHERE id=?", (title, day, month, id), update=True)
            return jsonify(id=id, day=day, month=month, title=title)
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(user_upload_dir, filename))
            
            old_img = query_db("SELECT slug FROM img WHERE day=? and month=? and user=?", (day,month,session.get("user")), one=True)
            if old_img:
                if old_img["slug"]:
                    old_img_path = os.path.join(user_upload_dir, old_img["slug"])
                    if os.path.isfile(old_img_path):
                        os.remove(old_img_path)
                query_db("delete FROM img WHERE day=? and month=? and user=?", (day,month,session.get("user")), update=True)
        
            img_id = insert_db("img", fields=('day', 'month', 'user', 'title', 'slug'), args=(day, month, session.get("user"), title, filename))
            return jsonify(id=img_id, day=day, month=month, title=title)
    first_day, days_in_month = monthrange(2015, dt.now().month)
    days_in_month = range(1, days_in_month+1)
    today = dt.now().day
    this_month = dt.now().month
    if img:
        img = query_db("SELECT * FROM img WHERE id=?", (img,), one=True)
        first_day, days_in_month = monthrange(2015, img["month"])
        days_in_month = range(1, days_in_month+1)
    return render_template('upload.html', img=img, days_in_month=days_in_month, today=today, this_month=this_month)

'''

    Run the file!
    
'''
if __name__ == '__main__':
  app.run()