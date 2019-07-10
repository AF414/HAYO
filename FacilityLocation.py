# Resources:
# https://scipbook.readthedocs.io/en/latest/flp.html#cflp-sol
# https://developers.google.com/optimization/assignment/assignment_cp
# 
import time
import json
import requests
from ortools.linear_solver import pywraplp
import configparser
import os
import pickle

# Account and API info
config = configparser.ConfigParser()
config.read("HERE_config.txt")

app_id = config['DEFAULT']["app_id"]
app_code = config['DEFAULT']["app_code"]


def main():
    here_api = "https://tce.api.here.com/2/calculateroute.json?app_id=" + app_id + "&app_code=" + app_code

    with open("cities.json", "r") as read_file:
        city_data = json.load(read_file)

    fac_number = [0, 1, 2, 3, 4]
    cus_number = [25, 26, 27, 28, 29, 30, 31, 32]

    cached_file_name = 'cached_cost_'+str(fac_number).replace(",", "_")+str(cus_number).replace(",", "_")+'.pickle'
    cost = []

    if not os.path.exists(cached_file_name):
        for fac in fac_number:
            fact = []
            for cus in cus_number:
                print(city_data[fac]['city'], city_data[fac]['latitude'], city_data[fac]['longitude'])
                print(city_data[cus]['city'], city_data[cus]['latitude'], city_data[cus]['longitude'])
                cost_opt = ""  # &cost_optimize=1

                request_string = here_api + "&waypoint0=" + str(city_data[fac]['latitude']) + "," + str(
                    city_data[fac]['longitude']) + "&waypoint1=" + str(city_data[cus]['latitude']) + "," + str(
                    city_data[cus]['longitude']) + "&mode=fastest;car" + cost_opt
                r = requests.get(request_string)

                print(r.status_code)
                # print(r.text)
                here_data = r.json()
                try:
                    here_cost = float(here_data['costs']['totalCost'])
                except:
                    here_cost = "NA"
                fact.append(here_cost)
            cost.append(fact)
            print(fact)

        with open(cached_file_name, 'wb') as cost_file:
            pickle.dump(cost, cost_file)

    else:
        with open(cached_file_name, 'r') as cost_file:
            cost = pickle.load(cost_file)

    print(cost)

    solver = pywraplp.Solver('SolveAssignmentProblem',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    start = time.time()

    task_sizes = [10, 7, 3, 12, 15, 4, 11, 5]

    # Maximum total of task sizes for any worker
    total_size_max = [100, 15, 15, 15, 100]
    num_workers = len(cost)
    num_tasks = len(cost[1])
    # Variables
    x = {}

    for i in range(num_workers):
        for j in range(num_tasks):
            x[i, j] = solver.IntVar(0, 1, 'x[%i,%i]' % (i, j))

    # Constraints
    # The total size of the tasks each worker takes on is at most total_size_max.

    for i in range(num_workers):
        solver.Add(solver.Sum([task_sizes[j] * x[i, j] for j in range(num_tasks)]) <= total_size_max[i])

    # Each task is assigned to at least one worker.

    for j in range(num_tasks):
        solver.Add(solver.Sum([x[i, j] for i in range(num_workers)]) >= 1)

    solver.Minimize(solver.Sum([cost[i][j] * x[i, j] for i in range(num_workers)
                                for j in range(num_tasks)]))
    sol = solver.Solve()

    print('Minimum cost = ', solver.Objective().Value())
    print()
    for i in range(num_workers):
        for j in range(num_tasks):
            if x[i, j].solution_value() > 0:
                print('Worker', i, ' assigned to task', j, '  Cost = ', cost[i][j])
    print()
    end = time.time()
    print("Time = ", round(end - start, 4), "seconds")


if __name__ == '__main__':
    main()
