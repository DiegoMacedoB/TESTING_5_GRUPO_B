import sqlite3
import datetime
from enum import Enum
from typing import List, Optional, Union, Dict

# ====================== ENUMERACIONES ======================
class Priority(Enum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3

class TaskStatus(Enum):
    PENDIENTE = 1
    COMPLETADA = 2

# ====================== MODELO DE DATOS ======================
class Task:
    def __init__(self, id: int, title: str, description: str,
                 due_date: datetime.datetime, priority: Priority,
                 status: TaskStatus, created_at: datetime.datetime):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
        self.created_at = created_at

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Task':
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            due_date=datetime.datetime.fromisoformat(row["due_date"]),
            priority=Priority[row["priority"]],
            status=TaskStatus[row["status"]],
            created_at=datetime.datetime.fromisoformat(row["created_at"])
        )

# ====================== GESTOR CON SQLITE ======================
class TaskManager:
    DB_FILE = "tasks.db"
    MAX_TITLE_LENGTH = 50

    def __init__(self):
        self._conn = sqlite3.connect(self.DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
        self._conn = sqlite3.connect(
            self.DB_FILE,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self):
        SQL = """
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            due_date    TEXT NOT NULL,
            priority    TEXT NOT NULL,
            status      TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );
        """
        self._conn.execute(SQL)
        self._conn.commit()

    def add_task(self, title: str, description: str,
                due_date_str: str, priority_str: str) -> Union[str, Task]:
        # Validaciones básicas
        title = title.strip()
        if not title:
            return "Error: El título no puede estar vacío."
        if len(title) > self.MAX_TITLE_LENGTH:
            return f"Error: El título no puede exceder {self.MAX_TITLE_LENGTH} caracteres."

        # Verificación de duplicados (solo para nuevas tareas)
        existing_task = self._conn.execute(
            "SELECT id FROM tasks WHERE LOWER(title) = LOWER(?) AND LOWER(description) = LOWER(?)",
            (title, description)
        ).fetchone()
        
        if existing_task:
            return "ERR0R: Ya existe una tarea similar"

        try:
            due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
            priority = Priority[priority_str.upper()]
            
            # Validación de fecha
            now = datetime.datetime.now()
            if due_date < now:
                return "Error: La fecha no puede ser en el pasado."
            if due_date > now + datetime.timedelta(days=365*2):
                return "Error: La fecha no puede ser mayor a 2 años."

        except ValueError:
            return "Error: Formato de fecha inválido (Use YYYY-MM-DD HH:MM)"
        except KeyError:
            return "Error: Prioridad inválida (Use BAJA, MEDIA o ALTA)"

        # Insertar nueva tarea
        try:
            cur = self._conn.execute(
                """INSERT INTO tasks 
                (title, description, due_date, priority, status, created_at) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (title, description, due_date.isoformat(), 
                priority.name, TaskStatus.PENDIENTE.name,
                datetime.datetime.now().isoformat())
            )
            self._conn.commit()
            return self.get_task(cur.lastrowid)
        except sqlite3.Error as e:
            return f"Error en la base de datos: {str(e)}"

    def get_task(self, task_id: int) -> Optional[Task]:
        cur = self._conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return Task.from_row(row) if row else None

    def update_task(self, task_id: int, title: str = None,
                    description: str = None, due_date_str: str = None,
                    priority_str: str = None) -> Union[str, Task]:
        task = self.get_task(task_id)
        # recortamos espacios y validamos
        title = title.strip()
        if not title:
            return "Error: El título no puede estar vacío ni contener sólo espacios."
        if len(title) > self.MAX_TITLE_LENGTH:
            return f"Error: El título debe tener como máximo {self.MAX_TITLE_LENGTH} caracteres."
        if not task:
            return f"Error: No se encontró una tarea con ID {task_id}"
        updates, params = [], []
        if title is not None:
            if not title or len(title) > self.MAX_TITLE_LENGTH:
                return f"Error: El título debe tener entre 1 y {self.MAX_TITLE_LENGTH} caracteres."
            updates.append("title = ?"); params.append(title)
        if description is not None:
            updates.append("description = ?"); params.append(description)
        if due_date_str is not None:
            try:
                new_due = datetime.datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
                now = datetime.datetime.now()
                max_due = now + datetime.timedelta(days=365*2)
                if new_due < now:
                    return "Error: La fecha de vencimiento no puede ser anterior a hoy."
                if new_due > max_due:
                    return "Error: La fecha de vencimiento no puede superar los 2 años a partir de hoy."
                updates.append("due_date = ?"); params.append(new_due.isoformat())
            except ValueError:
                return "Error: Formato de fecha incorrecto. Use YYYY-MM-DD HH:MM"
        if priority_str is not None:
            try:
                Priority[priority_str.upper()]
                updates.append("priority = ?"); params.append(priority_str.upper())
            except KeyError:
                return "Error: Prioridad inválida. Use BAJA, MEDIA o ALTA."
        if not updates:
            return task  
        params.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        self._conn.execute(sql, params)
        self._conn.commit()
        return self.get_task(task_id)

    def toggle_task_status(self, task_id: int) -> Union[str, Task]:
        task = self.get_task(task_id)
        if not task:
            return f"Error: No se encontró la tarea con ID {task_id}"

        new_status = TaskStatus.COMPLETADA.name if task.status == TaskStatus.PENDIENTE else TaskStatus.PENDIENTE.name
        self._conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        self._conn.commit()
        return self.get_task(task_id)

    def delete_task(self, task_id: int) -> Union[str, bool]:
        if not self.get_task(task_id):
            return f"Error: No se encontró una tarea con ID {task_id}"
        self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()
        return True

    def get_all_tasks(self, order_by: str = "due_date", direction: str = "asc") -> List[Task]:
            valid_columns = {"id", "title", "description", "due_date", "priority", "status", "created_at"}
            if order_by not in valid_columns:
                order_by = "due_date"
            if direction.lower() not in {"asc", "desc"}:
                direction = "asc"
            sql = f"SELECT * FROM tasks ORDER BY {order_by} {direction.upper()}"
            cur = self._conn.execute(sql)
            return [Task.from_row(row) for row in cur.fetchall()]

    def __del__(self):
        self._conn.close()
