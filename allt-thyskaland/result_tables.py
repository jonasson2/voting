import pandas as pd, numpy as np
from numpy import c_, r_
from copy import copy, deepcopy
from germany_dictionaries import method_measures, land_stats
from util import disp
pd.options.display.width = 0
pd.options.display.float_format = " {:,.2f}".format
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=120)

def add_summary_stats(index, seats):
    seats1 = copy(seats)
    for i in index:
        if i=='avg':  seats1 = r_[seats1, sum(seats)/len(seats)]
        elif i=='min': seats1 = r_[seats1, min(seats)]
        elif i=='max': seats1 = r_[seats1, max(seats)]
        elif i=='sum': seats1 = r_[seats1, sum(seats)]
    return seats1

def method_measure_table(methods, stats, info, type):
    A = []
    measures = (method_measures if type == 'land'
                else land_stats['const'] if type == 'constituency'
                else land_stats['pairs'])
    cols = []
    if not measures or not methods:
        return
    for m in measures:
        if m.endswith('dispar'):
            cols.append('min_' + m)
            cols.append('max_' + m)
        else:
            cols.append(m)
    for mth in methods:
        row = []
        for m in measures:
            stat = stats[mth][m]
            name = stat.name
            entry = get_stat(stat, with_detail=info["detail"])
            row.append(entry)
            if name.endswith('dispar'):
                entry = get_stat(stat, oper='max', with_detail=info["detail"])
                row.append(entry)
        A.append(row)
    idx = [m[:-1] if m.endswith('C') else m for m in methods]
    df = pd.DataFrame(A, index=idx, columns=cols)
    title = f'{type.upper()} METHODS: AVERAGE SIMULATED MEASURES'
    df.attrs['title'] = title
    df.index.name = 'method'
    print_df(df)
    #return df

def measure_table(method, stats, data, info, measures, select):
    is_pair = ':' in method
    index = list(info[select].values()) + ['min', 'max', 'sum', 'avg']
    if is_pair:
        #land_method, _ = method.split('')
        descriptor = "METHOD PAIR"
    else:
        descriptor = "LAND METHOD"
    if method not in stats:
        return None
    else:
        stats = stats[method]
    A = np.zeros((len(index), 0))
    #print(f'{land_stats["land"]=}')
    #print(f'{measures=}')
    #print(f'{stats.keys()=}')
    pass
    M = [m for m in measures if m in stats.keys()]
    for m in M:
        column = get_stat(stats[m], by=select, with_detail=info["detail"])
        A = c_[A, column]
    title = f"{select.upper()} MEASURES FOR {descriptor} {method.upper()}"
    seats = data["partyseats"] if select=='party' else data["landseats2021"]
    df = pd.DataFrame(A, index=index, columns=M)
    df['seats'] = [f"{s:.0f}" for s in add_summary_stats(df.index, seats)]
    df.attrs['title'] = title
    df.index.name = select
    print_df(df)
    #return df

def get_stat(stat, by = None, oper = None, with_detail=False):
    name = stat.name
    if stat.shape == 1:
        idx = 0
    else:
        if oper is None:
            if '-' in name:
                (_, name) = name.split('-')
            oper = ('min' if name.startswith('min') or name.endswith('dispar')
                    else 'max' if name.startswith('max')
                    else 'sum'
            )
        lenopt = len(stat.options)
        oper_pos = stat.options.index(oper) - lenopt
        idx = (stat.shape + oper_pos if isinstance(stat.shape, int)
               else tuple(s + oper_pos for s in stat.shape))
    fmt = ('.4f' if name.endswith('entropy_diff')
            else '.3%' if name.endswith(('share', 'marg', 'rate'))
            else '.3f')
    fmts = ('.3f' if name.endswith('entropy_diff')
            else '.2%' if name.endswith(('share', 'marg', 'rate'))
            else '.2f')
    val = stat.numpy_mean()
    error = stat.numpy_error()
    std = stat.numpy_std()
    if by is None:
        val = val[idx]
        error = error[idx]
        std = std[idx]
    elif isinstance(stat.shape, int):
        pass
    elif by == 'land':
        nland = stat.shape[0]
        val = val[range(nland), idx[1]]
        error = error[range(nland), idx[1]]
        std = std[range(nland), idx[1]]
    elif by == 'party':
        nparty = stat.shape[1]
        val = val[idx[0], range(nparty)]
        error = error[idx[0], range(nparty)]
        std = std[idx[0], range(nparty)]
    else:
        raise ValueError
    def entry(v, e, s):
        if with_detail:
            return f"{v:{fmt}} (±{e:{fmt}} s:{s:{fmts}})"
        else:
            return f"{v:{fmts}}"
    if isinstance(val, float):
        e = entry(val, error, std)
    else:
        e = [entry(v, e, s) for (v, e, s) in zip(val, error, std)]
    return e

def print_df(dfs, formats=None, wrap_headers=True):
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
        return formatters, default_format

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
    translate = {
        'alloc': 'allocations',
        'abs':   'absolute',
        'bundes':'bundeswide',
        'dispar':'disparity',
        'diff':  'difference',
        'diffs': 'differences',
        'freq':  'frequency',
        'marg':  'margin',
        'max':   'maximum',
        'min':   'minimum',
        'neg':   'negative',
        'opt':   'optimal',
        'sum':   'sum of',
    }
    #tr = {}
    if all('_' not in l for l in df.columns):
        return df
    def lineswrap(hdr):
        # Replace _ with space, replace abbreviations accoding to translate, and return
        # hdr split into two part of minimal max len
        words = hdr.split('_')
        for (s1,s2) in translate.items():
            words = [re.sub(f"^{s1}$", s2, w) for w in words]
        tuples = [(' '.join(words[:i]), ' '.join(words[i:])) for i in range(len(words))]
        hdrlens = [max(len(x),len(y)) for (x,y) in tuples]
        (x,y) = tuples[hdrlens.index(min(hdrlens))]
        return ' ' + x, ' ' + y
    df = deepcopy(df)
    df.columns = pd.MultiIndex.from_tuples([lineswrap(h) for h in df.columns])
    return df
