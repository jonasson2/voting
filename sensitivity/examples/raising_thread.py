from threading import Thread
import time

class RaisingThread(Thread):
    def run(self):
        self.exception = None
        try:
            super().run()            
        except Exception as e:
            self.exception = e
        
    def join(self):
        super().join()
        if self.exception:
            raise self.exception

def cause_error(timeout):
    time.sleep(timeout)
    raise Exception("My error")

try:
    thread = RaisingThread(target=cause_error, args=(1,))
    thread.start()
    thread.join()
except Exception as e:
    print('Caught exception', e)
