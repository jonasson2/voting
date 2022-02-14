import multiprocessing as mp
from secrets import token_urlsafe
from time import time

def worker(queue):
    pars = queue.get()
    (function, data, askQ, ansQ, resQ) = pars
    function(data, askQ, ansQ, resQ)

class Workers:
    def __init__(self, nproc):
        mp.set_start_method('spawn')
        self.manager = mp.Manager()
        self.nproc = nproc
        self.inputQueue = self.manager.Queue()
        self.askQ = self.manager.Queue()
        self.ansQ = self.manager.Queue()
        self.resQ = self.manager.Queue()
        self.task_count = {}
        self.check_time = {}
        for k in range(self.nproc):
            p = mp.Process(target = worker, args=(self.inputQueue,))
            p.start()

    def start_task(self, function, data):
        queues = (self.askQ, self.ansQ, self.resQ)
        self.inputQueue.put((function, data, *queues))

    def check(self):
        self.check_time = time()
        for i in range(self.nproc):
            self.askQ.put('check')
        progress_list = [self.ansQ.get() for i in range(self.nproc)]
        return sum(progress_list)

    def stop(self):
        # Stop all tasks
        for i in range(self.nproc):
            self.askQ.put('stop')
        return sum(self.ansQ.get() for i in range(self.nproc))

    def result(self):
        result = self.resQ.get()
        return result
