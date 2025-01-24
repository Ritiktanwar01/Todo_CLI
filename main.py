import typer
from rich.console import Console
from rich.table import Table
import sqlite3
from typing import List
import datetime
import datetime

#  models handling 

class Todo:
    def __init__(self, task, category, 
                 date_added=None, date_completed=None,
                 status=None, position=None):
        self.task = task
        self.category = category
        self.date_added = date_added if date_added is not None else datetime.datetime.now().isoformat()
        self.date_completed = date_completed if date_completed is not None else None
        self.status = status if status is not None else 1  # 1 = open, 2 = completed
        self.position = position if position is not None else None

    def __repr__(self) -> str:
        return f"({self.task}, {self.category}, {self.date_added}, {self.date_completed}, {self.status}, {self.position})"


#  db handling 


conn = sqlite3.connect('todos.db')
c = conn.cursor()


def create_table():
    c.execute("""CREATE TABLE IF NOT EXISTS todos (
            task text,
            category text,
            date_added text,
            date_completed text,
            status integer,
            position integer
            )""")


create_table()


def insert_todo(todo: Todo):
    c.execute('select count(*) FROM todos')
    count = c.fetchone()[0]
    todo.position = count if count else 0
    with conn:
        c.execute('INSERT INTO todos VALUES (:task, :category, :date_added, :date_completed, :status, :position)',
        {'task': todo.task, 'category': todo.category, 'date_added': todo.date_added,
         'date_completed': todo.date_completed, 'status': todo.status, 'position': todo.position })


def get_all_todos() -> List[Todo]:
    c.execute('select * from todos')
    results = c.fetchall()
    todos = []
    for result in results:
        todos.append(Todo(*result))
    return todos


def delete_todo(position):
    c.execute('select count(*) from todos')
    count = c.fetchone()[0]

    with conn:
        c.execute("DELETE from todos WHERE position=:position", {"position": position})
        for pos in range(position+1, count):
            change_position(pos, pos-1, False)


def change_position(old_position: int, new_position: int, commit=True):
    c.execute('UPDATE todos SET position = :position_new WHERE position = :position_old',
                {'position_old': old_position, 'position_new': new_position})
    if commit:
        conn.commit()


def update_todo(position: int, task: str, category: str):
    with conn:
        if task is not None and category is not None:
            c.execute('UPDATE todos SET task = :task, category = :category WHERE position = :position',
                      {'position': position, 'task': task, 'category': category})
        elif task is not None:
            c.execute('UPDATE todos SET task = :task WHERE position = :position',
                      {'position': position, 'task': task})
        elif category is not None:
            c.execute('UPDATE todos SET category = :category WHERE position = :position',
                      {'position': position, 'category': category})


def complete_todo(position: int):
    with conn:
        c.execute('UPDATE todos SET status = 2, date_completed = :date_completed WHERE position = :position',
                  {'position': position, 'date_completed': datetime.datetime.now().isoformat()})
        

console = Console()

app = typer.Typer()

#  main functions 


@app.command(short_help='adds an item')
def add(task: str, category: str):
    typer.echo(f"adding {task}, {category}")
    todo = Todo(task, category)
    insert_todo(todo)
    show()

@app.command()
def delete(position: int):
    typer.echo(f"deleting {position}")
    # indices in UI begin at 1, but in database at 0
    delete_todo(position-1)
    show()

@app.command()
def update(position: int, task: str = None, category: str = None):
    typer.echo(f"updating {position}")
    update_todo(position-1, task, category)
    show()

@app.command()
def complete(position: int):
    typer.echo(f"complete {position}")
    complete_todo(position-1)
    show()

@app.command()
def show():
    tasks = get_all_todos()
    console.print("[bold magenta]Todos[/bold magenta]!", "💻")

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("#", style="dim", width=6)
    table.add_column("Todo", min_width=20)
    table.add_column("Category", min_width=12, justify="right")
    table.add_column("Done", min_width=12, justify="right")

    def get_category_color(category):
        COLORS = {'Learn': 'cyan', 'YouTube': 'red', 'Sports': 'cyan', 'Study': 'green'}
        if category in COLORS:
            return COLORS[category]
        return 'white'

    for idx, task in enumerate(tasks, start=1):
        c = get_category_color(task.category)
        is_done_str = '✅' if task.status == 2 else '❌'
        table.add_row(str(idx), task.task, f'[{c}]{task.category}[/{c}]', is_done_str)
    console.print(table)


if __name__ == "__main__":
    app()