import json, tempfile
from secrets import token_urlsafe
from pathlib import Path
from time import time
from dictionaries import CONSTANTS
from traceback import format_exc
# from util import traceback
import multiprocessing as mp
from util import disp

NTOK = CONSTANTS["simulation_id_length"]

def get_id():
    if NTOK==0:
        return 'test'
    token = token_urlsafe(NTOK)
    if all(x=='-' for x in token):
        token = 'x' * NTOK
    while token[0] == '-':
        token = token_urlsafe(NTOK)
    return token

def parallel_dir():
    pardir = Path(__file__).parents[1]/"pardir"
    pardir.mkdir(parents=True, exist_ok=True)
    return pardir

def write_json(simid, data, suffix):
    dir = parallel_dir()
    filename = dir/f'{simid}-{suffix}.json'
    with open(filename, 'w', encoding='utf-8') as fd:
        json.dump(data, fd, indent=2, ensure_ascii=False)

def read_json(simid, suffix):
    dir = parallel_dir()
    filename = dir/f'{simid}-{suffix}.json'
    try:
        with open(filename, encoding='utf-8') as fd:
            data = json.load(fd)
            return data
    except (ValueError, FileNotFoundError):
        return None

def write_sim_settings(simid, data): write_json(simid, data, 'settings')
def read_sim_settings(simid):        return read_json(simid, 'settings')

def write_sim_status(simid, status): write_json(simid, status, 'status')
def read_sim_status(simid):          return read_json(simid, 'status')

def write_sim_dict(simid, results):  write_json(simid, results, 'results')
def read_sim_dict(simid):            return read_json(simid, 'results')

def write_sim_stop(simid):           write_json(simid, {'stop':True}, 'stop')
def read_sim_stop(simid):            return read_json(simid, 'stop')

def write_sim_error(simid, message):
    dir = parallel_dir()
    filename = dir/f'{simid}-error.txt'
    with open(filename, 'w', encoding='utf-8') as fd:
        fd.write(message)

def read_sim_error(simid):
    dir = parallel_dir()
    filename = dir/f'{simid}-error.txt'
    try:
        with open(filename) as fd:
            message = fd.read()
            return message
    except (ValueError, FileNotFoundError):
        return None

def start_python_command(command, simid):
    from subprocess import Popen
    import sys
    python = sys.executable
    p = Popen([python, command, simid], start_new_session=True)
    return p

def kill_process(pid):
    import os
    import signal
    os.kill(pid, signal.SIGTERM)

def clean(simid):
    dir = parallel_dir()
    for file in dir.glob(f'{simid}*.json'):
        file.unlink(missing_ok=True)

class Monitor:
    def __init__(self, nproc):
        manager = mp.Manager()
        self.nproc = nproc
        self.queue = manager.Queue()
        self.stopQueue = manager.Queue()
        self.starttime = time()
        self.iter = [0]*nproc
        self.errortrace = [None]*nproc
        self.stopped = [False]*nproc
        self.done = False
        self.info = {}
        
    def monitor(self, tasknr, info=None):
        # called by the pool workers
        while not self.stopQueue.empty():
            stopnr = self.stopQueue.get()
            self.stopped[stopnr] = True
        self.queue.put((tasknr, info))
        return all(self.stopped)

    def has_stopped(self):
        return all(self.stopped)

    def collect_progress(self):
        while not self.queue.empty():
            (nr,info) = self.queue.get()
            self.info[nr] = info
        runtime = time() - self.starttime
        return (self.info, runtime, self.stopped)

    def send_stopsignal(self):
        # workers will stop next time they send progress
        for k in range(self.nproc):
            self.stopQueue.put(k)
