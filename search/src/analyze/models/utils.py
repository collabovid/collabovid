def batch_iterator(iterable, batch_size=1):
    """
    yields batches from the given iterator
    :param iterable: The iterable that should be batched
    :param batch_size: The batch size
    :return:
    """
    from itertools import chain, islice
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, batch_size - 1)))
