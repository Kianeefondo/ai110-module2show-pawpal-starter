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

        selected_pet_name = None
        if selected_pet_filter:
            selected_pet_name = next(p for p in st.session_state.owner.pets if p.pet_id == selected_pet_filter).name

        tasks = []
        for pet in st.session_state.owner.pets:
            if selected_pet_name and pet.name != selected_pet_name:
                continue
            tasks.extend([{"pet": pet.name, "task": task} for task in pet.get_tasks(completed=status_filter)])

        if not tasks:
            st.info("No tasks found with your selected filters.")
        else:
            sorted_tasks = st.session_state.scheduler.sort_tasks_by_time([item["task"] for item in tasks])
            task_to_pet = {item["task"].task_id: item["pet"] for item in tasks}
            table_data = []
            for task in sorted_tasks:
                table_data.append(
                    {
                        "Pet": task_to_pet.get(task.task_id, "Unknown"),
                        "Task": task.description,
                        "Scheduled": task.scheduled_time.strftime("%Y-%m-%d %H:%M") if task.scheduled_time else "No schedule",
                        "Frequency": task.frequency,
                        "Completed": "Yes" if task.completed else "No",
                    }
                )

            st.success("Schedule generated with sorted tasks")
            st.table(table_data)

            warnings = st.session_state.scheduler.detect_conflicts_messages(st.session_state.owner.owner_id)
            if warnings:
                st.warning("⚠️ Scheduling conflicts found")
                for warning in warnings:
                    st.warning(warning)
            else:
                st.success("No conflicts found for selected tasks.")

    st.markdown("### Conflict detection")
    if st.button("Check conflicts"):
        warnings = st.session_state.scheduler.detect_conflicts_messages(st.session_state.owner.owner_id)
        if not warnings:
            st.success("No conflicts detected.")
        else:
            st.warning("Detected time conflicts:")
            for warning in warnings:
                st.warning(f"• {warning}")

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
