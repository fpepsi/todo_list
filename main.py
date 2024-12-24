from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, BooleanField, RadioField, SubmitField
from wtforms.validators import DataRequired, Optional

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Mock data
members = ["Alice", "Bob", "Charlie"]  # Registered members
task_list = []  # List to store tasks

# FlaskForm for the task
class TaskForm(FlaskForm):
    title = StringField("Task Title", validators=[DataRequired()])
    description = TextAreaField("Task Description", validators=[Optional()])
    due_date = DateField("Due Date", format='%Y-%m-%d', validators=[Optional()])
    estimated_days = IntegerField("Days", validators=[Optional()])
    estimated_hours = IntegerField("Hours", validators=[Optional()])
    estimated_minutes = IntegerField("Minutes", validators=[Optional()])
    share_with = SelectField("Share With", choices=[], validators=[Optional()])
    category = SelectField(
        "Category", 
        choices=[("chores", "Chores"), ("events", "Events"), ("school", "School"), ("work", "Work")],
        validators=[DataRequired()]
    )
    priority = RadioField(
        "Priority", 
        choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")],
        validators=[DataRequired()]
    )
    completed = BooleanField("Completed")
    tabled = BooleanField("Tabled")
    submit = SubmitField("Add Task")

@app.route("/", methods=["GET", "POST"])
def home():
    form = TaskForm()
    form.share_with.choices = [(member, member) for member in members]  # Populate the Share With dropdown
    today_tasks = [
        task for task in task_list 
        if not task["completed"] and (not task["due_date"] or task["due_date"] >= "2024-01-01")  # Example filter
    ]

    if form.validate_on_submit():
        task = {
            "title": form.title.data,
            "description": form.description.data,
            "due_date": form.due_date.data,
            "estimated_time": f"{form.estimated_days.data or 0}d {form.estimated_hours.data or 0}h {form.estimated_minutes.data or 0}m",
            "share_with": form.share_with.data,
            "category": form.category.data,
            "priority": form.priority.data,
            "completed": form.completed.data,
            "tabled": form.tabled.data,
        }
        task_list.append(task)
        flash("Task added successfully!", "success")
        return redirect(url_for("home"))

    return render_template("home.html", form=form, today_tasks=today_tasks, task_list=task_list)

@app.route("/register")
def register():
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
