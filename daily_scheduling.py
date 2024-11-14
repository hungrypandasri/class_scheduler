from pyomo.environ import *
from pyomo.opt import SolverFactory

# Define data
classes = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12']  # Classes
students = {'C1': 30, 'C2': 25, 'C3': 20, 'C4': 35, 'C5': 15, 'C6': 45, 'C7': 30, 'C8': 25, 'C9': 20, 'C10': 35, 'C11': 15, 'C12': 45}  # Number of students in each class
durations = {'C1': 2, 'C2': 1, 'C3': 1, 'C4': 2, 'C5': 1, 'C6': 3, 'C7': 2, 'C8': 1, 'C9': 1, 'C10': 2, 'C11': 1, 'C12': 3}  # Class durations in hours
classrooms = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']  # Classrooms
capacity = {'R1': 40, 'R2': 50, 'R3': 35, 'R4': 60, 'R5': 30, 'R6': 45, 'R7': 60}

# Time slots (8 AM to 8 PM is 12 hours, so we use time slots 8-20)
time_slots = range(8, 20)

# Create a model
model = ConcreteModel()

# Variables: x[c, r, t] = 1 if class c is scheduled in room r starting at time t
model.x = Var(classes, classrooms, time_slots, domain=Binary)

# Constraint: Each class must be assigned to exactly one room and one start time
def class_assignment_rule(model, c):
    return sum(model.x[c, r, t] for r in classrooms for t in time_slots) == 1
model.class_assignment = Constraint(classes, rule=class_assignment_rule)

# Constraint: Room capacity must be enough for the students in each class
def room_capacity_rule(model, c, r, t):
    return model.x[c, r, t] * students[c] <= capacity[r]
model.room_capacity = Constraint(classes, classrooms, time_slots, rule=room_capacity_rule)

# Constraint: No overlapping classes in the same room
def no_overlap_rule(model, r, t):
    return sum(model.x[c, r, t_prime]
               for c in classes
               for t_prime in range(max(t - durations[c] + 1, 8), t + 1) if t_prime < 20) <= 1
model.no_overlap = Constraint(classrooms, time_slots, rule=no_overlap_rule)

# Constraint: Classes can only start between 8 AM and 8 PM, allowing time for the duration
def valid_start_time_rule(model, c, r, t):
    return model.x[c, r, t] == 0 if t + durations[c] > 20 else Constraint.Skip
model.valid_start_time = Constraint(classes, classrooms, time_slots, rule=valid_start_time_rule)

# Solve using Gurobi
opt = SolverFactory('gurobi')
results = opt.solve(model, tee=True)

# Output the schedule
for c in classes:
    for r in classrooms:
        for t in time_slots:
            if model.x[c, r, t].value == 1:
                print(f"Class {c} is scheduled in Room {r} starting at {t}:00 for {durations[c]} hours")
