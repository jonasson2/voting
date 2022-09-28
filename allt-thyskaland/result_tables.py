import pandas as pd, numpy as np
from numpy import c_, r_
from copy import copy, deepcopy
from util import disp
from dictionaries import party_measures, land_measures, alloc_measures, measure_dicts, \
    measure_formats
pd.options.display.width = 0
pd.options.display.float_format = " {:,.2f}".format

def method_measure_table(running):
    # select can be party, 'mean' 'max' or 'sum'
    methods = list(running.keys())
    A = []
    for mth in methods:
        measures = list(running[mth].keys())
        for m in alloc_measures:
            measures.remove(m)
        row = []
        for m in measures:
            select = measure_dicts[m][1]
            running_entry = running[mth][m]
            if running_entry.shape == 1:
                sel_index = 0
            else:
                sel_index = running_entry.entries.index(select)
            avg = running_entry.mean()[sel_index]
            error = running_entry.error()[sel_index]
            fmt = measure_formats[m]
            entry = f"{avg:{fmt}} ± {error:{fmt}}"
            row.append(entry)
        A.append(row)
    df = pd.DataFrame(A, index=methods, columns=measures)
    title = f'AVERAGE SIMULATED MEASURES'
    df.attrs['title'] = title
    df.index.name = 'statemethod-constmethod'
    return df

def add_summary_stats(index, seats):
    seats1 = copy(seats)
    for i in index:
        if i=='mean':  seats1 = r_[seats1, seats.mean()]
        elif i=='min': seats1 = r_[seats1, seats.min()]
        elif i=='max': seats1 = r_[seats1, seats.max()]
        elif i=='sum': seats1 = r_[seats1, seats.sum()]
    return seats1

def measure_table(running, ref_alloc, method, select):
    # select is a list of measure short names
    if method not in running:
        return None
    measure_list = party_measures if select == 'party' else land_measures
    measures = [r for r in running[method].keys() if r in measure_list]
    index = running[method][measures[0]].entries
    A = np.zeros((len(index), 0))
    for m in measures:
        avg = running[method][m].mean()
        error = running[method][m].error()
        fmt = measure_formats[m]
        column = [f"{a:{fmt}} ± {e:{fmt}}" for (a, e) in zip(avg, error)]
        A = c_[A, column]
    title = f"{select.upper()} MEASURES FOR METHOD {method.upper()}"
    seats = ref_alloc.sum(axis = (0 if select=='party' else 1))
    df = pd.DataFrame(A, index=index, columns=measures)
    df['seats'] = [f"{s:.0f}" for s in add_summary_stats(df.index, seats)]
    df.attrs['title'] = title
    df.index.name = select
    return df

def print_df(dfs, formats=None, wrap_headers=False):
    # e.g. print_df(df, {'': '.2f', 'col2: '.1%'})
    if dfs is None: return

    def extend_block(block, number):
        w = len(block[0])
        block.extend(copy([' '*w])*number)
        return block

    def overwrite_start(string, replace):
        n = len(replace)
        return replace + string[n:]

    def get_formatters(formats):
        if formats is None: formats = {'': '.2f'}
        formatters = {k: ("  {:" + v + "}").format for (k, v) in formats.items()}
        if '' not in formatters: formatters[''] = " {:.2f}".format
        default_format = formatters['']
        return (formatters, default_format)

    def block(df, formats):
        (formatters, default_format) = get_formatters(formats)
        if wrap_headers:
            df = wrap_hdr(df)
        with pd.option_context("display.float_format", default_format,
                               "display.colheader_justify", 'center'):
            string = df.to_string(formatters=formatters)
            split = string.splitlines()
            width = max(map(len,split))
            has_multiindex = isinstance(df.columns, pd.MultiIndex)
            nheader = 2 if has_multiindex else 1
            if df.index.name is not None:
                split[nheader-1] = overwrite_start(split[nheader-1], df.index.name)
                del split[nheader]
            split.insert(nheader, '–'*width)
            if 'title' in df.attrs:
                width = max(width, len(df.attrs['title']))
                split.insert(0, df.attrs['title'].center(width))
            for i in range(len(split)):
                if len(split[i]) < width:
                    split[i] = split[i].ljust(width)
            return split

    if isinstance(dfs, pd.DataFrame):
        dfs = [dfs]
    blocks = [block(df, formats) for df in dfs]
    nlines = max(len(b) for b in blocks)
    for i in range(len(blocks)):
        blocks[i] = extend_block(blocks[i], nlines - len(blocks[i]))
    concatenated_rows = ["   ".join(rows) for rows in zip(*blocks)]
    print()
    print('\n'.join(concatenated_rows))

def wrap_hdr(df):
    import re
    tr = {'max':'maximum', 'min':'minimum', 'marg':'margin', 'freq':'frequency', 'alloc':
          'allocations', 'neg':'negative', 'dispar':'disparity', 'bundes':'bundeswide'}
    #tr = {}
    if all('_' not in l for l in df.columns):
        return df
    def lineswrap(hdr):
        # Replace _ with space, replace abbreviations accoding to tr, and return hdr
        # split into two part of minimal max len
        words = hdr.split('_')
        for (s1,s2) in tr.items():
            words = [re.sub(f"^{s1}$", s2, w) for w in words]
        tuples = [(' '.join(words[:i]), ' '.join(words[i:])) for i in range(len(words))]
        hdrlens = [max(len(x),len(y)) for (x,y) in tuples]
        (x,y) = tuples[hdrlens.index(min(hdrlens))]
        return (' ' + x, ' ' + y)
    df = deepcopy(df)
    df.columns = pd.MultiIndex.from_tuples([lineswrap(h) for h in df.columns])
    return df
