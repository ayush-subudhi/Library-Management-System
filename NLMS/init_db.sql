-- Books table
CREATE TABLE IF NOT EXISTS books(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    isbn TEXT,
    quantity INTEGER DEFAULT 0
);

-- Students
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll TEXT
);

-- Transactions (issue / return)
CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    student_id INTEGER,
    issued_at TEXT,
    due_date TEXT,
    returned_at TEXT,
    fine INTEGER DEFAULT 0,
    FOREIGN KEY(book_id) REFERENCES books(id),
    FOREIGN KEY(student_id) REFERENCES students(id)
);

INSERT OR IGNORE INTO books(id, title, author, isbn, quantity) VALUES
(1, 'Introduction to Algorithms', 'Cormen et al.', '9780262033848', 3),
(2, 'Clean Code', 'Robert C. Martin', '9780132350884', 2);

INSERT OR IGNORE INTO students(id, name, roll) VALUES
(1, 'Alice Student', 'S101'),
(2, 'Bob Student', 'S102');
