from datetime import datetime
from pawpal_system import Scheduler, Owner, Pet, Task

scheduler = Scheduler()
owner = Owner(owner_id="o1", name="Alice", contact_info="alice@example.com")
scheduler.add_owner(owner)

pet1 = Pet("p1", "Buddy", "Dog")
pet2 = Pet("p2", "Mittens", "Cat")
owner.add_pet(pet1)
owner.add_pet(pet2)

now = datetime.now().replace(second=0, microsecond=0)

# Add tasks out of order
pet1.add_task(Task("t1", "Feed Buddy", scheduled_time=now.replace(hour=18, minute=0)))
pet1.add_task(Task("t2", "Walk Buddy", scheduled_time=now.replace(hour=8, minute=0)))
pet1.add_task(Task("t3", "Play Buddy", scheduled_time=now.replace(hour=12, minute=0)))

pet2.add_task(Task("t4", "Feed Mittens", scheduled_time=now.replace(hour=9, minute=0), completed=True))
pet2.add_task(Task("t5", "Groom Mittens", scheduled_time=now.replace(hour=14, minute=0)))
pet2.add_task(Task("t6", "Cuddle Mittens"))  # unscheduled

# Add a conflict example: two tasks at same time for different pets
conflict_time = now.replace(hour=10, minute=0)
pet1.add_task(Task("t7", "Brush Buddy", scheduled_time=conflict_time))
pet2.add_task(Task("t8", "Trim Mittens", scheduled_time=conflict_time))

all_tasks = owner.get_all_tasks()
print("All tasks in insertion order:")
for t in all_tasks:
    print(f"- {t.task_id}: {t.description}, {t.scheduled_time or 'unscheduled'}, completed={t.completed}")

sorted_tasks = scheduler.sort_tasks_by_time(all_tasks)
print("\nSorted by scheduled time:")
for t in sorted_tasks:
    time_str = t.scheduled_time.strftime('%H:%M') if t.scheduled_time else 'unscheduled'
    print(f"- {t.task_id}: {t.description} at {time_str}")

filtered_tasks = scheduler.filter_tasks(owner.owner_id, completed=False)
print("\nFiltered (not completed):")
for t in filtered_tasks:
    print(f"- {t.task_id}: {t.description}, completed={t.completed}")

filtered_by_pet = scheduler.filter_tasks(owner.owner_id, pet_name="Mittens")
print("\nFiltered by pet Mittens:")
for t in filtered_by_pet:
    time_str = t.scheduled_time.strftime('%H:%M') if t.scheduled_time else 'unscheduled'
    print(f"- {t.task_id}: {t.description} at {time_str}, completed={t.completed}")

conflicts = scheduler.detect_conflicts(owner.owner_id)
print(f"\nConflict groups found: {len(conflicts)}")
for group in conflicts:
    print("Conflict:")
    for t in group:
        print(f" - {t.task_id} {t.description} at {t.scheduled_time}")
