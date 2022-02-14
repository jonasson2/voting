import multiprocessing as mp
from secrets import token_urlsafe
from time import time

def worker(queue):
    for k in range(9999):
        (function, data, askQ, ansQ, resQ, id) = queue.get()
        print(f'k={k}, askQ={askQ}, id={id}')
        function(data, askQ, ansQ, resQ)

print('importing')
ids = set()
print('ids')
manager = mp.Manager()
print('after manager')
nproc = 1
inputQueue = mp.Queue()
askQs = {}
ansQs = {}
resQs = {}
task_count = {}
check_time = {}
print('defining functions')

def setup(nprocessors):
    print('setup')
    global nproc
    nproc = nprocessors
    for k in range(nproc):
        p = mp.Process(target = worker, args=(inputQueue,))
        print('starting p')
        p.start()

def start(self):
    # Create id (20 random characters) and queues for a set of tasks
    id = token_urlsafe(4)
    ids.add(id)
    askQs[id] = manager.Queue()
    ansQs[id] = manager.Queue()
    resQs[id] = manager.Queue()
    task_count[id] = 0
    return id

def start_task(function, data, id):
    # Start a single task with specified id
    print(f'starting task, id={id}')
    queues = (askQs[id], ansQs[id], resQs[id])
    inputQueue.put((function, data, *queues, id))
    task_count[id] += 1

def check(id):
    # Check progress of all tasks with specified id, sum the results
    check_time[id] = time()
    for i in range(nproc):
        askQs[id].put('check')
    progress_list = [ansQs[id].get() for i in range(nproc)]
    return sum(progress_list)

def delete_old(id, older_than):
    # Discard tasks that have not been checked for older_than seconds
    for id in ids:
        if time() - check_time[id] > older_than:
            delete(id)

def stop(id):
    # Stop all tasks with specified id
    for i in range(nproc):
        askQs[id].put('stop')
    return sum(ansQs[id].get() for i in range(nproc))

def delete(id):
    print(f'deleting task set {id}')
    del task_count[id]
    if id in check_time:
        del check_time[id]
    del askQs[id]
    del ansQs[id]
    del resQs[id]
    ids.discard(id)

def result(id):
    # Return results from a single subtask, remove id after returning last result
    print('id =', id)
    print(f'resQs[id]: {resQs[id]}')
    result = resQs[id].get()
    task_count[id] -= 1
    if task_count[id] == 0:
        pass
        #print(f'deleting id {id}')
        #delete(id)
    return result
