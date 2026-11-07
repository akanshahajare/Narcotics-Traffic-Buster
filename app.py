import os, sqlite3, hashlib, uuid, json
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from flask import Flask, request, jsonify, session, send_from_directory, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / '.env')
DATA = BASE / 'instance'; UPLOADS = DATA / 'evidence'
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True)
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'dev-only-change-this-secret-before-deployment')
app.config.update(MAX_CONTENT_LENGTH=12*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
DB = DATA / 'monitoring.db'
ALLOWED = {'jpg','jpeg','png','webp'}

def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c

def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY, reference TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, latitude REAL, longitude REAL, accuracy REAL, address TEXT, image_name TEXT, image_hash TEXT, captured_at TEXT, status TEXT NOT NULL DEFAULT 'Submitted', admin_note TEXT DEFAULT '', created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at DESC);
        ''')
        email=(os.getenv('ADMIN_EMAIL') or '').strip().lower(); pw=os.getenv('ADMIN_PASSWORD') or ''
        if not email or len(pw) < 12:
            raise RuntimeError('Set ADMIN_EMAIL and ADMIN_PASSWORD (at least 12 characters) in .env before starting the application.')
        if not c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
            c.execute('INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)',('System Administrator',email,generate_password_hash(pw),'admin',now()))

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def current_user():
    if not session.get('uid'): return None
    with connect() as c: r=c.execute('SELECT id,name,email,role FROM users WHERE id=?',(session['uid'],)).fetchone()
    return dict(r) if r else None
def auth(required=True, admin=False):
    def deco(fn):
        @wraps(fn)
        def wrapped(*a,**kw):
            u=current_user()
            if not u: return jsonify(error='Authentication required'),401
            if admin and u['role']!='admin': return jsonify(error='Administrator access required'),403
            return fn(*a,**kw)
        return wrapped
    return deco

def report_dict(r):
    d=dict(r); d['evidence_url']=('/api/evidence/'+d['id']) if d.get('image_name') else None
    return d

@app.get('/')
def index(): return render_template('index.html')
@app.get('/manifest.json')
def manifest(): return send_from_directory(BASE,'manifest.json')
@app.get('/sw.js')
def sw(): return send_from_directory(BASE,'sw.js',mimetype='application/javascript')
@app.get('/health')
def health(): return jsonify(status='ok',service='Narcotics Traffic Buster',database='sqlite')

@app.post('/api/register')
def register():
    x=request.get_json(silent=True) or {}; name=(x.get('name') or '').strip(); email=(x.get('email') or '').strip().lower(); pw=x.get('password') or ''
    if not name or '@' not in email or len(pw)<8: return jsonify(error='Enter a name, valid email and password of at least 8 characters.'),400
    try:
        with connect() as c: c.execute('INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)',(name,email,generate_password_hash(pw),'customer',now()))
    except sqlite3.IntegrityError: return jsonify(error='An account with this email already exists.'),409
    return jsonify(message='Account created. Please sign in.'),201

@app.post('/api/login')
def login():
    x=request.get_json(silent=True) or {}; email=(x.get('email') or '').strip().lower(); pw=x.get('password') or ''
    with connect() as c: u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    if not u or not check_password_hash(u['password'],pw): return jsonify(error='Incorrect email or password.'),401
    session.clear(); session['uid']=u['id']
    return jsonify(user={'id':u['id'],'name':u['name'],'email':u['email'],'role':u['role']})

@app.post('/api/logout')
def logout(): session.clear(); return jsonify(message='Signed out')
@app.get('/api/me')
def me():
    u=current_user(); return jsonify(user=u) if u else (jsonify(user=None),200)

@app.post('/api/reports')
@auth()
def create_report():
    u=current_user(); category=(request.form.get('category') or 'Suspicious activity').strip(); desc=(request.form.get('description') or '').strip()
    if len(desc)<10: return jsonify(error='Please provide at least 10 characters of detail.'),400
    def num(k):
        try: return float(request.form[k]) if request.form.get(k) else None
        except ValueError: return None
    lat,lon=num('latitude'),num('longitude')
    if (lat is None) != (lon is None) or (lat is not None and not(-90<=lat<=90 and -180<=lon<=180)): return jsonify(error='Invalid GPS coordinates.'),400
    file=request.files.get('photo'); stored=None; digest=None; captured=None
    if file and file.filename:
        ext=secure_filename(file.filename).rsplit('.',1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED: return jsonify(error='Photo must be JPG, PNG or WEBP.'),400
        raw=file.read()
        if len(raw)>10*1024*1024: return jsonify(error='Photo must be 10 MB or smaller.'),400
        digest=hashlib.sha256(raw).hexdigest(); stored=f'{uuid.uuid4().hex}.{ext}'; (UPLOADS/stored).write_bytes(raw)
        captured=request.form.get('captured_at') or now()
    rid=uuid.uuid4().hex; ref='NTB-'+datetime.now().strftime('%y%m%d')+'-'+uuid.uuid4().hex[:6].upper(); created=now()
    with connect() as c:
        c.execute('INSERT INTO reports(id,reference,user_id,category,description,latitude,longitude,accuracy,address,image_name,image_hash,captured_at,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(rid,ref,u['id'],category,desc,lat,lon,num('accuracy'),(request.form.get('address') or '')[:250],stored,digest,captured,created))
    return jsonify(message='Report submitted',reference=ref,id=rid),201

@app.get('/api/reports')
@auth()
def list_reports():
    u=current_user()
    with connect() as c:
        if u['role']=='admin': rows=c.execute('SELECT r.*,u.name AS reporter,u.email AS reporter_email FROM reports r JOIN users u ON u.id=r.user_id ORDER BY r.created_at DESC').fetchall()
        else: rows=c.execute('SELECT r.*,u.name AS reporter FROM reports r JOIN users u ON u.id=r.user_id WHERE r.user_id=? ORDER BY r.created_at DESC',(u['id'],)).fetchall()
    return jsonify(reports=[report_dict(r) for r in rows])

@app.patch('/api/reports/<rid>')
@auth(admin=True)
def update_report(rid):
    x=request.get_json(silent=True) or {}; status=x.get('status'); note=(x.get('admin_note') or '')[:1000]
    if status not in {'Submitted','Under review','Verified','Closed','Rejected'}: return jsonify(error='Invalid status.'),400
    with connect() as c:
        cur=c.execute('UPDATE reports SET status=?,admin_note=? WHERE id=?',(status,note,rid))
        if not cur.rowcount: return jsonify(error='Report not found.'),404
    return jsonify(message='Report updated')

@app.get('/api/evidence/<rid>')
@auth()
def evidence(rid):
    u=current_user()
    with connect() as c: r=c.execute('SELECT user_id,image_name FROM reports WHERE id=?',(rid,)).fetchone()
    if not r or not r['image_name']: return jsonify(error='Evidence not found.'),404
    if u['role']!='admin' and r['user_id']!=u['id']: return jsonify(error='Forbidden'),403
    return send_from_directory(UPLOADS,r['image_name'],as_attachment=False)

@app.get('/api/stats')
@auth(admin=True)
def stats():
    with connect() as c:
        total=c.execute('SELECT COUNT(*) n FROM reports').fetchone()['n']; pending=c.execute("SELECT COUNT(*) n FROM reports WHERE status IN ('Submitted','Under review')").fetchone()['n']; verified=c.execute("SELECT COUNT(*) n FROM reports WHERE status='Verified'").fetchone()['n']; users=c.execute("SELECT COUNT(*) n FROM users WHERE role='customer'").fetchone()['n']
    return jsonify(total=total,pending=pending,verified=verified,customers=users)

@app.errorhandler(413)
def too_large(e): return jsonify(error='Upload is too large. Maximum request size is 12 MB.'),413

init_db()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=os.getenv('FLASK_DEBUG')=='1')
