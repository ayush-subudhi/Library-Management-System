from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3, os, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "library.db")

app = Flask(__name__)
app.secret_key = "replace_this_with_a_random_secret"

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.executescript(open(os.path.join(BASE_DIR, "init_db.sql")).read())
    db.commit()

@app.route("/")
def home():
    db = get_db()
    q = request.args.get("q","")
    if q:
        cur = db.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?",
                         ('%'+q+'%','%'+q+'%','%'+q+'%'))
    else:
        cur = db.execute("SELECT * FROM books")
    books = cur.fetchall()
    return render_template("index.html", books=books, q=q)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # simple fixed admin credential for demo
        if username == "admin" and password == "admin123":
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/admin")
def admin_dashboard():
    db = get_db()
    books = db.execute("SELECT * FROM books").fetchall()
    transactions = db.execute("SELECT t.*, b.title FROM transactions t LEFT JOIN books b ON b.id=t.book_id ORDER BY t.issued_at DESC LIMIT 10").fetchall()
    return render_template("admin_dashboard.html", books=books, transactions=transactions)

@app.route("/books/add", methods=["GET","POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form.get("isbn","")
        qty = int(request.form.get("quantity",0))
        db = get_db()
        db.execute("INSERT INTO books(title,author,isbn,quantity) VALUES(?,?,?,?)",(title,author,isbn,qty))
        db.commit()
        flash("Book added","success")
        return redirect(url_for("admin_dashboard"))
    return render_template("add_book.html")

@app.route("/books/edit/<int:book_id>", methods=["GET","POST"])
def edit_book(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?",(book_id,)).fetchone()
    if not book:
        flash("Book not found","danger"); return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        db.execute("UPDATE books SET title=?,author=?,isbn=?,quantity=? WHERE id=?",
                   (request.form["title"], request.form["author"], request.form.get("isbn",""), int(request.form.get("quantity",0)), book_id))
        db.commit()
        flash("Book updated","success")
        return redirect(url_for("admin_dashboard"))
    return render_template("edit_book.html", book=book)

@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    db = get_db()
    db.execute("DELETE FROM books WHERE id=?",(book_id,))
    db.commit()
    flash("Book deleted","warning")
    return redirect(url_for("admin_dashboard"))

@app.route("/students")
def students():
    db = get_db()
    students = db.execute("SELECT * FROM students").fetchall()
    return render_template("students.html", students=students)

@app.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (student_id,))
    db.commit()
    flash("Student deleted successfully", "warning")
    return redirect(url_for("students"))


@app.route("/students/add", methods=["POST"])
def add_student():
    name = request.form["name"]
    roll = request.form.get("roll","")
    db = get_db()
    db.execute("INSERT INTO students(name,roll) VALUES(?,?)",(name,roll))
    db.commit()
    flash("Student added","success")
    return redirect(url_for("students"))

@app.route("/issue", methods=["GET","POST"])
def issue():
    db = get_db()
    if request.method == "POST":
        book_id = int(request.form["book_id"])
        student_id = int(request.form["student_id"])
        due_days = int(request.form.get("due_days",14))
        issued_at = datetime.datetime.now().isoformat()
        due_date = (datetime.datetime.now() + datetime.timedelta(days=due_days)).date().isoformat()
        # decrement quantity if available
        book = db.execute("SELECT quantity FROM books WHERE id=?",(book_id,)).fetchone()
        if not book or book["quantity"] <= 0:
            flash("Book not available", "danger")
            return redirect(url_for("issue"))
        db.execute("INSERT INTO transactions(book_id, student_id, issued_at, due_date, returned_at) VALUES(?,?,?,?,?)",
                   (book_id, student_id, issued_at, due_date, None))
        db.execute("UPDATE books SET quantity = quantity - 1 WHERE id=?",(book_id,))
        db.commit()
        flash("Book issued","success")
        return redirect(url_for("admin_dashboard"))
    books = db.execute("SELECT * FROM books WHERE quantity>0").fetchall()
    students = db.execute("SELECT * FROM students").fetchall()
    return render_template("issue.html", books=books, students=students)

@app.route("/return/<int:tx_id>", methods=["POST"])
def return_book(tx_id):
    db = get_db()
    tx = db.execute("SELECT * FROM transactions WHERE id=?",(tx_id,)).fetchone()
    if not tx:
        flash("Transaction not found","danger"); return redirect(url_for("admin_dashboard"))
    returned_at = datetime.datetime.now().isoformat()
    db.execute("UPDATE transactions SET returned_at=? WHERE id=?",(returned_at, tx_id))
    db.execute("UPDATE books SET quantity = quantity + 1 WHERE id=?",(tx["book_id"],))
    # simple fine calc: 10 currency units per day overdue
    due = datetime.datetime.fromisoformat(tx["due_date"]).date()
    now = datetime.date.today()
    fine = 0
    if now > due:
        days = (now - due).days
        fine = days * 10
    db.execute("UPDATE transactions SET fine=? WHERE id=?",(fine, tx_id))
    db.commit()
    flash(f"Book returned. Fine = {fine}", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/transactions")
def transactions():
    db = get_db()
    txs = db.execute("""SELECT t.*, b.title, s.name as student_name FROM transactions t
                        LEFT JOIN books b ON b.id=t.book_id
                        LEFT JOIN students s ON s.id=t.student_id
                        ORDER BY t.issued_at DESC""").fetchall()
    return render_template("transactions.html", txs=txs)

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        with app.app_context():
            init_db()
            print("Initialized DB at", DB_PATH)
    app.run(host="0.0.0.0", port=5000, debug=True)
