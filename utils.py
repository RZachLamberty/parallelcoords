import sys

import pandas as pd


def tighten_up(df, category_num_thresh=12, verbose=True):
    """follow a few heuristics to reduce the size of the dataframe"""
    if verbose:
        s0 = sys.getsizeof(df)

    # let's treat anything smaller than our threshold as a categorical
    nu = df.nunique()
    nu = nu[nu < category_num_thresh]
    categories = nu.index
    for col in categories:
        print('categorizing {}'.format(col))
        df.loc[:, col] = df[col].astype('category')

    del nu

    # now downcast numeric
    for col in set(df.columns).difference(categories):
        # this will be one of b(ool), u(nsigned), i(nteger), f(loat), c(omplex)
        dt = df[col].dtype
        dtk = df[col].dtype.kind

        if dtk == 'b':
            continue

        # unsigned, integer, or float could all possibly be downcast to unsigned
        if dtk in 'uif':
            df.loc[:, col] = pd.to_numeric(df[col], downcast='unsigned')
            if df[col].dtype != dt:
                continue

        # integer or float could both be downcast to signed ints
        if dtk in 'if':
            df.loc[:, col] = pd.to_numeric(df[col], downcast='integer')
            if df[col].dtype != dt:
                continue

        # finally, float could still be smaller (downcast to float)
        if dtk in 'f':
            df.loc[:, col] = pd.to_numeric(df[col], downcast='float')
            if df[col].dtype != dt:
                continue

    if verbose:
        s1 = sys.getsizeof(df)
        msg = (
            'the size of the dataframe went from {} down to {} ({:.0%} '
            'reduction)'
        )
        print(msg.format(s0, s1, 1 - s1 / s0))

    # no need to reply, all updates were made in place
