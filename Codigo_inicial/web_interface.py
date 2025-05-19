#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template_string, request, redirect, url_for
from Gestor_tareas import TaskManager, Task, TaskStatus, Priority
import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necesario para sesiones Flask

# Inicializar el gestor de tareas
task_manager = TaskManager()

# HTML Template mejorado
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestor de Tareas</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .priority-high { color: #e74c3c; font-weight: bold; }
        .priority-medium { color: #f39c12; }
        .priority-low { color: #2ecc71; }
        .completed { text-decoration: line-through; color: #95a5a6; }
        .actions a { margin-right: 10px; color: #3498db; text-decoration: none; }
        .actions a:hover { text-decoration: underline; }
        form { background: #f9f9f9; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], textarea, select { 
            width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; 
            box-sizing: border-box; margin-bottom: 10px; 
        }
        textarea { 
            height: 100px; 
            min-height: 100px;
            resize: none;
            overflow: auto;
        }
        button { 
            background-color: #4CAF50; color: white; padding: 10px 15px; 
            border: none; border-radius: 4px; cursor: pointer; 
        }
        button:hover { background-color: #45a049; }
        .error { color: #e74c3c; margin: 10px 0; }
        .success { color: #2ecc71; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Gestor de Tareas</h1>
    
    <!-- Mensajes de estado -->
    {% if message %}
        <div class="{{ 'success' if message_type == 'success' else 'error' }}">{{ message }}</div>
    {% endif %}
    
    <!-- Formulario para agregar/editar tarea -->
    <form method="POST" action="{{ form_action }}">
        <h2>{{ form_title }}</h2>
        <input type="hidden" name="task_id" value="{{ task.id if task else '' }}">
        
        <div class="form-group">
            <label for="title">Título:</label>
            <input type="text" id="title" name="title" value="{{ task_data.title if task_data else (task.title if task else '') }}">
        </div>
        
        <div class="form-group">
            <label for="description">Descripción:</label>
            <textarea id="description" name="description">{{ task_data.description if task_data else (task.description if task else '') }}</textarea>
        </div>
        
        <div class="form-group">
            <label for="due_date">Fecha vencimiento (YYYY-MM-DD HH:MM):</label>
            <input type="text" id="due_date" name="due_date" 
                   value="{{ task.due_date.strftime('%Y-%m-%d %H:%M') if task else '' }}" required>
        </div>
        
        <div class="form-group">
            <label for="priority">Prioridad:</label>
            <select id="priority" name="priority">
                {% for level in ['BAJA', 'MEDIA', 'ALTA'] %}
                    <option value="{{ level }}" 
                        {% if task_data and task_data.priority == level %}
                            selected
                        {% elif task and task.priority.name == level %}
                            selected
                        {% endif %}>
                        {{ level.capitalize() }}
                    </option>
                {% endfor %}
            </select>
        </div>
        
        <button type="submit">{{ 'Actualizar' if task else 'Agregar' }} Tarea</button>
        {% if task %}
            <a href="{{ url_for('index') }}" style="margin-left: 10px;">Cancelar</a>
        {% endif %}
    </form>

    <!-- Lista de tareas -->
    <h2>Tus Tareas</h2>
    <table>
        <thead>
            <tr>
                <th>
                    <a href="{{ url_for('index', order_by='title', direction='desc' if order_by == 'title' and direction == 'asc' else 'asc') }}">
                        Título
                        {% if order_by == 'title' %}
                            {% if direction == 'asc' %}▲{% else %}▼{% endif %}
                        {% endif %}
                    </a>
                </th>
                <th>
                    <a href="{{ url_for('index', order_by='description', direction='desc' if order_by == 'description' and direction == 'asc' else 'asc') }}">
                        Descripción
                        {% if order_by == 'description' %}
                            {% if direction == 'asc' %}▲{% else %}▼{% endif %}
                        {% endif %}
                    </a>
                </th>
                <th>
                    <a href="{{ url_for('index', order_by='due_date', direction='desc' if order_by == 'due_date' and direction == 'asc' else 'asc') }}">
                        Vencimiento
                        {% if order_by == 'due_date' %}
                            {% if direction == 'asc' %}▲{% else %}▼{% endif %}
                        {% endif %}
                    </a>
                </th>
                <th>
                    <a href="{{ url_for('index', order_by='priority', direction='desc' if order_by == 'priority' and direction == 'asc' else 'asc') }}">
                        Prioridad
                        {% if order_by == 'priority' %}
                            {% if direction == 'asc' %}▲{% else %}▼{% endif %}
                        {% endif %}
                    </a>
                </th>
                <th>
                    <a href="{{ url_for('index', order_by='status', direction='desc' if order_by == 'status' and direction == 'asc' else 'asc') }}">
                        Estado
                        {% if order_by == 'status' %}
                            {% if direction == 'asc' %}▲{% else %}▼{% endif %}
                        {% endif %}
                    </a>
                </th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for task in tasks %}
            <tr class="{{ 'completed' if task.status.name == 'COMPLETADA' else '' }}">
                <td>{{ task.title }}</td>
                <td>{{ task.description[:50] }}{% if task.description|length > 50 %}...{% endif %}</td>
                <td>{{ task.due_date.strftime('%Y-%m-%d %H:%M') }}</td>
                <td class="priority-{{ task.priority.name.lower() }}">{{ task.priority.name }}</td>
                <td>{{ task.status.name }}</td>
                <td class="actions">
                    <a href="{{ url_for('edit_task', task_id=task.id) }}">Editar</a>
                    <a href="{{ url_for('toggle_task_status', task_id=task.id) }}" 
                    style="color: {{ '#2ecc71' if task.status.name == 'COMPLETADA' else '#e74c3c' }}">
                        {{ 'Marcar Pendiente' if task.status.name == 'COMPLETADA' else 'Completar' }}
                    </a>
                    <a href="{{ url_for('delete_task', task_id=task.id) }}" 
                    onclick="return confirm('¿Eliminar esta tarea?')">Eliminar</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route('/')
def index():
    """Página principal que muestra todas las tareas"""
    order_by = request.args.get('order_by', 'due_date')
    direction = request.args.get('direction', 'asc')
    tasks = task_manager.get_all_tasks(order_by=order_by, direction=direction)
    message = request.args.get('message')
    message_type = request.args.get('message_type')
    return render_template_string(HTML_TEMPLATE, 
                                tasks=tasks,
                                form_title="Agregar Nueva Tarea",
                                form_action=url_for('add_task'),
                                message=message,
                                message_type=message_type,
                                order_by=order_by,
                                direction=direction)

@app.route('/add', methods=['POST'])
def add_task():
    """Agrega una nueva tarea"""
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['due_date']
    priority = request.form['priority']
    
    result = task_manager.add_task(title, description, due_date, priority)
    
    if isinstance(result, Task):
        return redirect(url_for('index', 
                              message="Tarea creada con éxito", 
                              message_type="success"))
    else:
        return render_template_string(HTML_TEMPLATE,
                                   tasks=task_manager.get_all_tasks(),
                                   form_title="Agregar Nueva Tarea",
                                   form_action=url_for('add_task'),
                                   message=result,
                                   message_type="error")

@app.route('/edit/<int:task_id>')
def edit_task(task_id):
    """Muestra el formulario de edición"""
    task = task_manager.get_task(task_id)
    if not task:
        return redirect(url_for('index', 
                              message=f"No se encontró la tarea con ID {task_id}", 
                              message_type="error"))
    
    return render_template_string(HTML_TEMPLATE,
                               tasks=task_manager.get_all_tasks(),
                               task=task,
                               form_title="Editar Tarea",
                               form_action=url_for('update_task'))
@app.route('/update', methods=['POST'])
def update_task():
    """Actualiza una tarea existente sin modificar el estado"""
    task_id = int(request.form['task_id'])
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['due_date']
    priority = request.form['priority']
    
    # Solo actualiza los campos básicos (sin estado)
    result = task_manager.update_task(
        task_id, title=title, description=description,
        due_date_str=due_date, priority_str=priority
    )
    
    if isinstance(result, str):  # Si hay error
        return render_template_string(HTML_TEMPLATE,
                                   tasks=task_manager.get_all_tasks(),
                                   task=task_manager.get_task(task_id),
                                   form_title="Editar Tarea",  
                                   form_action=url_for('update_task'),
                                   message=result,
                                   message_type="error")
    
    return redirect(url_for('index', 
                          message="Tarea actualizada con éxito", 
                          message_type="success"))
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    """Elimina una tarea"""
    result = task_manager.delete_task(task_id)
    
    if result is True:
        return redirect(url_for('index', 
                              message="Tarea eliminada con éxito", 
                              message_type="success"))
    else:
        return redirect(url_for('index', 
                              message=result, 
                              message_type="error"))
@app.route('/toggle_task_status/<int:task_id>')
def toggle_task_status(task_id):
    result = task_manager.toggle_task_status(task_id)
    if isinstance(result, Task):
        status = "COMPLETADA" if result.status == TaskStatus.COMPLETADA else "PENDIENTE"
        return redirect(url_for('index', 
                             message=f"Estado cambiado a {status}", 
                             message_type="success"))
    else:
        return redirect(url_for('index', 
                             message=result, 
                             message_type="error"))
if __name__ == '__main__':
    app.run(debug=True, port=5000)
