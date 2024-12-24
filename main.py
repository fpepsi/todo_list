from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField, RadioField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Optional
from datetime import datetime as dt, timedelta, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Text, DateTime, Date
import json


app = Flask(__name__)
app.secret_key = "your_secret_key"


EST = timezone(timedelta(hours=-5), name="EST") # Defines the timezone as there is no logic built in to customize it
tz = EST
year = dt.now().year # sets footer year disclaimer
members = ["Fabio", "Jana", "Susan", "Claudia"]  # Registered members as there is no logic built in for registration

# create task database
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///tasks_app.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class TaskApp(db.Model):
    __tablename__ = 'tasks'
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Unique identifier for each task
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # Task title
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # Task description (optional)
    due_date: Mapped[dt | None] = mapped_column(Date, nullable=True)  # Due date (optional)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Estimated time in minutes
    estimated_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Estimated time in hours
    estimated_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Estimated time in days
    share_with: Mapped[str | None] = mapped_column(Text, nullable=True)  # Comma-separated list of users
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="work")  # Task category
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="low")  # Priority: low, medium, high
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Completion status
    tabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Tabled status
    created_at: Mapped[dt] = mapped_column(DateTime, default=lambda: dt.now(tz), nullable=False)  # Creation timestamp
    updated_at: Mapped[dt] = mapped_column(DateTime, default=lambda: dt.now(tz), onupdate=lambda: dt.now(tz), nullable=False)  # Update timestamp


    def __repr__(self):
        return f"<Task {self.title} - Category: {self.category}>"

 
with app.app_context():
    db.create_all()


# FlaskForm for the task
class TaskForm(FlaskForm):
    title = StringField("Task Title", validators=[DataRequired()])
    description = TextAreaField("Task Description", validators=[Optional()])
    due_date = DateField("Due Date", format='%Y-%m-%d', validators=[Optional()])
    estimated_minutes = SelectField(
        "Minutes",
        choices=[(0, "0"), (15, "15"), (30, "30"), (45, "45")],
        default=0,
        coerce=int,  # Ensures the selected value is cast to an integer
        validators=[Optional()],
    )
    estimated_hours = SelectField(
        "Hours",
        choices=[(i, str(i)) for i in range(0, 24)],  # Range of 0 to 23
        default=0,
        coerce=int,
        validators=[Optional()],
    )
    estimated_days = SelectField(
        "Days",
        choices=[(i, str(i)) for i in range(0, 32)],  # Range of 0 to 31
        default=0,
        coerce=int,
        validators=[Optional()],
    )
    share_with = SelectMultipleField("Share With", choices=[], validators=[Optional()])
    category = SelectField(
        "Category", 
        choices=[("chores", "Chores"), ("events", "Events"), ("school", "School"), ("work", "Work")],
        default='work',
        validators=[DataRequired()]
    )
    priority = RadioField(
        "Priority", 
        choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")],
        default='low',
        validators=[DataRequired()]
    )
    submit = SubmitField("Add Task")


class TaskStatus(FlaskForm):
    completed = BooleanField("Completed", default=False)
    tabled = BooleanField("Tabled", default=False)


@app.route("/", methods=["GET", "POST"])
def home():
    # fetches database and prepares a list to render
    result = db.session.execute(db.select(TaskApp).order_by(TaskApp.created_at))
    if result:
        tasks = result.scalars().all()
        # create a list from db object and replaces string in share_with column with a list
        task_list = [
        {
        **{key: value for key, value in task.__dict__.items() if not key.startswith('_')},
        "share_with": json.loads(task.share_with) if task.share_with else []
        }
        for task in tasks
        ]       
    else:
        task_list = []
    # creates for for user to populate and splits original list between opened and tabled tasks
    form1 = TaskForm()
    form2 = TaskStatus()
    form1.share_with.choices = [(member, member) for member in members]  # Populate the Share With dropdown
    open_tasks = [
        task for task in task_list 
        if not task["completed"] and not task["tabled"]
    ]
    tabled_tasks = [
        task for task in task_list 
        if not task["completed"] and task["tabled"]
    ]
    
    if form1.validate_on_submit():
        if form1.due_date.data:
            due_date = form1.due_date.data.strftime("%d-%b-%Y")
        else:
            due_date = form1.due_date.data
        if form1.description.data:
            description=form1.description.data
        else:
            description = "Description not provided"
        new_task = TaskApp(
            title=form1.title.data,
            description=description,
            due_date=due_date,
            estimated_minutes=form1.estimated_minutes.data,
            estimated_hours=form1.estimated_hours.data,
            estimated_days=form1.estimated_days.data,
            share_with=json.dumps(form1.share_with.data), # converts list into string
            category=form1.category.data,
            priority=form1.priority.data,
            completed=False,
            tabled=False,
        )
        db.session.add(new_task)
        db.session.commit()

        flash("Task added successfully!", "success")
        return redirect(url_for("home"))
    
    if form2.validate_on_submit():
        task_id = request.form.get("task_id")
        print(f'taskd_id= {task_id}')
        if not task_id:
            flash("No task ID provided.", "error")
            return redirect(url_for('home'))
        
        # Fetch the task from the database
        task = db.session.get(TaskApp, task_id)
        if not task:
            flash("Task not found.", "error")
            return redirect(url_for('home'))

         # Handle the 'completed' checkbox
        if "completed" in request.form:
            task.completed = True
            db.session.commit()
            flash(f"Task '{task.title}' marked as completed.", "success")

        # Handle the 'tabled' checkbox
        elif "tabled" in request.form:
            task.tabled = True
            db.session.commit()
            flash(f"Task '{task.title}' marked as tabled.", "success")

        # Handle the 'delete' button
        else:
            db.session.delete(task)
            db.session.commit()
            flash(f"Task '{task.title}' deleted successfully.", "success")

        return redirect(url_for('home'))

    return render_template("home.html", form1=form1, form2=form2, open_tasks=open_tasks, tabled_tasks=tabled_tasks, year=year)

@app.route("/register")
def register():
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
