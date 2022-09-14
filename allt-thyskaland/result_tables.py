import pandas as pd, numpy as np
from numpy import c_
from copy import copy, deepcopy
from util import disp
from dictionaries import short_party_measures, short_land_measures
pd.options.display.width = 0
pd.options.display.float_format = " {:,.2f}".format

def method_measure_table(running, measure_formats, select):
    # select can be party, 'mean' 'max' or 'sum'
    methods = list(running.keys())
    measures = list(running[methods[0]].keys())
    sel_index = running[methods[0]][measures[0]].names.index(select)
    A = []
    for mth in methods:
        row = []
        for m in measures:
            avg = running[mth][m].mean()[sel_index]
            std = running[mth][m].std()[sel_index]
            fmt = measure_formats[m]
            entry = f"{avg:{fmt}} ± {std:{fmt}}"
            row.append(entry)
        A.append(row)
    df = pd.DataFrame(A, index=methods, columns=measures)
    title = f"{select.upper()} MEASURES OVER PARTIES/CONSTITUENCES"
    df.attrs['title'] = title
    df.index.name = 'statemethod-constmethod'
    return df

def measure_table(running, measure_formats, method, select):
    # select is a list of measure short names
    measure_list = short_party_measures if select == 'party' else short_land_measures
    measures = [r for r in running[method].keys() if r in measure_list]
    index = running[method][measures[0]].names
    A = np.zeros((len(index), 0))
    for m in measures:
        avg = running[method][m].mean()
        std = running[method][m].std()
        fmt = measure_formats[m]
        column = [f"{a:{fmt}} ± {s:{fmt}}" for (a, s) in zip(avg, std)]
        A = c_[A, column]
    title = f"{select.upper()} MEASURES FOR METHOD {method.upper()}"
    df = pd.DataFrame(A, index=index, columns=measures)
    df.attrs['title'] = title
    df.index.name = select
    return df

def print_df(dfs, formats=None, wrap_headers=False):
    # e.g. print_df(df, {'': '.2f', 'col2: '.1%'})

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
    tr = {'max':'maximum', 'min':'minimum', 'marg':'margin', 'freq':'frequency',
          'neg':'negative'}
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
