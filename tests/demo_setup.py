import sqlite3

def setup_demo_db(db_path="demo.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT,
        salary INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        employee_id INTEGER,
        amount INTEGER,
        sale_date DATE,
        FOREIGN KEY (employee_id) REFERENCES employees(id)
    )
    ''')
    
    # Insert data
    employees = [
        (1, 'Alice', 'Sales', 50000),
        (2, 'Bob', 'Engineering', 70000),
        (3, 'Charlie', 'Sales', 55000),
        (4, 'David', 'Marketing', 60000)
    ]
    cursor.executemany('INSERT OR REPLACE INTO employees VALUES (?,?,?,?)', employees)
    
    sales = [
        (1, 1, 1000, '2023-01-01'),
        (2, 1, 1500, '2023-01-15'),
        (3, 3, 2000, '2023-01-20'),
        (4, 2, 500, '2023-02-01')
    ]
    cursor.executemany('INSERT OR REPLACE INTO sales VALUES (?,?,?,?)', sales)
    
    conn.commit()
    conn.close()
    print(f"Demo database created at {db_path}")

if __name__ == "__main__":
    setup_demo_db()
