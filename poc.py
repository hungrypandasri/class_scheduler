import pyomo.environ as pe

# Define the problem
m = pe.ConcreteModel()

# Sample data
classes = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12']  # Classes
students = {'C1': 30, 'C2': 25, 'C3': 20, 'C4': 35, 'C5': 15, 'C6': 45, 'C7': 30, 'C8': 25, 'C9': 20, 'C10': 35, 'C11': 15, 'C12': 45}  # Number of students in each class
durations = {'C1': 2, 'C2': 1.5, 'C3': 1, 'C4': 2.5, 'C5': 0.5, 'C6': 3, 'C7': 2, 'C8': 1.5, 'C9': 1, 'C10': 2.5, 'C11': 0.5, 'C12': 3}  # Class durations in hours
classrooms = ['R1', 'R2', 'R3', 'R4']  # Classrooms
capacity = {'R1': 40, 'R2': 50, 'R3': 35, 'R4': 60}  # Capacity of each classroom
time_slots = list(range(8, 20))  # Time slots from 8:00 AM to 8:00 PM (hourly)

m.x = pe.Var(classes, classrooms, time_slots, within=pe.Binary)  # Binary variable: 1 if class is assigned, 0 otherwise

# Objective: Minimize the unused capacity
def objective_function(model):
    return sum((capacity[j] - students[i]) * model.x[i, j, k]
               for i in classes for j in classrooms for k in time_slots)
m.obj = pe.Objective(rule=objective_function, sense=pe.minimize)

def class_assignment_constraint(model, i):
    return sum(model.x[i, j, k] for j in classrooms for k in time_slots) == 1
m.class_assignment_constraint = pe.Constraint(classes, rule=class_assignment_constraint)

def classroom_time_constraint(model, j, k):
    return sum(model.x[i, j, t] for i in classes for t in range(k, k + int(durations[i])) if k + int(durations[i]) <= 20) <= 1
m.classroom_time_constraint = pe.Constraint(classrooms, time_slots, rule=classroom_time_constraint)

def capacity_constraint(model, i, j, k):
    return students[i] * model.x[i, j, k] <= capacity[j]
m.capacity_constraint = pe.Constraint(classes, classrooms, time_slots, rule=capacity_constraint)


def time_limit_constraint(model, i, k):
    # Ensure the class starts within valid time slots (8 AM to 8 PM)
    if k + int(durations[i]) <= 20:  # Class must end before or exactly at 8 PM
        return pe.Constraint.Feasible
    else:
        return pe.Constraint.Skip  # Skip if this would lead to a trivial constraint

m.time_limit_constraint = pe.Constraint(classes, time_slots, rule=time_limit_constraint)


def precedence_constraint(model, j, k):
    if k > 8:  # Apply precedence only after the first time slot
        return sum(model.x[i, j, k] for i in classes) <= sum(model.x[i, j, k-1] for i in classes)
    return pe.Constraint.Skip
m.precedence_constraint = pe.Constraint(classrooms, time_slots, rule=precedence_constraint)

m.x['C8','R3',13].fix(1)

# Solve the model
solver = pe.SolverFactory('gurobi')  # You can use 'cbc', 'gurobi' or other solvers as well
solver.solve(m)
m.display()

# Output the results
for i in classes:
    for j in classrooms:
        for k in time_slots:
            if m.x[i, j, k].value == 1:
                print(f"Class {i} is assigned to classroom {j} at time slot {k}:00")

