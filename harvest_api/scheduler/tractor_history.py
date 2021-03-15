import atexit, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func

from database import sessions, engines
from mappings.tractor_tables import Blade, BladeUse, Task, Job
from mappings.harvest_tables import History

# Set of filter to get rig of unused pools
pool_filters = (
    Blade.profile != "LAVIT",
    Blade.profile != "JV",
    Blade.profile != "windows10",
    Blade.profile != "TD",
    Blade.profile != "BUG",
    Blade.availdisk > 5
)

# Store the current state of the blades in a new record in the history table
def update_tractor_history():
    # Get the working blades
    blades_busy = sessions["tractor"].query(func.count(1)) \
    .filter(BladeUse.taskcount > 0) \

    # Get the free blades
    blades_free = sessions["tractor"].query(func.count(Blade.bladeid)) \
    .filter(Blade.status == "") \
    .filter(*pool_filters) \

    # Get the blades with nimby on
    blades_nimby = sessions["tractor"].query(func.count(1)) \
    .filter(Blade.status.like("nimby%") ) \
    .filter(*pool_filters) \

    # Get the blades that are off
    # TODO: find the sqlalchemy way to use the function age
    blades_off_query = engines["tractor"].execute("SELECT count(*) FROM blade where age(current_timestamp, heartbeattime) > interval '1 hours'")
    blades_off = [blades_off_result[0] for blades_off_result in blades_off_query]

    # Add the result to a new record in the history table
    new_record = History(date = datetime.datetime.now(), blade_busy = blades_busy[0][0], blade_free = blades_free[0][0], blade_nimby = blades_nimby[0][0], blade_off = blades_off[0])
    sessions["harvest"].add(new_record)
    sessions["harvest"].commit()


# Initialize the scheduler with the update_tractor_history function
tractor_history_updater = BackgroundScheduler()
# Trigger the function every 5 seconds
tractor_history_updater.add_job(func = update_tractor_history, trigger = "interval", hours = 1, id = "tractor_history")

# Shut down the scheduler when exiting the app
atexit.register(lambda: tractor_history_updater.shutdown())
