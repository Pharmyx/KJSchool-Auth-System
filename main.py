import customtkinter as ctk
import sqlite3
from datetime import datetime, date
import hashlib
import re
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Tuple
import json
import os

logging.basicConfig(
    filename='school_auth.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SchoolAuthSystem:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title("King James School Authentication System")
        self.root.geometry("800x900")
        self.root.resizable(False, False)
        self.colors = {
            "primary": "#2B2D42",
            "secondary": "#468189",
            "border": "#D9D9D9",
            "background": "#1C2526",
            "text": "#E6E8E6",
            "success": "#679436",
            "error": "#A63C3C"
        }
        self.fonts = {
            "title": ctk.CTkFont(family="Roboto", size=28, weight="bold"),
            "subtitle": ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            "regular": ctk.CTkFont(family="Roboto", size=16),
            "small": ctk.CTkFont(family="Roboto", size=14),
            "copyright": ctk.CTkFont(family="Roboto", size=12)
        }
        self.db_file = 'school_attendance.db'
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.valid_classes = [
            "7A", "7B", "7C", "8A", "8B", "8C",
            "9A", "9B", "9C", "10A", "10B", "10C",
            "11A", "11B", "11C", "12A", "12B", "13A"
        ]
        self.setup_database()
        self.setup_gui()
        self.load_config()

    def setup_database(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL CHECK(age >= 11 AND age <= 18),
                    class_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    login_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (student_id)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS teachers (
                    teacher_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            self.conn.commit()
            logging.info("Database tables initialized successfully")
        except sqlite3.Error as e:
            logging.error(f"Database setup failed: {str(e)}")
            messagebox.showerror("Error", "Failed to initialize database")
            self.root.quit()

    def load_config(self):
        config_file = 'config.json'
        default_config = {
            "school_name": "King James School, Knaresborough",
            "min_age": 11,
            "max_age": 18,
            "admin_password": self.hash_password("admin123"),
            "teacher_password": self.hash_password("teacher123")
        }
        if not os.path.exists(config_file):
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except json.JSONDecodeError:
            self.config = default_config
            logging.warning("Invalid config file, using default configuration")

    def hash_password(self, password: str):
        return hashlib.sha256(password.encode()).hexdigest()

    def validate_student_id(self, student_id: str):
        pattern = r'^KJ\d{4}\d{4}$'
        return bool(re.match(pattern, student_id))

    def validate_teacher_id(self, teacher_id: str):
        pattern = r'^TJ\d{4}\d{4}$'
        return bool(re.match(pattern, teacher_id))

    def validate_name(self, name: str):
        pattern = r'^[A-Za-z\s]+$'
        return bool(re.match(pattern, name.strip()))

    def add_footer(self, window: ctk.CTkBaseClass):
        footer_frame = ctk.CTkFrame(
            window,
            fg_color=self.colors["primary"],
            corner_radius=10,
            height=50
        )
        footer_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        footer_frame.pack_propagate(False)
        ctk.CTkLabel(
            footer_frame,
            text="© 2025 King James School, Knaresborough",
            font=self.fonts["copyright"],
            text_color=self.colors["text"]
        ).pack(expand=True)

    def setup_gui(self):
        main_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.colors["background"],
            corner_radius=20
        )
        main_frame.pack(pady=30, padx=30, fill="both", expand=True)
        header_frame = ctk.CTkFrame(
            main_frame,
            fg_color=self.colors["primary"],
            corner_radius=15
        )
        header_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(
            header_frame,
            text="King James School",
            font=self.fonts["title"],
            text_color=self.colors["text"]
        ).pack(pady=10)
        ctk.CTkLabel(
            header_frame,
            text="Authentication System",
            font=self.fonts["subtitle"],
            text_color=self.colors["text"]
        ).pack(pady=5)
        login_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        login_frame.pack(pady=20)
        ctk.CTkLabel(
            login_frame,
            text="Select Login Type:",
            font=self.fonts["regular"],
            text_color=self.colors["text"]
        ).pack(pady=10)
        login_type = ctk.CTkSegmentedButton(
            login_frame,
            values=["Student", "Teacher", "Admin"],
            command=self.switch_login_type,
            font=self.fonts["regular"],
            fg_color=self.colors["secondary"],
            selected_color=self.colors["success"],
            selected_hover_color=self.colors["success"],
            unselected_color=self.colors["primary"],
            text_color=self.colors["text"],
            width=300
        )
        login_type.set("Student")
        login_type.pack(pady=10)
        self.form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.form_frame.pack(pady=20, padx=20, fill="both")
        self.current_login_type = "Student"
        self.setup_student_form()
        self.add_footer(self.root)

    def switch_login_type(self, login_type: str):
        self.current_login_type = login_type
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        if login_type == "Student":
            self.setup_student_form()
        elif login_type == "Teacher":
            self.setup_teacher_form()
        else:
            self.setup_admin_form()

    def setup_student_form(self):
        self.entries = {}
        fields = [
            ("Student ID", "Enter KJYYYYXXXX format"),
            ("Name", "Enter full name"),
            ("Age", "11-18"),
            ("Class", "Select class"),
            ("Password", "Enter password")
        ]
        input_container = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        input_container.pack(expand=True)
        for field, placeholder in fields:
            frame = ctk.CTkFrame(input_container, fg_color="transparent")
            frame.pack(pady=15, fill="x", padx=50)
            ctk.CTkLabel(
                frame,
                text=f"{field}:",
                width=120,
                font=self.fonts["regular"],
                text_color=self.colors["text"],
                anchor="e"
            ).pack(side="left")
            if field == "Class":
                entry = ctk.CTkComboBox(
                    frame,
                    values=self.valid_classes,
                    width=300,
                    font=self.fonts["regular"],
                    dropdown_font=self.fonts["small"],
                    fg_color=self.colors["secondary"],
                    button_color=self.colors["border"],
                    button_hover_color=self.colors["success"],
                    text_color=self.colors["text"],
                    border_color=self.colors["border"],
                    border_width=2
                )
            else:
                entry = ctk.CTkEntry(
                    frame,
                    placeholder_text=placeholder,
                    width=300,
                    font=self.fonts["regular"],
                    fg_color=self.colors["secondary"],
                    text_color=self.colors["text"],
                    border_color=self.colors["border"],
                    border_width=2
                )
                if field == "Password":
                    entry.configure(show="*")
            entry.pack(side="left", padx=10)
            self.entries[field] = entry
        button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        button_frame.pack(pady=30, expand=True)
        ctk.CTkButton(
            button_frame,
            text="Login",
            command=self.verify_login,
            width=200,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)
        ctk.CTkButton(
            button_frame,
            text="View Today's Attendance",
            command=self.view_attendance,
            width=200,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)

    def setup_teacher_form(self):
        self.entries = {}
        fields = [
            ("Teacher ID", "Enter TJYYYYXXXX format"),
            ("Name", "Enter full name"),
            ("Password", "Enter password")
        ]
        input_container = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        input_container.pack(expand=True)
        for field, placeholder in fields:
            frame = ctk.CTkFrame(input_container, fg_color="transparent")
            frame.pack(pady=15, fill="x", padx=50)
            ctk.CTkLabel(
                frame,
                text=f"{field}:",
                width=120,
                font=self.fonts["regular"],
                text_color=self.colors["text"],
                anchor="e"
            ).pack(side="left")
            entry = ctk.CTkEntry(
                frame,
                placeholder_text=placeholder,
                width=300,
                font=self.fonts["regular"],
                fg_color=self.colors["secondary"],
                text_color=self.colors["text"],
                border_color=self.colors["border"],
                border_width=2
            )
            if field == "Password":
                entry.configure(show="*")
            entry.pack(side="left", padx=10)
            self.entries[field] = entry
        button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        button_frame.pack(pady=30, expand=True)
        ctk.CTkButton(
            button_frame,
            text="Login",
            command=self.verify_login,
            width=200,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)

    def setup_admin_form(self):
        self.entries = {}
        input_container = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        input_container.pack(expand=True)
        ctk.CTkLabel(
            input_container,
            text="Admin Login",
            font=self.fonts["subtitle"],
            text_color=self.colors["text"]
        ).pack(pady=20)
        frame = ctk.CTkFrame(input_container, fg_color="transparent")
        frame.pack(pady=15, fill="x", padx=50)
        ctk.CTkLabel(
            frame,
            text="Password:",
            width=120,
            font=self.fonts["regular"],
            text_color=self.colors["text"],
            anchor="e"
        ).pack(side="left")
        entry = ctk.CTkEntry(
            frame,
            placeholder_text="Enter admin password",
            width=300,
            font=self.fonts["regular"],
            fg_color=self.colors["secondary"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            show="*"
        )
        entry.pack(side="left", padx=10)
        self.entries["Password"] = entry
        button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        button_frame.pack(pady=30, expand=True)
        ctk.CTkButton(
            button_frame,
            text="Verify",
            command=self.verify_login,
            width=200,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)

    def verify_login(self):
        if self.current_login_type == "Student":
            self.verify_student_login()
        elif self.current_login_type == "Teacher":
            self.verify_teacher_login()
        else:
            self.verify_admin_login()

    def verify_student_login(self):
        student_id = self.entries["Student ID"].get().strip()
        name = self.entries["Name"].get().strip()
        age = self.entries["Age"].get().strip()
        class_name = self.entries["Class"].get().strip()
        password = self.entries["Password"].get().strip()
        if not all([student_id, name, age, class_name, password]):
            messagebox.showerror("Error", "All fields are required", icon="error")
            logging.warning("Student login attempt with missing fields")
            return
        if not self.validate_student_id(student_id):
            messagebox.showerror("Error", "Invalid Student ID (KJYYYYXXXX)", icon="error")
            logging.warning(f"Invalid student ID: {student_id}")
            return
        if not self.validate_name(name):
            messagebox.showerror("Error", "Name must contain only letters and spaces", icon="error")
            logging.warning(f"Invalid name: {name}")
            return
        if class_name not in self.valid_classes:
            messagebox.showerror("Error", "Invalid class selection", icon="error")
            logging.warning(f"Invalid class: {class_name}")
            return
        try:
            age = int(age)
            if not (11 <= age <= 18):
                raise ValueError("Age out of range")
        except ValueError:
            messagebox.showerror("Error", "Age must be 11-18", icon="error")
            logging.warning(f"Invalid age: {age}")
            return
        try:
            self.cursor.execute('''
                SELECT * FROM students 
                WHERE student_id = ? AND name = ? AND age = ? 
                AND class_name = ? AND password_hash = ?
            ''', (student_id, name, age, class_name, self.hash_password(password)))
            if self.cursor.fetchone():
                self.cursor.execute('''
                    UPDATE students 
                    SET last_login = ? 
                    WHERE student_id = ?
                ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), student_id))
                self.cursor.execute('''
                    INSERT INTO attendance (student_id, name, class_name, login_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, name, class_name, 
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Present"))
                self.conn.commit()
                messagebox.showinfo("Success", "Login successful! Attendance recorded.", icon="info")
                logging.info(f"Successful student login: {student_id} ({name})")
                self.clear_entries()
            else:
                messagebox.showerror("Error", "Invalid credentials", icon="error")
                logging.warning(f"Failed student login attempt: {student_id}")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {str(e)}", icon="error")
            logging.error(f"Database error during student login: {str(e)}")

    def verify_teacher_login(self):
        teacher_id = self.entries["Teacher ID"].get().strip()
        name = self.entries["Name"].get().strip()
        password = self.entries["Password"].get().strip()
        if not all([teacher_id, name, password]):
            messagebox.showerror("Error", "All fields are required", icon="error")
            logging.warning("Teacher login attempt with missing fields")
            return
        if not self.validate_teacher_id(teacher_id):
            messagebox.showerror("Error", "Invalid Teacher ID (TJYYYYXXXX)", icon="error")
            logging.warning(f"Invalid teacher ID: {teacher_id}")
            return
        if not self.validate_name(name):
            messagebox.showerror("Error", "Name must contain only letters and spaces", icon="error")
            logging.warning(f"Invalid name: {name}")
            return
        try:
            self.cursor.execute('''
                SELECT * FROM teachers 
                WHERE teacher_id = ? AND name = ? AND password_hash = ?
            ''', (teacher_id, name, self.hash_password(password)))
            if self.cursor.fetchone():
                messagebox.showinfo("Success", "Teacher login successful!", icon="info")
                logging.info(f"Successful teacher login: {teacher_id} ({name})")
                self.clear_entries()
                self.show_teacher_management(teacher_id, name)
            else:
                messagebox.showerror("Error", "Invalid credentials", icon="error")
                logging.warning(f"Failed teacher login attempt: {teacher_id}")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {str(e)}", icon="error")
            logging.error(f"Database error during teacher login: {str(e)}")

    def verify_admin_login(self):
        password = self.entries["Password"].get().strip()
        if not password:
            messagebox.showerror("Error", "Password is required", icon="error")
            logging.warning("Admin login attempt with missing password")
            return
        if self.hash_password(password) == self.config["admin_password"]:
            messagebox.showinfo("Success", "Admin login successful!", icon="info")
            logging.info("Successful admin login")
            self.clear_entries()
            self.show_admin_functions()
        else:
            messagebox.showerror("Error", "Invalid admin password", icon="error")
            logging.warning("Failed admin login attempt")

    def clear_entries(self):
        for entry in self.entries.values():
            if isinstance(entry, ctk.CTkEntry):
                entry.delete(0, tk.END)
            elif isinstance(entry, ctk.CTkComboBox):
                entry.set(self.valid_classes[0])

    def show_teacher_management(self, teacher_id: str, teacher_name: str):
        teacher_window = ctk.CTkToplevel(self.root)
        teacher_window.title("Teacher Management Panel")
        teacher_window.geometry("1000x800")
        teacher_window.transient(self.root)
        teacher_window.configure(fg_color=self.colors["background"])
        ctk.CTkLabel(
            teacher_window,
            text=f"Welcome, {teacher_name}",
            font=self.fonts["subtitle"],
            text_color=self.colors["text"]
        ).pack(pady=20)
        options_frame = ctk.CTkFrame(teacher_window, fg_color="transparent")
        options_frame.pack(pady=20, expand=True)
        ctk.CTkButton(
            options_frame,
            text="View Today's Attendance",
            command=lambda: self.view_attendance(teacher_window),
            width=250,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)
        ctk.CTkButton(
            options_frame,
            text="View Attendance History",
            command=self.view_attendance_history,
            width=250,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)
        ctk.CTkButton(
            options_frame,
            text="Manage Students",
            command=self.manage_students,
            width=250,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)
        self.add_footer(teacher_window)

    def view_attendance(self, parent_window: Optional[ctk.CTkToplevel] = None):
        view_window = ctk.CTkToplevel(self.root if parent_window is None else parent_window)
        view_window.title("Today's Attendance")
        view_window.geometry("1000x700")
        view_window.transient(self.root)
        view_window.configure(fg_color=self.colors["background"])
        ctk.CTkLabel(
            view_window,
            text="Today's Attendance",
            font=self.fonts["subtitle"],
            text_color=self.colors["text"]
        ).pack(pady=20)
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=self.colors["background"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["background"],
            font=("Roboto", 12)
        )
        style.configure(
            "Treeview.Heading",
            background=self.colors["primary"],
            foreground=self.colors["text"],
            font=("Roboto", 14, "bold")
        )
        columns = ("ID", "Name", "Class", "Time", "Status")
        tree = ttk.Treeview(view_window, columns=columns, show="headings", style="Treeview")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180)
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        try:
            today = date.today().strftime("%Y-%m-%d")
            self.cursor.execute('''
                SELECT student_id, name, class_name, login_time, status
                FROM attendance
                WHERE login_time LIKE ?
                ORDER BY login_time DESC
            ''', (f"{today}%",))
            for row in self.cursor.fetchall():
                tree.insert("", "end", values=row)
            logging.info("Today's attendance viewed")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {str(e)}", icon="error")
            logging.error(f"Database error in view_attendance: {str(e)}")
        self.add_footer(view_window)

    def view_attendance_history(self):
        history_window = ctk.CTkToplevel(self.root)
        history_window.title("Attendance History")
        history_window.geometry("1000x800")
        history_window.transient(self.root)
        history_window.configure(fg_color=self.colors["background"])
        ctk.CTkLabel(
            history_window,
            text="Attendance History",
            font=self.fonts["subtitle"],
            text_color=self.colors["text"]
        ).pack(pady=20)
        filter_frame = ctk.CTkFrame(history_window, fg_color="transparent")
        filter_frame.pack(pady=20, expand=True)
        ctk.CTkLabel(
            filter_frame,
            text="Select Date:",
            font=self.fonts["regular"],
            text_color=self.colors["text"]
        ).pack(side="left", padx=10)
        date_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="YYYY-MM-DD",
            width=200,
            font=self.fonts["regular"],
            fg_color=self.colors["secondary"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2
        )
        date_entry.pack(side="left", padx=10)
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=self.colors["background"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["background"],
            font=("Roboto", 12)
        )
        style.configure(
            "Treeview.Heading",
            background=self.colors["primary"],
            foreground=self.colors["text"],
            font=("Roboto", 14, "bold")
        )
        columns = ("ID", "Name", "Class", "Time", "Status")
        tree = ttk.Treeview(history_window, columns=columns, show="headings", style="Treeview")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180)
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        def load_history():
            for item in tree.get_children():
                tree.delete(item)
            selected_date = date_entry.get().strip() or date.today().strftime("%Y-%m-%d")
            try:
                self.cursor.execute('''
                    SELECT student_id, name, class_name, login_time, status
                    FROM attendance
                    WHERE login_time LIKE ?
                    ORDER BY login_time DESC
                ''', (f"{selected_date}%",))
                for row in self.cursor.fetchall():
                    tree.insert("", "end", values=row)
                logging.info(f"Attendance history viewed for {selected_date}")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {str(e)}", icon="error")
                logging.error(f"Database error in view_attendance_history: {str(e)}")
        ctk.CTkButton(
            filter_frame,
            text="Load History",
            command=load_history,
            width=150,
            height=40,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(side="left", padx=10)
        load_history()
        self.add_footer(history_window)

    def manage_students(self):
        manage_window = ctk.CTkToplevel(self.root)
        manage_window.title("Manage Students")
        manage_window.geometry("1000x800")
        manage_window.transient(self.root)
        manage_window.configure(fg_color=self.colors["background"])
        ctk.CTkLabel(
            manage_window,
            text="Student Management",
            font=self.fonts["subtitle"],
            text_color=self.colors["text"]
        ).pack(pady=20)
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=self.colors["background"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["background"],
            font=("Roboto", 12)
        )
        style.configure(
            "Treeview.Heading",
            background=self.colors["primary"],
            foreground=self.colors["text"],
            font=("Roboto", 14, "bold")
        )
        columns = ("ID", "Name", "Age", "Class", "Last Login")
        tree = ttk.Treeview(manage_window, columns=columns, show="headings", style="Treeview")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180)
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        try:
            self.cursor.execute('''
                SELECT student_id, name, age, class_name, last_login
                FROM students
                ORDER BY name
            ''')
            for row in self.cursor.fetchall():
                tree.insert("", "end", values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {str(e)}", icon="error")
            logging.error(f"Database error in manage_students: {str(e)}")
        def delete_student():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Select a student to delete", icon="error")
                return
            student_id = tree.item(selected)["values"][0]
            if messagebox.askyesno("Confirm", f"Delete student {student_id}?"):
                try:
                    self.cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
                    self.cursor.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
                    self.cursor.execute('''
                        INSERT INTO admin_logs (action, details, timestamp)
                        VALUES (?, ?, ?)
                    ''', ("Delete Student", f"Deleted student {student_id}", 
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    self.conn.commit()
                    tree.delete(selected)
                    messagebox.showinfo("Success", "Student deleted", icon="info")
                    logging.info(f"Student deleted: {student_id}")
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Database error: {str(e)}", icon="error")
                    logging.error(f"Database error in delete_student: {str(e)}")
        button_frame = ctk.CTkFrame(manage_window, fg_color="transparent")
        button_frame.pack(pady=20, expand=True)
        ctk.CTkButton(
            button_frame,
            text="Delete Selected Student",
            command=delete_student,
            width=200,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["error"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=10)
        self.add_footer(manage_window)

    def show_admin_functions(self):
        admin_window = ctk.CTkToplevel(self.root)
        admin_window.title("Admin Functions")
        admin_window.geometry("600x800")
        admin_window.transient(self.root)
        admin_window.configure(fg_color=self.colors["background"])
        ctk.CTkLabel(
            admin_window,
            text="Admin: User Registration",
            font=self.fonts["subtitle"],
            text_color=self.colors["text"]
        ).pack(pady=20)
        student_frame = ctk.CTkFrame(admin_window, fg_color="transparent")
        student_frame.pack(pady=20, padx=20, fill="both")
        ctk.CTkLabel(
            student_frame,
            text="Register Student",
            font=self.fonts["regular"],
            text_color=self.colors["text"]
        ).pack(pady=10)
        student_entries = {}
        fields = [
            ("Student ID", "KJYYYYXXXX"),
            ("Name", "Full name"),
            ("Age", "11-18"),
            ("Class", "e.g., 7A"),
            ("Password", "Password")
        ]
        for field, placeholder in fields:
            frame = ctk.CTkFrame(student_frame, fg_color="transparent")
            frame.pack(pady=10, fill="x", padx=50)
            ctk.CTkLabel(
                frame,
                text=f"{field}:",
                width=120,
                font=self.fonts["regular"],
                text_color=self.colors["text"],
                anchor="e"
            ).pack(side="left")
            if field == "Class":
                entry = ctk.CTkComboBox(
                    frame,
                    values=self.valid_classes,
                    width=300,
                    font=self.fonts["regular"],
                    fg_color=self.colors["secondary"],
                    button_color=self.colors["border"],
                    button_hover_color=self.colors["success"],
                    text_color=self.colors["text"],
                    border_color=self.colors["border"],
                    border_width=2
                )
            else:
                entry = ctk.CTkEntry(
                    frame,
                    placeholder_text=placeholder,
                    width=300,
                    font=self.fonts["regular"],
                    fg_color=self.colors["secondary"],
                    text_color=self.colors["text"],
                    border_color=self.colors["border"],
                    border_width=2
                )
                if field == "Password":
                    entry.configure(show="*")
            entry.pack(side="left", padx=10)
            student_entries[field] = entry
        def register_student():
            student_id = student_entries["Student ID"].get().strip()
            name = student_entries["Name"].get().strip()
            age = student_entries["Age"].get().strip()
            class_name = student_entries["Class"].get().strip()
            password = student_entries["Password"].get().strip()
            if not all([student_id, name, age, class_name, password]):
                messagebox.showerror("Error", "All fields are required", icon="error")
                return
            if not self.validate_student_id(student_id):
                messagebox.showerror("Error", "Invalid Student ID format", icon="error")
                return
            if not self.validate_name(name):
                messagebox.showerror("Error", "Invalid name format", icon="error")
                return
            try:
                age = int(age)
                if not (11 <= age <= 18):
                    raise ValueError("Age out of range")
            except ValueError:
                messagebox.showerror("Error", "Age must be 11-18", icon="error")
                return
            try:
                self.cursor.execute('''
                    INSERT INTO students (student_id, name, age, class_name, password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (student_id, name, age, class_name, 
                      self.hash_password(password), 
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                self.cursor.execute('''
                    INSERT INTO admin_logs (action, details, timestamp)
                    VALUES (?, ?, ?)
                ''', ("Register Student", f"Registered student {student_id}", 
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                self.conn.commit()
                messagebox.showinfo("Success", "Student registered successfully", icon="info")
                logging.info(f"Student registered: {student_id}")
                for entry in student_entries.values():
                    if isinstance(entry, ctk.CTkEntry):
                        entry.delete(0, tk.END)
                    elif isinstance(entry, ctk.CTkComboBox):
                        entry.set(self.valid_classes[0])
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Student ID already exists", icon="error")
                logging.warning(f"Failed registration: ID {student_id} exists")
        ctk.CTkButton(
            student_frame,
            text="Register Student",
            command=register_student,
            width=200,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=20)
        teacher_frame = ctk.CTkFrame(admin_window, fg_color="transparent")
        teacher_frame.pack(pady=20, padx=20, fill="both")
        ctk.CTkLabel(
            teacher_frame,
            text="Register Teacher",
            font=self.fonts["regular"],
            text_color=self.colors["text"]
        ).pack(pady=10)
        teacher_entries = {}
        teacher_fields = [
            ("Teacher ID", "TJYYYYXXXX"),
            ("Name", "Full name"),
            ("Password", "Password")
        ]
        for field, placeholder in teacher_fields:
            frame = ctk.CTkFrame(teacher_frame, fg_color="transparent")
            frame.pack(pady=10, fill="x", padx=50)
            ctk.CTkLabel(
                frame,
                text=f"{field}:",
                width=120,
                font=self.fonts["regular"],
                text_color=self.colors["text"],
                anchor="e"
            ).pack(side="left")
            entry = ctk.CTkEntry(
                frame,
                placeholder_text=placeholder,
                width=300,
                font=self.fonts["regular"],
                fg_color=self.colors["secondary"],
                text_color=self.colors["text"],
                border_color=self.colors["border"],
                border_width=2
            )
            if field == "Password":
                entry.configure(show="*")
            entry.pack(side="left", padx=10)
            teacher_entries[field] = entry
        def register_teacher():
            teacher_id = teacher_entries["Teacher ID"].get().strip()
            name = teacher_entries["Name"].get().strip()
            password = teacher_entries["Password"].get().strip()
            if not all([teacher_id, name, password]):
                messagebox.showerror("Error", "All fields are required", icon="error")
                return
            if not self.validate_teacher_id(teacher_id):
                messagebox.showerror("Error", "Invalid Teacher ID format", icon="error")
                return
            if not self.validate_name(name):
                messagebox.showerror("Error", "Invalid name format", icon="error")
                return
            try:
                self.cursor.execute('''
                    INSERT INTO teachers (teacher_id, name, password_hash, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (teacher_id, name, self.hash_password(password), 
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                self.cursor.execute('''
                    INSERT INTO admin_logs (action, details, timestamp)
                    VALUES (?, ?, ?)
                ''', ("Register Teacher", f"Registered teacher {teacher_id}", 
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                self.conn.commit()
                messagebox.showinfo("Success", "Teacher registered successfully", icon="info")
                logging.info(f"Teacher registered: {teacher_id}")
                for entry in teacher_entries.values():
                    entry.delete(0, tk.END)
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Teacher ID already exists", icon="error")
                logging.warning(f"Failed registration: ID {teacher_id} exists")
        ctk.CTkButton(
            teacher_frame,
            text="Register Teacher",
            command=register_teacher,
            width=200,
            height=50,
            font=self.fonts["regular"],
            fg_color=self.colors["primary"],
            hover_color=self.colors["success"],
            text_color=self.colors["text"],
            border_color=self.colors["border"],
            border_width=2,
            corner_radius=10
        ).pack(pady=20)
        self.add_footer(admin_window)

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logging.info("Application terminated by user")
        finally:
            self.conn.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    try:
        app = SchoolAuthSystem()
        app.run()
    except Exception as e:
        logging.error(f"Application failed to start: {str(e)}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")