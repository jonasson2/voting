import multiprocessing as mp
from secrets import token_urlsafe
from time import time

def worker(queue):
    for k in range(9999):
        (function, data, askQ, ansQ, resQ, id) = queue.get()
        print(f'k={k}, askQ={askQ}, id={id}')
        function(data, askQ, ansQ, resQ)

class Workers:
    def __init__(self, nproc):
        mp.set_start_method('spawn')
        self.ids = set()
        self.manager = mp.Manager()
        self.nproc = nproc
        self.inputQueue = mp.Queue()
        self.askQs = {}
        self.ansQs = {}
        self.resQs = {}
        self.task_count = {}
        self.check_time = {}
        for k in range(self.nproc):
            p = mp.Process(target = worker, args=(self.inputQueue,))
            p.start()
    
    def start(self):
        # Create id (20 random characters) and queues for a set of tasks
        id = token_urlsafe(4)
        self.ids.add(id)
        self.askQs[id] = self.manager.Queue()
        self.ansQs[id] = self.manager.Queue()
        self.resQs[id] = self.manager.Queue()
        self.task_count[id] = 0
        return id

    def start_task(self, function, data, id):
        # Start a single task with specified id
        print(f'starting task, id={id}')
        queues = (self.askQs[id], self.ansQs[id], self.resQs[id])
        print('xxxxxxxxxxxxx')
        self.inputQueue.put((function, data, *queues, id))
        print('yyyyyyyyyyyyy')
        self.task_count[id] += 1

    def check(self, id):
        # Check progress of all tasks with specified id, sum the results
        self.check_time[id] = time()
        for i in range(self.nproc):
            self.askQs[id].put('check')
        progress_list = [self.ansQs[id].get() for i in range(self.nproc)]
        return sum(progress_list)

    def delete_old(self, id, older_than):
        # Discard tasks that have not been checked for older_than seconds
        for id in self.ids:
            if time() - self.check_time[id] > older_than:
                self.delete(id)
        
    def stop(self, id):
        # Stop all tasks with specified id
        for i in range(self.nproc):
            self.askQs[id].put('stop')
        return sum(self.ansQs[id].get() for i in range(self.nproc))

    def delete(self, id):
        print(f'deleting task set {id}')
        del self.task_count[id]
        if id in self.check_time:
            del self.check_time[id]
        del self.askQs[id]
        del self.ansQs[id]
        del self.resQs[id]
        self.ids.discard(id)
    
    def result(self, id):
        # Return results from a single subtask, remove id after returning last result
        print('id =', id)
        print(f'resQs[id]: {self.resQs[id]}')
        result = self.resQs[id].get()
        self.task_count[id] -= 1
        if self.task_count[id] == 0:
            pass
            #print(f'deleting id {id}')
            #self.delete(id)
        return result
