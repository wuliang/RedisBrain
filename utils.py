from math import sqrt

def stat(lst):
    """Calculate mean and std deviation from the input list."""
    n = float(len(lst))
    mean = sum(lst) / n
    stdev = sqrt((sum(x*x for x in lst) / n) - (mean * mean)) 
    return mean, stdev

def kmeans(lst, n):
    cluster = []
    for i in lst:
        if len(cluster) <= 1:    # the first two values are going directly in
            cluster.append(i)
            continue

        mean,stdev = stat(cluster)
        if abs(mean - i) > n * stdev:    # check the "distance"
            yield cluster
            cluster[:] = []    # reset cluster to the empty list

        cluster.append(i)
    yield cluster           # yield the last cluster
    
def collection_str(collection):
    if isinstance(collection, list):
        brackets = '[%s]'
        single_add = ''
    elif isinstance(collection, tuple):
        brackets = '(%s)'
        single_add =','
    else:
        return str(collection)
    items = ', '.join([collection_str(x) for x in collection])
    if len(collection) == 1:
        items += single_add
    return brackets % items
    
