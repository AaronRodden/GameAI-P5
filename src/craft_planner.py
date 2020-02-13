import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.
#    print(rule)
    def check(state):
#        print(state[rule])
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].

        if 'Requires' in rule:
            for item, truth in rule['Requires'].items():
                if state[item] < 1:
#                    print("Require check not passed")
                    return False
        if 'Consumes' in rule:
            for item,amount in rule['Consumes'].items():
                if item not in state or state[item] < amount:

                    return False
        return True

    return check


def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        
        #I had this at bottom for a while, making it so our next state was just a copy
        # this resulted in our search going no where
        next_state = state.copy()
        
        for item, amount in rule['Produces'].items():
            if item in state:
                next_state[item] += amount
            else:
                next_state[item] = amount
        if 'Consumes' in rule:
            for item, amount in rule['Consumes'].items():
                next_state[item] = next_state[item] - amount
        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for item,amount in goal.items():
            if item not in state or state[item] < amount:
                return False
        return True
    
    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
#            print("Check passed")
            yield (r.name, r.effect(state), r.cost)


def heuristic(action, state):
    # Implement your heuristic here!
    
    #So far all this herustic does is steer us away from redundent states
    
    tools = ['bench', 'furnace', 'iron_axe', 'iron_pickaxe', 'stone_axe', 'stone_pickaxe', 'wooden_axe', 'wooden_pickaxe']
    #Don't look at tool states if we already have them
    for tool in tools:
        if state[tool] > 1:
            return float('inf')
        elif tool in action:
            return 0
    
    #Don't look at making worse tools (I think this doesent actually reduce search...)
    if state['iron_pickaxe'] > 0:
        if 'stone_pickaxe' in action or 'wooden_pickaxe' in action:
            return float('inf')
    elif state['stone_pickaxe'] > 0:
        if 'wooden_pickaxe' in action:
            return float('inf')
    #Same thing for axes
    if state['iron_axe'] > 0:
        if 'stone_axe' in action or 'wooden_axe' in action:
            return float('inf')
    elif state['stone_axe'] > 0:
        if 'wooden_axe' in action:
            return float('inf')
        
    return 0



def create_path(pred_state, pred_action, last_state):
    path = []
    while pred_action[last_state] is not None:
        path.append((last_state,pred_action[last_state]))
        last_state = pred_state[(last_state)]
    return list(reversed(path))
    

def search(graph, state, is_goal, limit, heuristic, all_recipes):

    start_time = time()
#    graph(state)
    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state

    queue = [(0,state)]
    pred = {state : None}
    pred_actions = {state : None}
    path_cost = {state : 0}
    visited_count = 1

    
    while time() - start_time < limit:
        visited_count += 1
        curr_cost, curr_state = heappop(queue)
        if is_goal(curr_state):
            print("Path found in a time of: " + str(time() - start_time), 'seconds.')
            print("Path cost: " + str(curr_cost))
            print("Number of states visited: " + str(visited_count))
            return create_path(pred,pred_actions, curr_state)

        for action, new_state, new_cost in graph(curr_state):
            pathcost =  curr_cost + new_cost
            estimate = heuristic(action, new_state)
            total_est = pathcost + estimate
            
            if new_state not in pred.keys() or pathcost < path_cost[new_state]:
                pred[new_state] = curr_state
                pred_actions[new_state] = action
                path_cost[new_state] = pathcost
                heappush(queue, (total_est, new_state))

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    # # List of items that can be in your inventory:
#    print('All items:', Crafting['Items'])
    #
#      List of items in your initial inventory with amounts:
#    print('Initial inventory:', Crafting['Initial'])
    #
    # # List of items needed to be in your inventory at the end of the plan:
#    print('Goal:',Crafting['Goal'])
    #
    # # Dict of crafting recipes (each is a dict):
#    print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']}) 
    state.update(Crafting['Initial'])

    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic, all_recipes)

    if resulting_plan:
        print("Plan length: " + str(len(resulting_plan)) + "\n")
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
