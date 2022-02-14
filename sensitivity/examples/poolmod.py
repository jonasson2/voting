from workers import askQs, ansQs, resQs, start, start_task, check, stop, nproc, setup
from time import sleep

def taskFunction(data, askQ, ansQ, resQ):
    (n, val) = data
    print('val=',val)
    for i in range(n):
        print(i, id)
        sleep(0.1)
        result = i*10
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
    resQs.put(result)

def run():
    setup(1)
    print('starting')
    id1 = start()
    for i in range(nproc):
        val = (12, i+1)
        print('val=',val)
        start_task(taskFunction, val, id1)
    print('workers started')
    sleep(0.4)
    k = check(id1)
    print('current iteration count:',k)
    id2 = start()
    for i in range(nproc):
        val = (22, i+1)
        print('val=',val)
        start_task(taskFunction, val, id2)
    sleep(0.4)
    k = stop(id1)
    print('total iteration count:', k)
    for i in range(nproc):
        print(f'getting result {id1}')
        res = result(id1)
        print(f'result {i}: {res}')
    # k = stop(id2)
    # print('total iteration count:', k)
    # for i in range(nproc):
    #     res = result(id2)
    #     print(f'result {i}: {res}')

if __name__ == "__main__":
    run()
