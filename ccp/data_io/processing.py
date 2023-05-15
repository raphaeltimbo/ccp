"""Data processing functions for ccp.
"""
import pandas as pd


def fluctuation(x):
    """Calculate fluctuation of x.

    Fluctuation as defined in the ASME PTC 10-1997 is the highest reading minus
    the lowest reading divided by the mean of the readings.

    Parameters
    ----------
    x : array-like
        Array of values.

    Returns
    -------
    float
        Fluctuation of x.

    Examples
    --------
    >>> fluctuation([1, 2, 3, 4, 5])
    80.0
    >>> fluctuation([1, 1, 1, 1, 1])
    0.0
    """
    if x.mean() == 0:
        return 100
    else:
        return 100 * (x.max() - x.min()) / x.mean()


def fluctuation_data(df, window=3):
    """Calculate fluctuation of dataframe columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe with data to be filtered.
    window : int, optional
        Window size for rolling calculation. The default is 3.

    Returns
    -------
    pandas.DataFrame
        Dataframe with fluctuation values.


    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> fluctuation_data(df)
         a    b
    0  0.0  0.0
    1  0.0  0.0
    2  0.0  0.0
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> fluctuation_data(df, window=2)
            a    b
    0     0.0  0.0
    1  1000.0  0.0
    2  1000.0  0.0
    """
    fluctuation_df = (
        df.apply(pd.to_numeric)
        .rolling(
            window=window,
        )
        .apply(fluctuation)
        .fillna(0.0)
    )
    fluctuation_df = fluctuation_df[window - 1 :]
    fluctuation_df.reset_index(drop=True, inplace=True)
    return fluctuation_df


def filter_data(df, window=3, data_type=None):
    """Filter data according to fluctuation values.

    This function filters the data according to the fluctuation values of the
    columns. Default values for maximum fluctuation are based on ASME PTC 10-1997.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe with data to be filtered.

    window : int, optional
        Window size for rolling calculation, meaning how many rolls will be used
        to calculate the fluctuation.
        The default is 3.

    data_type : dict
        Dictionary with data types or maximum fluctuation values for each column.
        If the data_type is passed, the default maximum fluctuation values will
        be used.
        Values for data_type can be: "pressure", "temperature", "speed".

    Returns
    -------
    pandas.DataFrame
        Filtered dataframe.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3, 4, 4.01, 4.02], 'b': [4, 5, 6, 6.01, 6.02, 6.03]})
    >>> data_type = {'a': 'pressure', 'b': 'temperature'}
    >>> filter_data(df, window=3, data_type=data_type)
    """
    # default values for maximum fluctuation as per ASME PTC 10-1997
    maximum_fluctuation_values = {
        "pressure": 2,
        "temperature": 0.5,
        "speed": 0.5,
        None: None,
    }
    fluctuation_df = fluctuation_data(df, window=window)
    # TODO: Finish filtering based on maximum fluctuation values
    pass
