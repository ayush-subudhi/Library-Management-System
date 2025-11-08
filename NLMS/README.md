# Library Management System (Flask)

Simple Python + Flask Library Management System suitable for college project/demo.

Features included:
- Admin login (demo credentials: admin / admin123)
- Add / edit / delete books
- Add students
- Issue and return books (with simple fine calculation)
- Search on homepage (by title, author, or ISBN)
- SQLite database (file: library.db)

How to run:
1. Create a virtualenv (recommended) and activate it.
2. Install requirements: `pip install -r requirements.txt`
3. Start app: `python app.py`
4. Visit http://127.0.0.1:5000 in your browser.

Notes:
- This is intentionally minimal and focused on the essential features requested.
- For production, change the secret key and secure the admin login and forms.
