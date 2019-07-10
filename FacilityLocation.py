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
    vehicle_cost = 11
    driver_cost = 17

    cached_file_name = 'cached_cost_'+str(fac_number).replace(",", "_")+str(cus_number).replace(",", "_") + \
                       str(vehicle_cost)+str(driver_cost)+'.pickle'
    cost = []

    if not os.path.exists(cached_file_name):
        for fac in fac_number:
            fact = []
            for cus in cus_number:
                print(city_data[fac]['city'], city_data[fac]['latitude'], city_data[fac]['longitude'])
                print(city_data[cus]['city'], city_data[cus]['latitude'], city_data[cus]['longitude'])

                cost_opt = "&cost_optimize=1"

                request_string = here_api + \
                    "&waypoint0=" + str(city_data[fac]['latitude']) + "," + \
                    str(city_data[fac]['longitude']) + \
                    "&waypoint1=" + str(city_data[cus]['latitude']) + "," + \
                    str(city_data[cus]['longitude']) + \
                    "&mode=fastest;car" + \
                    cost_opt + \
                    "driver_cost=" + str(driver_cost) + \
                    "vehicle_cost=" + str(vehicle_cost)
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
        with open(cached_file_name, 'rb') as cost_file:
            cost = pickle.load(cost_file)

    for row in cost:
        print(row)

    solver = pywraplp.Solver('SolveAssignmentProblem',
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    start = time.time()

    delivery_sizes = [10, 7, 3, 12, 15, 4, 11, 5]

    # Maximum total of delivery sizes for any factory
    total_size_max = [1000, 10005, 10001, 10005, 10005]
    num_facilities = len(cost)
    num_customers = len(cost[1])
    # Variables
    x = {}

    for i in range(num_facilities):
        for j in range(num_customers):
            x[i, j] = solver.IntVar(0, 1, 'x[%i,%i]' % (i, j))

    # Constraints
    # The total size of the deliveries each facility takes on is at most total_size_max.

    for i in range(num_facilities):
        solver.Add(solver.Sum([delivery_sizes[j] * x[i, j] for j in range(num_customers)]) <= total_size_max[i])

    # Each customer is assigned to at least one factory.

    for j in range(num_customers):
        solver.Add(solver.Sum([x[i, j] for i in range(num_facilities)]) >= 1)

    solver.Minimize(solver.Sum([cost[i][j] * x[i, j] for i in range(num_facilities)
                                for j in range(num_customers)]))
    sol = solver.Solve()

    print('Minimum cost = ', solver.Objective().Value())
    print()
    for i in range(num_facilities):
        for j in range(num_customers):
            if x[i, j].solution_value() > 0:
                print('Factory', i, city_data[fac_number[i]]['city'], 'deliver to', j, city_data[cus_number[j]]['city'], ' Cost = ', cost[i][j], sep="  |   ")
    print()
    end = time.time()
    print("Time = ", round(end - start, 4), "seconds")


if __name__ == '__main__':
    main()
