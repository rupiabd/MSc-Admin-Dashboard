from flask import Flask, render_template,request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
#from flask_wtf import CSRFProtect


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/csedata'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

#csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define the database models
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    cohort_year = db.Column(db.Integer, nullable=False)

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    grade = db.Column(db.String(2), nullable=False)

    student = db.relationship('Student', backref='results')
    module = db.relationship('Module', backref='results')

# Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/students")
def list_students():
    students = Student.query.all()
    return render_template("students.html", students=students)
@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)  # Fetch student by ID
    if request.method == "POST":
        try:
            student.name = request.form["name"]
            student.email = request.form["email"]
            student.cohort_year = request.form["cohort_year"]
            db.session.commit()
            flash("Student updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating student: {e}", "danger")
        return redirect(url_for("list_students"))
    return render_template("edit_students.html", student=student)

@app.route("/delete-student/<int:student_id>", methods=["POST", "GET"])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash("Student deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting student: {e}", "danger")
    return redirect(url_for("list_students"))

@app.route("/modules")
def list_modules():
    modules = Module.query.all()
    return render_template("modules.html", modules=modules)

@app.route("/results")
def list_results():
    results = db.session.query(
        Result.id,
        Student.name.label("student_name"),
        Module.name.label("module_name"),
        Result.grade
    ).join(Student, Student.id == Result.student_id).join(Module, Module.id == Result.module_id).all()
    return render_template("results.html", results=results)

@app.route("/analytics")
def analytics():
    # Total number of students
    total_students = db.session.query(Student).count()

    # Average grades for each module
    avg_grades = db.session.query(
        Module.name.label("module_name"),
        db.func.avg(db.case(
            (Result.grade == "A", 4),
            (Result.grade == "B", 3),
            (Result.grade == "C", 2),
            else_=1
        )).label("avg_grade")
    ).join(Result, Module.id == Result.module_id).group_by(Module.name).all()

    # Render analytics.html
    return render_template(
        "analytics1.html",
        total_students=total_students,
        avg_grades=avg_grades
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        new_admin_email = request.form.get("admin_email")
        # Save the settings 
        return "Settings updated successfully!"
    return render_template("settings.html")

@app.route("/add-student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        cohort_year = request.form["cohort_year"]
        new_student = Student(name=name, email=email, cohort_year=cohort_year)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for("list_students"))
    return render_template("add_student.html")

@app.route("/add-module", methods=["GET", "POST"])
def add_module():
    if request.method == "POST":
        name = request.form["name"]
        credits = request.form["credits"]
        new_module = Module(name=name, credits=credits)
        db.session.add(new_module)
        db.session.commit()
        return redirect(url_for("list_modules"))
    return render_template("add_module.html")

@app.route("/add-result", methods=["GET", "POST"])
def add_result():
    if request.method == "POST":
        student_id = request.form["student_id"]
        module_id = request.form["module_id"]
        grade = request.form["grade"]
        new_result = Result(student_id=student_id, module_id=module_id, grade=grade)
        db.session.add(new_result)
        db.session.commit()
        return redirect(url_for("list_results"))
    students = Student.query.all()
    modules = Module.query.all()
    return render_template("add_result.html", students=students, modules=modules)

if __name__ == "__main__":
    app.run(debug=True)

