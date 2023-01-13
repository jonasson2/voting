from argparse import ArgumentParser
from subprocess import run, Popen, PIPE
from pathlib import Path
import time, socket, sys
sys.path.append("../backend")
from util import remove_suffix

def get_hostname():
    host = remove_suffix(socket.gethostname(), '.local')
    return host

def get_arguments(args, description=None, epilog=None):
    # Get arguments from command line and provide help. Returns a list
    # in the same order as the arguments in args.
    from argparse import RawTextHelpFormatter as raw, ArgumentDefaultsHelpFormatter as dhf
    from argparse import SUPPRESS
    class rawdhf(raw, dhf): pass
    p = ArgumentParser(description = description, epilog=epilog, formatter_class=rawdhf)
    #p = ArgumentParser(description=description, epilog=epilog)
    for arg in args:
        (name, type, help) = arg[:3]
        if name[0] == '-':
            short = name[:2]
            full = '-' + name
            if type == bool:
                p.add_argument(short, full, action='store_true', help=help)
            else:
                assert len(arg) > 3
                df = arg[3] if arg[3] else SUPPRESS
                if len(arg) == 5:
                    t = type
                    mv = arg[4]
                    p.add_argument(short, full, type=t, help=help, default=df, metavar=mv)
                else:
                    p.add_argument(short, full, type=type, help=help, default=df)
        else:
            if len(arg) == 3:
                p.add_argument(name, type=type, help=help)
            else:
                p.add_argument(name, type=type, help=help, nargs='?', default=arg[3])
    n = p.parse_args()
    return vars(n).values()

def runshell(command):
    result = run(command, stdout=PIPE, shell=True).stdout.decode().splitlines()
    return result

def run_parallel(node, command, errorfile=Path("/dev/null")):
    curdir = Path.cwd()
    runcmd = f'cd {curdir}; {command} > {errorfile} 2>&1 & echo $!'
    p = Popen(['ssh', node, runcmd], start_new_session=True, stdout = PIPE)
    pid = p.communicate()[0].decode().strip()
    return pid
