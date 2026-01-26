-- MySQL Initialization Script for DB-LLM Project

CREATE DATABASE IF NOT EXISTS demo;
USE demo;

-- 1. Classes
CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL
);

-- 2. Students
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(20),
    class_id INT,
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

-- 3. Student Attendance
CREATE TABLE IF NOT EXISTS student_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    date DATE,
    status ENUM('Present', 'Absent', 'Leave'),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- 4. Users (for teachers/staff)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100)
);

-- 5. Teachers
CREATE TABLE IF NOT EXISTS teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    subject VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    join_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 6. Teacher Attendance
CREATE TABLE IF NOT EXISTS teacher_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    date DATE,
    status ENUM('Present', 'Absent', 'Leave'),
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

-- 7. Leave Types
CREATE TABLE IF NOT EXISTS leave_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(50)
);

-- 8. Teacher Leaves
CREATE TABLE IF NOT EXISTS teacher_leaves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    leave_type_id INT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id)
);

-- 9. Teacher Leave Balance
CREATE TABLE IF NOT EXISTS teacher_leave_balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    leave_type_id INT,
    remaining_days INT,
    total_days INT,
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id)
);

-- Sample Data
INSERT INTO classes (class_name) VALUES ('Grade 10-A'), ('Grade 10-B'), ('Grade 11-A');

INSERT INTO students (name, roll_no, class_id) VALUES
('John Doe', '101', 1),
('Jane Smith', '102', 1),
('Alice Johnson', '201', 2),
('Bob Brown', '301', 3);

INSERT INTO student_attendance (student_id, date, status) VALUES
(1, CURDATE(), 'Present'),
(2, CURDATE(), 'Absent'),
(3, CURDATE(), 'Present'),
(4, CURDATE(), 'Leave');

INSERT INTO users (name, email) VALUES
('Mr. Anderson', 'anderson@school.com'),
('Ms. Davis', 'davis@school.com');

INSERT INTO teachers (user_id, subject, phone, address, join_date) VALUES
(1, 'Mathematics', '555-0101', '123 Math St', '2020-01-15'),
(2, 'Physics', '555-0102', '456 Physics Ave', '2021-08-20');

INSERT INTO teacher_attendance (teacher_id, date, status) VALUES
(1, CURDATE(), 'Present'),
(2, CURDATE(), 'Present');

INSERT INTO leave_types (type_name) VALUES ('Sick Leave'), ('Casual Leave'), ('Earned Leave');

INSERT INTO teacher_leaves (teacher_id, leave_type_id, start_date, end_date, status) VALUES
(1, 1, '2023-10-01', '2023-10-03', 'Approved');

INSERT INTO teacher_leave_balance (teacher_id, leave_type_id, remaining_days, total_days) VALUES
(1, 1, 10, 12),
(1, 2, 5, 5),
(2, 1, 8, 12);
