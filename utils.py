import datetime
import sys

import numpy as np
import pandas as pd



def tighten_up(df, category_num_thresh=5000, verbose=True):
    """follow a few heuristics to reduce the size of the dataframe"""
    if verbose:
        s0 = sys.getsizeof(df)

    # get dates out of there first
    datecols = [_ for _ in df if 'date' in _.lower()]
    for dc in datecols:
        print('updating datecol: {}'.format(dc))
        df.loc[:, dc] = pd.to_datetime(df[dc])

    # let's treat anything smaller than our threshold as a categorical
    object_cols = df.dtypes[df.dtypes == object].index.values
    nu = df[object_cols].nunique()
    nu = nu[nu < category_num_thresh]
    categories = nu.index
    for col in set(categories).difference(datecols):
        print('categorizing {}'.format(col))
        cattype = pd.api.types.CategoricalDtype(
            categories=np.sort(df[col].unique()),
            ordered=True
        )
        df.loc[:, col] = df[col].astype(cattype)

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
