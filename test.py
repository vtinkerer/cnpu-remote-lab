import sys 
import select 
import time 
while True: 
    user_inputs = [] 
    while True: 
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]: 
            try: user_inputs.append(input()) 
            except EOFError: 
                break 
        else: break 
    print("You entered:", user_inputs) 
    print("Performing other tasks...") 
    time.sleep(3)