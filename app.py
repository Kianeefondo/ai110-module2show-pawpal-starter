import streamlit as st
from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ interactive app.

This app now hooks into your backend classes so you can add pets and tasks and generate a basic schedule.
"""
)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

if "owner" not in st.session_state:
    st.session_state.owner = None

st.subheader("Owner & Pets")
owner_name = st.text_input("Owner name", value="Jordan")
contact_info = st.text_input("Contact info", value="jordan@example.com")

if st.button("Create owner"):
    st.session_state.owner = Owner("o1", owner_name, contact_info)
    st.session_state.scheduler.add_owner(st.session_state.owner)
    st.success(f"Owner created: {owner_name}")

if st.session_state.owner:
    st.write(f"**Current owner:** {st.session_state.owner.name} ({st.session_state.owner.contact_info})")

    st.markdown("### Add a pet")
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.button("Add pet"):
        pet_id = f"pet{len(st.session_state.owner.pets) + 1}"
        pet = Pet(pet_id=pet_id, name=pet_name, species=species)
        st.session_state.owner.add_pet(pet)
        st.success(f"Added pet {pet_name}")

    if st.session_state.owner.pets:
        st.write("**Pets:**")
        for pet in st.session_state.owner.pets:
            st.write(f"- {pet.name} ({pet.species})")

    st.markdown("### Add a task")
    if st.session_state.owner.pets:
        selected_pet_id = st.selectbox(
            "Select pet for task",
            options=[pet.pet_id for pet in st.session_state.owner.pets],
            format_func=lambda pid: next(p for p in st.session_state.owner.pets if p.pet_id == pid).name,
        )
        task_desc = st.text_input("Task description", value="Feed your pet")
        scheduled_time = st.time_input("Scheduled time", value=datetime.now().time())
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=0)
        if st.button("Add task"):
            pet = next(p for p in st.session_state.owner.pets if p.pet_id == selected_pet_id)
            task_id = f"task{sum(len(p.tasks) for p in st.session_state.owner.pets) + 1}"
            task = Task(task_id=task_id, description=task_desc, scheduled_time=datetime.combine(datetime.now().date(), scheduled_time), frequency=frequency)
            pet.add_task(task)
            st.success(f"Added task to {pet.name}: {task_desc}")

        st.markdown("**Pet tasks:**")
        for pet in st.session_state.owner.pets:
            st.write(f"- {pet.name}: {len(pet.tasks)} tasks")
    else:
        st.info("Add a pet first before adding tasks.")

    st.markdown("### Generate schedule")
    selected_pet_filter = st.selectbox(
        "Filter by pet",
        options=[None] + [pet.pet_id for pet in st.session_state.owner.pets],
        format_func=lambda pid: "All pets" if pid is None else next(p for p in st.session_state.owner.pets if p.pet_id == pid).name,
    )
    completed_filter = st.selectbox("Show tasks", options=[None, "incomplete", "complete"])

    if st.button("Generate schedule"):
        status_filter = None
        if completed_filter == "complete":
            status_filter = True
        elif completed_filter == "incomplete":
            status_filter = False

        tasks = []
        if selected_pet_filter:
            tasks = st.session_state.scheduler.get_tasks(st.session_state.owner.owner_id, pet_id=selected_pet_filter, completed=status_filter)
            tasks = [(next(p for p in st.session_state.owner.pets if p.pet_id == selected_pet_filter).name, t) for t in tasks]
        else:
            for pet in st.session_state.owner.pets:
                filtered = st.session_state.scheduler.get_tasks(st.session_state.owner.owner_id, pet_id=pet.pet_id, completed=status_filter)
                tasks.extend([(pet.name, t) for t in filtered])

        tasks = sorted(tasks, key=lambda e: e[1].scheduled_time or datetime.max)

        if not tasks:
            st.info("No tasks to schedule with current filters.")
        else:
            st.write("#### Planned tasks (sorted by time)")
            for pet_name, task in tasks:
                due = task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "No time"
                st.write(f"- {pet_name}: {task.description} at {due} ({task.frequency})")

    st.markdown("### Conflict detection")
    if st.button("Check conflicts"):
        conflicts = st.session_state.scheduler.detect_conflicts(st.session_state.owner.owner_id)
        if not conflicts:
            st.success("No conflicts detected.")
        else:
            st.warning("Detected time conflicts:")
            for group in conflicts:
                group_text = ", ".join([f"{t.description} (at {t.scheduled_time.strftime('%H:%M')})" for t in group])
                st.write(f"- {group_text}")

    st.markdown("### Recurring tasks processing")
    if st.button("Process recurring completed tasks"):
        processed_tasks = []
        for pet in st.session_state.owner.pets:
            for task in pet.tasks:
                if task.completed and task.frequency in ["daily", "weekly"]:
                    if task.complete_and_reschedule():
                        processed_tasks.append(task)
        if not processed_tasks:
            st.info("No recurring completed tasks to reschedule.")
        else:
            st.success(f"Rescheduled {len(processed_tasks)} recurring tasks.")

else:
    st.info("Create an owner to start adding pets and tasks.")
