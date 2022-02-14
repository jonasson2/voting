from workers import Workers
from time import sleep

nproc = 3

def taskFunction(data, askQ, ansQ, resQ):
    (n, val) = data
    print('val=',val)
    for i in range(n):
        print('i=',i)
        sleep(0.1)
        result = i*10
        print('(1)')
        e = askQ.empty()
        print('(2)')
        if not askQ.empty():
            chk = askQ.get()
            ansQ.put(i)
            stop = chk == 'stop'
            if stop:
                print('stopping, result=', result)
                print('resQ=', resQ)
                resQ.put(result)
                return
    print('(x) result=', result)
    resQ.put(result)

def run():
    workers = Workers(nproc)
    for i in range(nproc):
        val = (12, i+1)
        print('val=',val)
        workers.start_task(taskFunction, val)
    print('workers started')
    sleep(0.4)
    k = workers.check()
    print('current iteration count:',k)
    sleep(0.4)
    k = workers.stop()
    print('total iteration count:', k)
    for i in range(workers.nproc):
        res = workers.result()
        print(f'result {i}: {res}')

if __name__ == "__main__":
    run()
