from datetime import datetime, timedelta
from pawpal_system import Pet, Task, Owner, Scheduler


def test_mark_completed_updates_completion_status():
    task = Task(task_id="t1", description="Feed Buddy")
    assert task.completed is False

    task.mark_completed()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(pet_id="p1", name="Buddy", species="Dog")
    initial_count = len(pet.tasks)
    task = Task(task_id="t2", description="Walk Buddy")

    pet.add_task(task)

    assert len(pet.tasks) == initial_count + 1
    assert pet.tasks[0] is task


def test_scheduler_sort_and_conflict_detection():
    owner = Owner(owner_id="o1", name="Alice", contact_info="a")
    pet = Pet(pet_id="p1", name="Buddy", species="Dog")
    owner.add_pet(pet)
    scheduler = Scheduler()
    scheduler.add_owner(owner)

    now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    t1 = Task(task_id="t1", description="Feed", scheduled_time=now)
    t2 = Task(task_id="t2", description="Walk", scheduled_time=now + timedelta(hours=1))
    t3 = Task(task_id="t3", description="Vet", scheduled_time=now)
    pet.add_task(t1)
    pet.add_task(t2)
    pet.add_task(t3)

    sorted_tasks = scheduler.sort_tasks_by_time([t2, t3, t1])
    assert sorted_tasks == [t1, t3, t2]

    conflicts = scheduler.detect_conflicts("o1")
    assert len(conflicts) == 1
    assert set([task.task_id for task in conflicts[0]]) == {"t1", "t3"}


def test_scheduler_recurring_reschedule():
    owner = Owner(owner_id="o2", name="Jordan", contact_info="j")
    pet = Pet(pet_id="p2", name="Mittens", species="Cat")
    owner.add_pet(pet)
    scheduler = Scheduler()
    scheduler.add_owner(owner)

    date = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
    task = Task(task_id="t4", description="Feed", scheduled_time=date, frequency="daily")
    pet.add_task(task)

    next_task = scheduler.complete_task("o2", "p2", "t4")
    assert next_task is not task
    assert next_task.completed is False
    assert next_task.scheduled_time == date + timedelta(days=1)
    assert task.completed is True


def test_scheduler_complete_task_creates_next_recurring_instance():
    owner = Owner(owner_id="o4", name="Terry", contact_info="t")
    pet = Pet(pet_id="p4", name="Rex", species="Dog")
    owner.add_pet(pet)
    scheduler = Scheduler()
    scheduler.add_owner(owner)

    now = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    task = Task(task_id="t10", description="Walk", scheduled_time=now, frequency="daily")
    pet.add_task(task)

    new_task = scheduler.complete_task("o4", "p4", "t10")
    assert task.completed is True
    assert new_task is not task
    assert new_task.frequency == "daily"
    assert new_task.scheduled_time == now + timedelta(days=1)


def test_scheduler_complete_task_nonrecurring_returns_same_task():
    owner = Owner(owner_id="o5", name="Sam", contact_info="a")
    pet = Pet(pet_id="p5", name="Luna", species="Cat")
    owner.add_pet(pet)
    scheduler = Scheduler()
    scheduler.add_owner(owner)

    now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    task = Task(task_id="t11", description="Groom", scheduled_time=now, frequency="once")
    pet.add_task(task)

    returned = scheduler.complete_task("o5", "p5", "t11")
    assert returned is task
    assert returned.completed is True


def test_scheduler_filter_tasks_by_completed_and_pet_name():
    owner = Owner(owner_id="o3", name="Sam", contact_info="sam@example.com")
    pet1 = Pet(pet_id="p1", name="Buddy", species="Dog")
    pet2 = Pet(pet_id="p2", name="Mittens", species="Cat")
    owner.add_pet(pet1)
    owner.add_pet(pet2)
    scheduler = Scheduler()
    scheduler.add_owner(owner)

    t1 = Task(task_id="t1", description="Feed", scheduled_time=datetime.now(), completed=False)
    t2 = Task(task_id="t2", description="Walk", scheduled_time=datetime.now(), completed=True)
    t3 = Task(task_id="t3", description="Groom", scheduled_time=datetime.now(), completed=False)
    pet1.add_task(t1)
    pet1.add_task(t2)
    pet2.add_task(t3)

    not_done = scheduler.filter_tasks("o3", completed=False)
    assert set(t.task_id for t in not_done) == {"t1", "t3"}

    mittens_tasks = scheduler.filter_tasks("o3", pet_name="Mittens")
    assert len(mittens_tasks) == 1
    assert mittens_tasks[0].task_id == "t3"


def test_sort_tasks_by_time_hhmm_string():
    scheduler = Scheduler()
    a = Task(task_id="a", description="A", scheduled_time="18:00")
    b = Task(task_id="b", description="B", scheduled_time="08:00")
    c = Task(task_id="c", description="C", scheduled_time="12:30")

    sorted_tasks = scheduler.sort_tasks_by_time([a, b, c])
    assert [t.task_id for t in sorted_tasks] == ["b", "c", "a"]
