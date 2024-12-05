from pyomo.environ import *
from pyomo.opt import SolverFactory

# Input data
classes = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12']  # Classes
students = {'C1': 30, 'C2': 25, 'C3': 20, 'C4': 35, 'C5': 15, 'C6': 45, 'C7': 30, 'C8': 25, 'C9': 20, 'C10': 35, 'C11': 15, 'C12': 45}  # class strength
durations = {'C1': 1, 'C2': 1, 'C3': 1, 'C4': 2, 'C5': 1, 'C6': 3, 'C7': 2, 'C8': 1, 'C9': 1, 'C10': 2, 'C11': 1, 'C12': 3}  # class duration in hours
classrooms = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']  # rooms
capacity = {'R1': 40, 'R2': 50, 'R3': 35, 'R4': 60, 'R5': 30, 'R6': 45, 'R7': 60}  # Room capacities
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] # days in the week where classes can be placed

# Class schedule
class_days = {
    'C1': ['Monday', 'Wednesday', 'Friday'],
    'C2': ['Tuesday'],
    'C3': ['Thursday'],
    'C4': ['Monday', 'Wednesday'],
    'C5': ['Friday'],
    'C6': ['Tuesday', 'Thursday'],
    'C7': ['Monday', 'Friday'],
    'C8': ['Tuesday'],
    'C9': ['Wednesday'],
    'C10': ['Thursday', 'Friday'],
    'C11': ['Monday'],
    'C12': ['Wednesday', 'Friday']
}

# Time slots (8 AM to 8 PM is 12 hours, so we use time slots 8-20)
time_slots = range(8, 20)

# Create a model
model = ConcreteModel()

# Variables: x[c, r, t, d] = 1 if class c is scheduled in room r starting at time t on day d
model.x = Var(classes, classrooms, time_slots, days, domain=Binary)

# Constraint 1: Each class must be assigned to its specified days, one room and one start time per day
def class_assignment_rule(model, c, d):
    if d in class_days[c]:
        return sum(model.x[c, r, t, d] for r in classrooms for t in time_slots) == 1
    else:
        return sum(model.x[c, r, t, d] for r in classrooms for t in time_slots) == 0  # No assignment if not scheduled for that day
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

# Objective: Maximize the number of classes scheduled
def maximize_classes_scheduled(model):
    return sum(model.x[c, r, t, d]
               for c in classes for r in classrooms for t in time_slots for d in days)
model.obj = Objective(rule=maximize_classes_scheduled, sense=maximize)

# Solve using Gurobi
opt = SolverFactory('gurobi')
results = opt.solve(model, tee=True)

# Output the weekly schedule
print("Class Schedule:")
for c in classes:
    for d in days:
        for r in classrooms:
            for t in time_slots:
                if model.x[c, r, t, d].value == 1:
                    print(f"Class {c} is scheduled in Room {r} on {d} starting at {t}:00 for {durations[c]} hours")

# Count and print the number of time slots used
used_time_slots = set()  # A set to track used time slots
for r in classrooms:
    for t in time_slots:
        for d in days:
            for c in classes:
                if model.x[c, r, t, d].value == 1:
                    used_time_slots.add(t)  # Add time slot t to the set if it's used

# Print the number of distinct time slots used
print(f"\nTotal distinct time slots used: {len(used_time_slots)}")
