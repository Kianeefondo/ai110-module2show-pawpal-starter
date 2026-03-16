from datetime import datetime, timedelta


class Task:
    def __init__(self, task_id, description, scheduled_time=None, frequency="once", completed=False):
        self.task_id = task_id
        self.description = description
        self.scheduled_time = scheduled_time
        self.frequency = frequency
        self.completed = completed

    def mark_completed(self):
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self):
        """Mark this task as not completed."""
        self.completed = False

    def reschedule(self, new_time):
        """Update this task's scheduled time."""
        self.scheduled_time = new_time

    def get_next_occurrence(self):
        """Return the next scheduled datetime based on recurrence frequency."""
        if not self.scheduled_time:
            return None
        if self.frequency == "daily":
            return self.scheduled_time + timedelta(days=1)
        if self.frequency == "weekly":
            return self.scheduled_time + timedelta(weeks=1)
        return None

    def complete_and_reschedule(self):
        """Mark as completed and reschedule recurring tasks."""
        self.mark_completed()
        next_time = self.get_next_occurrence()
        if next_time:
            self.completed = False
            self.scheduled_time = next_time
            return True
        return False

    def __repr__(self):
        status = "✓" if self.completed else "✗"
        return f"Task({self.task_id}, {self.description!r}, {self.scheduled_time}, {self.frequency}, {status})"


class Pet:
    def __init__(self, pet_id, name, species, owner=None):
        self.pet_id = pet_id
        self.name = name
        self.species = species
        self.owner = owner
        self.tasks = []

    def add_task(self, task):
        """Add a task to this pet."""
        if not isinstance(task, Task):
            raise TypeError("Expected Task instance")
        self.tasks.append(task)

    def get_tasks(self, completed=None):
        """Return this pet's tasks, optionally filtering by completion."""
        if completed is None:
            return list(self.tasks)
        return [task for task in self.tasks if task.completed == completed]

    def __repr__(self):
        return f"Pet({self.pet_id}, {self.name!r}, {self.species!r}, tasks={len(self.tasks)})"


class Owner:
    def __init__(self, owner_id, name, contact_info):
        self.owner_id = owner_id
        self.name = name
        self.contact_info = contact_info
        self.pets = []

    def add_pet(self, pet):
        """Add a pet to this owner's list."""
        if not isinstance(pet, Pet):
            raise TypeError("Expected Pet instance")
        pet.owner = self
        self.pets.append(pet)

    def get_all_pets(self):
        """Return a list of all pets owned."""
        return list(self.pets)

    def get_all_tasks(self, completed=None):
        """Collect all tasks from all pets, optionally filtering by completion."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks(completed=completed))
        return tasks

    def __repr__(self):
        return f"Owner({self.owner_id}, {self.name!r}, pets={len(self.pets)})"


class Scheduler:
    def __init__(self):
        self.owners = {}

    def add_owner(self, owner):
        """Add an owner to scheduler tracking."""
        if not isinstance(owner, Owner):
            raise TypeError("Expected Owner instance")
        self.owners[owner.owner_id] = owner

    def get_owner(self, owner_id):
        """Retrieve an owner by id."""
        return self.owners.get(owner_id)

    def add_pet_to_owner(self, owner_id, pet):
        """Attach a pet to an existing owner."""
        owner = self.get_owner(owner_id)
        if owner is None:
            raise ValueError("Owner not found")
        owner.add_pet(pet)

    def add_task_to_pet(self, owner_id, pet_id, task):
        """Add a task to a specific pet under an owner."""
        owner = self.get_owner(owner_id)
        if owner is None:
            raise ValueError("Owner not found")
        pet = next((p for p in owner.pets if p.pet_id == pet_id), None)
        if pet is None:
            raise ValueError("Pet not found")
        pet.add_task(task)

    def get_tasks_for_owner(self, owner_id, completed=None, include_unassigned=False):
        """Return all tasks for an owner, optionally filtered by completion."""
        owner = self.get_owner(owner_id)
        if owner is None:
            return []
        return owner.get_all_tasks(completed=completed)

    def get_tasks_for_pet(self, owner_id, pet_id, completed=None):
        """Return tasks for a specific pet, optionally filtered by completion."""
        owner = self.get_owner(owner_id)
        if owner is None:
            return []
        pet = next((p for p in owner.pets if p.pet_id == pet_id), None)
        if pet is None:
            return []
        return pet.get_tasks(completed=completed)

    def sort_tasks_by_time(self, tasks):
        """Return tasks sorted by scheduled time in chronological order.

        Unscheduled tasks are sorted to the end.
        Supports tasks with datetime values or HH:MM strings.

        Args:
            tasks (list[Task]): List of Task instances.

        Returns:
            list[Task]: Sorted tasks by scheduled time.
        """
        def time_key(task):
            if task.scheduled_time is None:
                return (datetime.max, task.task_id)
            if isinstance(task.scheduled_time, str):
                try:
                    parsed = datetime.strptime(task.scheduled_time, "%H:%M")
                except ValueError:
                    parsed = datetime.max
                return (parsed, task.task_id)
            return (task.scheduled_time, task.task_id)

        return sorted(tasks, key=time_key)

    def filter_tasks(self, owner_id, completed=None, pet_name=None):
        """Filter an owner's tasks by completion status and/or pet name.

        Args:
            owner_id (str): The owner's id.
            completed (bool|None): If set, only tasks with this completion state are returned.
            pet_name (str|None): If set, only tasks for this pet name are returned.

        Returns:
            list[Task]: Filtered tasks matching criteria.
        """
        owner = self.get_owner(owner_id)
        if owner is None:
            return []

        filtered = []
        for pet in owner.pets:
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                filtered.append(task)
        return filtered

    def get_tasks(self, owner_id, pet_id=None, completed=None):
        """Return filtered tasks by owner, pet, and completion status."""
        owner = self.get_owner(owner_id)
        if owner is None:
            return []

        if pet_id:
            return self.get_tasks_for_pet(owner_id, pet_id, completed=completed)

        return self.get_tasks_for_owner(owner_id, completed=completed)

    def _generate_recurring_task_id(self, pet, base_id):
        existing_ids = {t.task_id for t in pet.tasks}
        if base_id not in existing_ids:
            return base_id
        suffix = 1
        while f"{base_id}_recurring_{suffix}" in existing_ids:
            suffix += 1
        return f"{base_id}_recurring_{suffix}"

    def complete_task(self, owner_id, pet_id, task_id):
        """Complete a task and auto-create a next recurring task if needed.

        If this task is daily/weekly, a new Task instance is added for the next
        scheduled slot and returned.

        Args:
            owner_id (str): Owner ID.
            pet_id (str): Pet ID.
            task_id (str): Task ID to complete.

        Returns:
            Task: The completed task (one-time) or the newly created next recurring task.
        """
        owner = self.get_owner(owner_id)
        if owner is None:
            raise ValueError("Owner not found")
        pet = next((p for p in owner.pets if p.pet_id == pet_id), None)
        if pet is None:
            raise ValueError("Pet not found")

        task = next((t for t in pet.tasks if t.task_id == task_id), None)
        if task is None:
            raise ValueError("Task not found")

        task.mark_completed()
        if task.frequency in ("daily", "weekly"):
            next_time = task.get_next_occurrence()
            if next_time:
                new_task_id = self._generate_recurring_task_id(pet, task.task_id)
                new_task = Task(
                    task_id=new_task_id,
                    description=task.description,
                    scheduled_time=next_time,
                    frequency=task.frequency,
                    completed=False,
                )
                pet.add_task(new_task)
                return new_task
        return task

    def detect_conflicts(self, owner_id, pet_id=None):
        """Return groups of tasks that conflict by exact scheduled datetime."""
        tasks = self.get_tasks(owner_id, pet_id=pet_id, completed=False)
        conflicts = {}
        for task in tasks:
            if task.scheduled_time is None:
                continue
            conflicts.setdefault(task.scheduled_time, []).append(task)
        return [group for group in conflicts.values() if len(group) > 1]

    def detect_conflicts_messages(self, owner_id):
        """Return lightweight warning strings for conflicts by scheduled time.

        This method does not raise errors. It returns warnings describing
        tasks that share the same scheduled timestamp across the owner's pets.

        Args:
            owner_id (str): Owner identifier.

        Returns:
            list[str]: Warning lines for each conflicting time slot.
        """
        owner = self.get_owner(owner_id)
        if owner is None:
            return []

        seen = {}
        warnings = []
        for pet in owner.pets:
            for task in pet.tasks:
                if task.scheduled_time is None:
                    continue
                key = task.scheduled_time
                if key not in seen:
                    seen[key] = []
                seen[key].append((pet, task))

        for scheduled_time, entries in seen.items():
            if len(entries) > 1:
                time_str = scheduled_time.strftime("%Y-%m-%d %H:%M") if isinstance(scheduled_time, datetime) else str(scheduled_time)
                tasks_desc = ", ".join([f"{pet.name}:{task.description}" for pet, task in entries])
                warnings.append(f"Warning: conflict at {time_str} for tasks [{tasks_desc}].")

        return warnings

    def get_due_tasks(self, before_time=None):
        """Return tasks due before the given time (or now)."""
        now = datetime.now()
        deadline = before_time or now
        due = []
        for owner in self.owners.values():
            for pet in owner.pets:
                for task in pet.tasks:
                    if task.scheduled_time and task.scheduled_time <= deadline and not task.completed:
                        due.append((owner, pet, task))
        return due

    def organize_tasks_by_pet(self):
        """Return tasks grouped by owner and pet identifiers."""
        grouped = {}
        for owner in self.owners.values():
            for pet in owner.pets:
                grouped[(owner.owner_id, pet.pet_id)] = list(pet.tasks)
        return grouped

    def __repr__(self):
        return f"Scheduler(owners={len(self.owners)})"
