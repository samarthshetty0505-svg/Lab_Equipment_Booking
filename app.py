from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)

app.secret_key = "lab_booking_secret_key"


# -----------------------------------------
# DATABASE CONNECTION
# -----------------------------------------

def get_db():
    connection = sqlite3.connect("lab_booking.db")
    connection.row_factory = sqlite3.Row
    return connection


# -----------------------------------------
# CREATE DATABASE TABLES
# -----------------------------------------

def init_db():

    connection = get_db()
    cursor = connection.cursor()

    # Students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Staff table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Admin table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Equipment table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        quantity INTEGER NOT NULL,
        available INTEGER NOT NULL
    )
    """)

    # Bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        equipment TEXT NOT NULL,
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        purpose TEXT NOT NULL,
        status TEXT DEFAULT 'Pending'
    )
    """)

    # Default student
    cursor.execute("""
    INSERT OR IGNORE INTO students
    (student_id, password)
    VALUES (?, ?)
    """, ("STU001", "12345"))

    # Default staff
    cursor.execute("""
    INSERT OR IGNORE INTO staff
    (username, password)
    VALUES (?, ?)
    """, ("staff", "staff123"))

    # Default admin
    cursor.execute("""
    INSERT OR IGNORE INTO admins
    (username, password)
    VALUES (?, ?)
    """, ("admin", "admin123"))

    # Default equipment
    equipment_list = [
        ("Digital Multimeter", 5),
        ("Oscilloscope", 3),
        ("Function Generator", 4),
        ("CRO", 2),
        ("Power Supply", 5),
        ("Signal Generator", 3)
    ]

    for name, quantity in equipment_list:

        cursor.execute("""
        INSERT OR IGNORE INTO equipment
        (name, quantity, available)
        VALUES (?, ?, ?)
        """, (name, quantity, quantity))

    connection.commit()
    connection.close()


# -----------------------------------------
# HOME PAGE
# -----------------------------------------

@app.route("/")
def home():

    return render_template("home.html")


# -----------------------------------------
# STUDENT REGISTRATION
# -----------------------------------------

@app.route("/student-register", methods=["GET", "POST"])
def student_register():

    message = ""

    if request.method == "POST":

        student_id = request.form["student_id"]
        password = request.form["password"]

        connection = get_db()

        try:

            connection.execute("""
            INSERT INTO students
            (student_id, password)
            VALUES (?, ?)
            """, (student_id, password))

            connection.commit()
            connection.close()

            return redirect(url_for("student_login"))

        except sqlite3.IntegrityError:

            connection.close()

            message = "Student ID already exists."

    return render_template(
        "student_register.html",
        message=message
    )


# -----------------------------------------
# STUDENT LOGIN
# -----------------------------------------

@app.route("/student-login", methods=["GET", "POST"])
def student_login():

    message = ""

    if request.method == "POST":

        student_id = request.form["student_id"]
        password = request.form["password"]

        connection = get_db()

        student = connection.execute("""
        SELECT * FROM students
        WHERE student_id = ?
        AND password = ?
        """, (student_id, password)).fetchone()

        connection.close()

        if student:

            session["student_id"] = student_id

            return redirect(
                url_for("student_dashboard")
            )

        message = "Invalid Student ID or Password."

    return render_template(
        "student_login.html",
        message=message
    )


# -----------------------------------------
# STUDENT DASHBOARD
# -----------------------------------------

@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    return render_template(
        "student_dashboard.html",
        student_id=session["student_id"]
    )


# -----------------------------------------
# VIEW EQUIPMENT
# -----------------------------------------

@app.route("/equipment")
def equipment():

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    connection = get_db()

    equipment_list = connection.execute("""
    SELECT * FROM equipment
    ORDER BY name
    """).fetchall()

    connection.close()

    return render_template(
        "equipment.html",
        equipment_list=equipment_list
    )


# -----------------------------------------
# BOOK EQUIPMENT
# -----------------------------------------

@app.route("/book-equipment", methods=["GET", "POST"])
def book_equipment():

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    message = ""
    error = ""

    connection = get_db()

    equipment_list = connection.execute("""
    SELECT * FROM equipment
    ORDER BY name
    """).fetchall()

    if request.method == "POST":

        equipment = request.form["equipment"]
        date = request.form["date"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        purpose = request.form["purpose"]

        # Check time
        if start_time >= end_time:

            error = "End time must be later than start time."

        else:

            # Check equipment availability
            item = connection.execute("""
            SELECT * FROM equipment
            WHERE name = ?
            """, (equipment,)).fetchone()

            if item is None:

                error = "Equipment not found."

            elif item["available"] <= 0:

                error = "Equipment is currently not available."

            else:

                connection.execute("""
                INSERT INTO bookings
                (
                    student_id,
                    equipment,
                    date,
                    start_time,
                    end_time,
                    purpose,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session["student_id"],
                    equipment,
                    date,
                    start_time,
                    end_time,
                    purpose,
                    "Pending"
                ))

                connection.commit()

                message = "Booking submitted successfully!"

    connection.close()

    return render_template(
        "book_equipment.html",
        student_id=session["student_id"],
        equipment_list=equipment_list,
        message=message,
        error=error
    )


# -----------------------------------------
# MY BOOKINGS
# -----------------------------------------

@app.route("/my-bookings")
def my_bookings():

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    connection = get_db()

    bookings = connection.execute("""
    SELECT *
    FROM bookings
    WHERE student_id = ?
    ORDER BY id DESC
    """, (session["student_id"],)).fetchall()

    connection.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )


# -----------------------------------------
# CANCEL BOOKING
# -----------------------------------------

@app.route("/cancel-booking/<int:booking_id>")
def cancel_booking(booking_id):

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    connection = get_db()

    connection.execute("""
    UPDATE bookings
    SET status = 'Cancelled'
    WHERE id = ?
    AND student_id = ?
    AND status = 'Pending'
    """, (
        booking_id,
        session["student_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(
        url_for("my_bookings")
    )


# -----------------------------------------
# STAFF LOGIN
# -----------------------------------------

@app.route("/staff-login", methods=["GET", "POST"])
def staff_login():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db()

        staff = connection.execute("""
        SELECT *
        FROM staff
        WHERE username = ?
        AND password = ?
        """, (username, password)).fetchone()

        connection.close()

        if staff:

            session["staff"] = username

            return redirect(
                url_for("staff_dashboard")
            )

        message = "Invalid Staff Username or Password."

    return render_template(
        "staff_login.html",
        message=message
    )


# -----------------------------------------
# STAFF DASHBOARD
# -----------------------------------------

@app.route("/staff-dashboard")
def staff_dashboard():

    if "staff" not in session:

        return redirect(
            url_for("staff_login")
        )

    connection = get_db()

    bookings = connection.execute("""
    SELECT *
    FROM bookings
    ORDER BY id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "staff_dashboard.html",
        bookings=bookings
    )


# -----------------------------------------
# APPROVE BOOKING
# -----------------------------------------

@app.route("/approve-booking/<int:booking_id>")
def approve_booking(booking_id):

    if "staff" not in session:

        return redirect(
            url_for("staff_login")
        )

    connection = get_db()
    cursor = connection.cursor()

    booking = cursor.execute("""
    SELECT *
    FROM bookings
    WHERE id = ?
    """, (booking_id,)).fetchone()

    if booking and booking["status"] == "Pending":

        equipment = cursor.execute("""
        SELECT *
        FROM equipment
        WHERE name = ?
        """, (booking["equipment"],)).fetchone()

        if equipment and equipment["available"] > 0:

            cursor.execute("""
            UPDATE bookings
            SET status = 'Approved'
            WHERE id = ?
            """, (booking_id,))

            cursor.execute("""
            UPDATE equipment
            SET available = available - 1
            WHERE name = ?
            """, (booking["equipment"],))

        else:

            cursor.execute("""
            UPDATE bookings
            SET status = 'Rejected'
            WHERE id = ?
            """, (booking_id,))

    connection.commit()
    connection.close()

    return redirect(
        url_for("staff_dashboard")
    )


# -----------------------------------------
# REJECT BOOKING
# -----------------------------------------

@app.route("/reject-booking/<int:booking_id>")
def reject_booking(booking_id):

    if "staff" not in session:

        return redirect(
            url_for("staff_login")
        )

    connection = get_db()

    connection.execute("""
    UPDATE bookings
    SET status = 'Rejected'
    WHERE id = ?
    AND status = 'Pending'
    """, (booking_id,))

    connection.commit()
    connection.close()

    return redirect(
        url_for("staff_dashboard")
    )


# -----------------------------------------
# RETURN EQUIPMENT
# -----------------------------------------

@app.route("/return-booking/<int:booking_id>")
def return_booking(booking_id):

    if "staff" not in session:

        return redirect(
            url_for("staff_login")
        )

    connection = get_db()
    cursor = connection.cursor()

    booking = cursor.execute("""
    SELECT *
    FROM bookings
    WHERE id = ?
    """, (booking_id,)).fetchone()

    if booking and booking["status"] == "Approved":

        cursor.execute("""
        UPDATE bookings
        SET status = 'Returned'
        WHERE id = ?
        """, (booking_id,))

        cursor.execute("""
        UPDATE equipment
        SET available = available + 1
        WHERE name = ?
        """, (booking["equipment"],))

    connection.commit()
    connection.close()

    return redirect(
        url_for("staff_dashboard")
    )


# -----------------------------------------
# ADMIN LOGIN
# -----------------------------------------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db()

        admin = connection.execute("""
        SELECT *
        FROM admins
        WHERE username = ?
        AND password = ?
        """, (username, password)).fetchone()

        connection.close()

        if admin:

            session["admin"] = username

            return redirect(
                url_for("admin_dashboard")
            )

        message = "Invalid Admin Username or Password."

    return render_template(
        "admin_login.html",
        message=message
    )


# -----------------------------------------
# ADMIN DASHBOARD
# -----------------------------------------

@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:

        return redirect(
            url_for("admin_login")
        )

    connection = get_db()

    students = connection.execute("""
    SELECT *
    FROM students
    ORDER BY id DESC
    """).fetchall()

    equipment_list = connection.execute("""
    SELECT *
    FROM equipment
    ORDER BY name
    """).fetchall()

    bookings = connection.execute("""
    SELECT *
    FROM bookings
    ORDER BY id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        equipment_list=equipment_list,
        bookings=bookings
    )


# -----------------------------------------
# ADD EQUIPMENT
# -----------------------------------------

@app.route("/add-equipment", methods=["POST"])
def add_equipment():

    if "admin" not in session:

        return redirect(
            url_for("admin_login")
        )

    name = request.form["name"]
    quantity = int(request.form["quantity"])

    connection = get_db()

    try:

        connection.execute("""
        INSERT INTO equipment
        (name, quantity, available)
        VALUES (?, ?, ?)
        """, (name, quantity, quantity))

        connection.commit()

    except sqlite3.IntegrityError:

        pass

    connection.close()

    return redirect(
        url_for("admin_dashboard")
    )


# -----------------------------------------
# DELETE EQUIPMENT
# -----------------------------------------

@app.route("/delete-equipment/<int:equipment_id>")
def delete_equipment(equipment_id):

    if "admin" not in session:

        return redirect(
            url_for("admin_login")
        )

    connection = get_db()

    connection.execute("""
    DELETE FROM equipment
    WHERE id = ?
    """, (equipment_id,))

    connection.commit()
    connection.close()

    return redirect(
        url_for("admin_dashboard")
    )


# -----------------------------------------
# LOGOUT
# -----------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# -----------------------------------------
# START APPLICATION
# -----------------------------------------

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
