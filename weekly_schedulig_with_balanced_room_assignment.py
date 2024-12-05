from pyomo.environ import *
from pyomo.opt import SolverFactory

# Input data
classes = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12']  # Classes
students = {'C1': 40, 'C2': 25, 'C3': 20, 'C4': 35, 'C5': 15, 'C6': 30, 'C7': 30, 'C8': 25, 'C9': 20, 'C10': 35,
            'C11': 15, 'C12': 45}  # class strength
durations = {'C1': 6, 'C2': 2, 'C3': 1, 'C4': 2, 'C5': 1, 'C6': 3, 'C7': 2, 'C8': 1, 'C9': 3, 'C10': 3, 'C11': 3,
             'C12': 3}  # class duration in hours
classrooms = ['R1','R2','R3', 'R4', 'R5', 'R6', 'R7']  # rooms
capacity = {'R1': 45, 'R2': 50, 'R3': 35, 'R4': 60, 'R5': 30, 'R6': 45, 'R7': 60}  # Room capacities

days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']  # days in the week where classes can be placed

# Class schedule
class_days = {
    'C1': ['Monday', 'Wednesday', 'Friday'],
    'C2': ['Monday','Tuesday'],
    'C3': ['Monday','Thursday'],
    'C4': ['Monday', 'Wednesday'],
    'C5': ['Monday','Friday'],
    'C6': ['Monday','Tuesday', 'Thursday'],
    'C7': ['Monday', 'Friday'],
    'C8': ['Monday','Tuesday'],
    'C9': ['Monday','Wednesday'],
    'C10': ['Monday','Thursday', 'Friday'],
    'C11': ['Monday'],
    'C12': ['Monday','Wednesday', 'Friday']
}

# Time slots (8 AM to 8 PM is 12 hours, so we use time slots 8-20)
time_slots = range(8, 20)

# Create a model
model = ConcreteModel()

# New: Variables: x[c, r, t, d] = 1 if class c is scheduled in room r starting at time t on day d
model.x = Var(classes, classrooms, time_slots, days, domain=Binary)

# New: Variable for tracking classroom usage
model.room_usage = Var(classrooms, domain=NonNegativeIntegers)

# Constraint 1: Each class must be assigned to its specified days, one room and one start time per day
def class_assignment_rule(model, c, d):
    if d in class_days[c]:
        return sum(model.x[c, r, t, d] for r in classrooms for t in time_slots) == 1
    else:
        return sum(model.x[c, r, t, d] for r in classrooms for t in time_slots) == 0
model.class_assignment = Constraint(classes, days, rule=class_assignment_rule)

# Constraint 2: Room capacity must be enough for the students in each class
def room_capacity_rule(model, c, r, t, d):
    return model.x[c, r, t, d] * students[c] <= capacity[r]
model.room_capacity = Constraint(classes, classrooms, time_slots, days, rule=room_capacity_rule)

# Constraint 3: No overlapping classes in the same room on the same day
def no_overlap_rule(model, r, t, d):
    return sum(model.x[c, r, t_prime, d]
               for c in classes
               for t_prime in range(max(t - durations[c] + 1, 8), t + 1) if t_prime < 20) <= 1
model.no_overlap = Constraint(classrooms, time_slots, days, rule=no_overlap_rule)

# Constraint 4: Classes can only start between 8 AM and 8 PM, allowing time for the duration
def valid_start_time_rule(model, c, r, t, d):
    return model.x[c, r, t, d] == 0 if t + durations[c] > 20 else Constraint.Skip
model.valid_start_time = Constraint(classes, classrooms, time_slots, days, rule=valid_start_time_rule)

# New: Constraint to calculate the number of classes assigned to each room
def room_usage_rule(model, r):
    return model.room_usage[r] == sum(model.x[c, r, t, d] for c in classes for t in time_slots for d in days)
model.room_usage_constraint = Constraint(classrooms, rule=room_usage_rule)

# Objective: Minimize the variance in classroom usage
def balance_classroom_usage_objective(model):
    mean_usage = sum(model.room_usage[r] for r in classrooms) / len(classrooms)
    return sum((model.room_usage[r] - mean_usage)**2 for r in classrooms)

# Minimize sense for the objective function
model.obj = Objective(rule=balance_classroom_usage_objective, sense=minimize)

# Solve using Gurobi
opt = SolverFactory('gurobi')
results = opt.solve(model, tee=True)

# Check solver status for infeasibility
if (results.solver.termination_condition == TerminationCondition.optimal or
    results.solver.termination_condition == TerminationCondition.feasible):
    # If a feasible solution is found, print the schedule
    for c in classes:
        for d in days:
            for r in classrooms:
                for t in time_slots:
                    if model.x[c, r, t, d].value == 1:
                        print(f"Class {c} is scheduled in Room {r} on {d} starting at {t}:00 for {durations[c]} hours")
else:
    # Handle infeasibility
    if results.solver.termination_condition == TerminationCondition.infeasible:
        print("No feasible solution found: The current problem constraints are too restrictive.")
        # Optionally, include potential reasons
        total_class_duration = sum(durations[c] * len(class_days[c]) for c in classes)
        total_available_time_slots = len(classrooms) * len(time_slots) * len(days)
        if total_class_duration > total_available_time_slots:
            print(f"Reason: The total required class time ({total_class_duration} hours) exceeds available time slots ({total_available_time_slots} hours).")
        else:
            print("Reason: Check if room capacities or time constraints are too tight.")
    else:
        print(f"Solver did not return a feasible solution. Termination condition: {results.solver.termination_condition}")