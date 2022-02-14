from util import remove_suffix, remove_prefix, disp

def traceline(line):
    # Extracts filename and line number from traceback file line
    from pathlib import Path
    word = line.split()
    file = remove_suffix(remove_prefix(word[1], '"'), '",')
    file = Path(file).name
    lineno = remove_suffix(word[3], ',') if len(word) > 3 else ""
    #function = word[5]
    tline = f"{file}:{lineno}"
    return tline

def traceblock(lines, sep):
    # Extracts trace lines as "file:line, file:line...: error" from traceback block
    file_indices = [k for (k,s) in enumerate(lines) if s.startswith('  File')]
    trace = sep.join(traceline(lines[t]) for t in file_indices)
    if file_indices and len(lines) > file_indices[-1] + 1:
        errormessage = lines[file_indices[-1]+2]
    else:
        errormessage = ""
    return (trace, errormessage)

def traceblocks(trace, sep=", "):
    # Construct list of trace lines and error messages
    tb_indices = [k for (k,s) in enumerate(trace) if s.startswith('Traceback ')]
    if not tb_indices:
        return "unkown location", "unknown error"
    tb_indices.append(len(trace))
    blocks = []
    errors = []
    for i in range(len(tb_indices) - 1):
        b = tb_indices[i]
        e = tb_indices[i+1]
        (block, errormessage) = traceblock(trace[b:e], sep)
        blocks.insert(0, block)
        errors.insert(0, errormessage)
    return blocks, errors

def short_traceback(python_trace):
    trace = python_trace.splitlines()
    blocks, errors = traceblocks(trace)
    return f"Server error ({blocks[0]}):\n{errors[0]}"

def traceback(python_trace, indent=2):
    spc = " "*indent
    trace = python_trace.splitlines()
    blocks, errors = traceblocks(trace)
    blksep = "\n" + spc
    tb = spc + blksep.join([f"{b}: {e}" for (b,e) in zip(blocks, errors)])
    return tb

def long_traceback(python_trace, indent=2):
    spc = " "*indent
    spc2 = spc*2
    trace = python_trace.splitlines()
    blocks, errors = traceblocks(trace, "\n  ")
    blksep = "\n" + spc
    tb = spc + blksep.join([f"{b}\n{spc2}{e}" for (b,e) in zip(blocks, errors)])
    return tb
