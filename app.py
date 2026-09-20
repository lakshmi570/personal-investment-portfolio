from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import init_db, get_db
import hashlib

app = Flask(__name__)
app.secret_key = 'investment_secret_2024'

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- AUTH ROUTES ----------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                       (username, email, hash_password(password)))
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Username or email already exists.', 'error')
        finally:
            db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db   = get_db()
        user = db.execute('SELECT * FROM users WHERE username=? AND password=?',
                          (username, hash_password(password))).fetchone()
        db.close()
        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- DASHBOARD ----------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db   = get_db()
    investments = db.execute('SELECT * FROM investments WHERE user_id=? ORDER BY buy_date DESC',
                             (session['user_id'],)).fetchall()
    db.close()

    total_invested = sum(i['buy_price'] * i['quantity'] for i in investments)
    total_current  = sum(i['current_price'] * i['quantity'] for i in investments)
    profit_loss    = total_current - total_invested
    pl_percent     = (profit_loss / total_invested * 100) if total_invested > 0 else 0

    return render_template('dashboard.html',
                           investments=investments,
                           total_invested=round(total_invested, 2),
                           total_current=round(total_current, 2),
                           profit_loss=round(profit_loss, 2),
                           pl_percent=round(pl_percent, 2))

# ---------- INVESTMENT CRUD ----------

@app.route('/add', methods=['GET', 'POST'])
def add_investment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name          = request.form['name'].strip()
        inv_type      = request.form['type']
        quantity      = float(request.form['quantity'])
        buy_price     = float(request.form['buy_price'])
        current_price = float(request.form['current_price'])
        buy_date      = request.form['buy_date']
        db = get_db()
        db.execute('INSERT INTO investments (user_id, name, type, quantity, buy_price, current_price, buy_date) VALUES (?,?,?,?,?,?,?)',
                   (session['user_id'], name, inv_type, quantity, buy_price, current_price, buy_date))
        db.commit()
        db.close()
        flash('Investment added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_investment.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_investment(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    inv = db.execute('SELECT * FROM investments WHERE id=? AND user_id=?',
                     (id, session['user_id'])).fetchone()
    if not inv:
        db.close()
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name          = request.form['name'].strip()
        inv_type      = request.form['type']
        quantity      = float(request.form['quantity'])
        buy_price     = float(request.form['buy_price'])
        current_price = float(request.form['current_price'])
        buy_date      = request.form['buy_date']
        db.execute('UPDATE investments SET name=?, type=?, quantity=?, buy_price=?, current_price=?, buy_date=? WHERE id=?',
                   (name, inv_type, quantity, buy_price, current_price, buy_date, id))
        db.commit()
        db.close()
        flash('Investment updated!', 'success')
        return redirect(url_for('dashboard'))
    db.close()
    return render_template('edit_investment.html', inv=inv)

@app.route('/delete/<int:id>')
def delete_investment(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM investments WHERE id=? AND user_id=?', (id, session['user_id']))
    db.commit()
    db.close()
    flash('Investment deleted.', 'success')
    return redirect(url_for('dashboard'))

# ---------- CHART DATA API ----------

@app.route('/api/chart-data')
def chart_data():
    if 'user_id' not in session:
        return jsonify({})
    db = get_db()
    rows = db.execute('SELECT type, SUM(current_price * quantity) as total FROM investments WHERE user_id=? GROUP BY type',
                      (session['user_id'],)).fetchall()
    db.close()
    return jsonify({'labels': [r['type'] for r in rows],
                    'values': [round(r['total'], 2) for r in rows]})

if __name__ == '__main__':
    app.run(debug=True)
