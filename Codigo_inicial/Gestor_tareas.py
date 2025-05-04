#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal del Gestor de Tareas

Contiene las clases fundamentales para gestionar tareas:
- Priority: Enumera los niveles de prioridad
- TaskStatus: Enumera los estados de las tareas
- Task: Modelo de datos para representar una tarea
- TaskManager: Lógica principal para gestión de tareas
"""

# Importaciones estándar
import datetime
import json
import os
from enum import Enum
from typing import Dict, List, Optional, Union

# ====================== ENUMERACIONES ======================
class Priority(Enum):
    """Niveles de prioridad para las tareas"""
    BAJA = 1
    MEDIA = 2
    ALTA = 3


class TaskStatus(Enum):
    """Estados posibles de una tarea"""
    PENDIENTE = 1
    COMPLETADA = 2


# ====================== MODELO DE DATOS ======================
class Task:
    """
    Representa una tarea en el sistema con sus atributos y métodos de conversión.
    
    Atributos:
        id: Identificador único (autogenerado)
        title: Título de la tarea (max 50 caracteres)
        description: Descripción detallada
        due_date: Fecha de vencimiento
        priority: Nivel de prioridad (Priority enum)
        status: Estado actual (TaskStatus enum)
        created_at: Fecha de creación (autogenerada)
    """
    
    def __init__(self, title: str, description: str, 
                 due_date: datetime.datetime, priority: Priority):
        """Inicializa una nueva tarea con estado PENDIENTE por defecto"""
        self.id = None  # Se asignará al guardar
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = TaskStatus.PENDIENTE
        self.created_at = datetime.datetime.now()
    
    def to_dict(self) -> Dict:
        """Serializa la tarea a diccionario para almacenamiento"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "priority": self.priority.name,
            "status": self.status.name,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Crea una tarea a partir de un diccionario serializado"""
        task = cls(
            title=data["title"],
            description=data["description"],
            due_date=datetime.datetime.fromisoformat(data["due_date"]),
            priority=Priority[data["priority"]]
        )
        task.id = data["id"]
        task.status = TaskStatus[data["status"]]
        task.created_at = datetime.datetime.fromisoformat(data["created_at"])
        return task


# ====================== LÓGICA PRINCIPAL ======================
class TaskManager:
    """
    Gestor principal de tareas con persistencia en JSON.
    
    Funcionalidades:
        - CRUD completo de tareas
        - Filtrado y ordenación
        - Persistencia automática en archivo
    """
    
    # Configuración
    DATA_FILE = "tasks.json"
    MAX_TITLE_LENGTH = 50
    
    def __init__(self):
        """Inicializa el gestor y carga tareas existentes"""
        self.tasks = {}
        self.next_id = 1
        self.load_tasks()
    
    # ================= OPERACIONES BÁSICAS =================
    def add_task(self, title: str, description: str, 
                due_date_str: str, priority_str: str) -> Union[str, Task]:
        """
        Agrega una nueva tarea con validación de datos.
        
        Args:
            title: Título (1-50 caracteres)
            description: Descripción detallada
            due_date_str: Fecha en formato "YYYY-MM-DD HH:MM"
            priority_str: "BAJA", "MEDIA" o "ALTA"
            
        Returns:
            Task si es exitoso, str con mensaje de error si falla
        """
        # Validaciones
        if not title or len(title) > self.MAX_TITLE_LENGTH:
            return f"Error: El título debe tener entre 1 y {self.MAX_TITLE_LENGTH} caracteres."
        
        try:
            due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
            priority = Priority[priority_str.upper()]
        except ValueError:
            return "Error: Formato de fecha incorrecto. Use YYYY-MM-DD HH:MM"
        except KeyError:
            return "Error: Prioridad inválida. Use BAJA, MEDIA o ALTA."
        
        # Creación y almacenamiento
        task = Task(title, description, due_date, priority)
        task.id = self.next_id
        self.tasks[self.next_id] = task
        self.next_id += 1
        self.save_tasks()
        return task
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Obtiene una tarea por su ID o None si no existe"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: int, title: str = None, 
                   description: str = None, due_date_str: str = None, 
                   priority_str: str = None) -> Union[str, Task]:
        """
        Actualiza una tarea existente.
        
        Args:
            task_id: ID de la tarea a modificar
            title/due_date_str/priority_str: Nuevos valores (opcionales)
            
        Returns:
            Task actualizada o str con error
        """
        task = self.get_task(task_id)
        if not task:
            return f"Error: No se encontró una tarea con ID {task_id}"
        
        # Actualización condicional de campos
        if title is not None:
            if not title or len(title) > self.MAX_TITLE_LENGTH:
                return f"Error: El título debe tener entre 1 y {self.MAX_TITLE_LENGTH} caracteres."
            task.title = title
        
        if description is not None:
            task.description = description
        
        if due_date_str is not None:
            try:
                task.due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return "Error: Formato de fecha incorrecto. Use YYYY-MM-DD HH:MM"
            
        if due_date_str is not None:
            try:
                new_due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
                if new_due_date < datetime.datetime.now():
                    return "Error: La fecha de vencimiento no puede ser en el pasado"
                task.due_date = new_due_date
            except ValueError:
                return "Error: Formato de fecha incorrecto. Use YYYY-MM-DD HH:MM"
        if priority_str is not None:
            try:
                task.priority = Priority[priority_str.upper()]
            except KeyError:
                return "Error: Prioridad inválida. Use BAJA, MEDIA o ALTA."
        
        self.save_tasks()
        return task
    
    def toggle_task_status(self, task_id: int) -> Union[str, Task]:
        """Alterna entre PENDIENTE/COMPLETADA"""
        task = self.get_task(task_id)
        if not task:
            return f"Error: No se encontró la tarea con ID {task_id}"
        
        task.status = TaskStatus.COMPLETADA if task.status == TaskStatus.PENDIENTE else TaskStatus.PENDIENTE
        self.save_tasks()
        return task
        
    def delete_task(self, task_id: int) -> Union[str, bool]:
        """Elimina una tarea permanentemente"""
        if task_id not in self.tasks:
            return f"Error: No se encontró una tarea con ID {task_id}"
        
        del self.tasks[task_id]
        self.save_tasks()
        return True
    
    # ================= CONSULTAS =================
    def get_all_tasks(self) -> List[Task]:
        """Devuelve todas las tareas como lista"""
        return list(self.tasks.values())
    
    def filter_tasks(self, status: TaskStatus = None, search_term: str = None, 
                    priority: Priority = None, date_from: datetime.datetime = None, 
                    date_to: datetime.datetime = None) -> List[Task]:
        """
        Filtra tareas por múltiples criterios.
        
        Args:
            status: Estado a filtrar
            search_term: Texto a buscar en título/descripción
            priority: Prioridad específica
            date_from/date_to: Rango de fechas
            
        Returns:
            Lista de tareas filtradas
        """
        filtered = self.get_all_tasks()
        
        if status: filtered = [t for t in filtered if t.status == status]
        if search_term:
            term = search_term.lower()
            filtered = [t for t in filtered if term in t.title.lower() or term in t.description.lower()]
        if priority: filtered = [t for t in filtered if t.priority == priority]
        if date_from: filtered = [t for t in filtered if t.due_date >= date_from]
        if date_to: filtered = [t for t in filtered if t.due_date <= date_to]
        
        return filtered
    
    def sort_tasks(self, tasks: List[Task], sort_by: str = "due_date", 
                  ascending: bool = True) -> List[Task]:
        """
        Ordena tareas por criterio.
        
        Args:
            tasks: Lista a ordenar
            sort_by: "due_date", "priority" o "title"
            ascending: Orden ascendente/descendente
            
        Returns:
            Lista ordenada
        """
        reverse = not ascending
        if sort_by == "due_date":
            return sorted(tasks, key=lambda t: t.due_date, reverse=reverse)
        elif sort_by == "priority":
            return sorted(tasks, key=lambda t: t.priority.value, reverse=reverse)
        elif sort_by == "title":
            return sorted(tasks, key=lambda t: t.title.lower(), reverse=reverse)
        return tasks
    
    # ================= PERSISTENCIA =================
    def load_tasks(self) -> None:
        """Carga tareas desde el archivo JSON"""
        if not os.path.exists(self.DATA_FILE):
            self.tasks = {}
            self.next_id = 1
            return
        
        try:
            with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = {int(tid): Task.from_dict(tdata) 
                            for tid, tdata in data["tasks"].items()}
                self.next_id = data["next_id"]
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            self.tasks = {}
            self.next_id = 1
    
    def save_tasks(self) -> None:
        """Guarda todas las tareas en archivo JSON"""
        data = {
            "tasks": {str(t.id): t.to_dict() for t in self.tasks.values()},
            "next_id": self.next_id
        }
        with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


