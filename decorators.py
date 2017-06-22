#!/usr/bin/python3

def logging_decorator(function):
    ''' Takes function and logs its call as DEBUG '''
    import logging
    logging.basicConfig(level=logging.DEBUG, format='+ %(asctime)s - %(levelname)s - %(message)s')

    def wrapper_func(*args, **kwargs):
        logging.debug('{args} {kwargs}'.format(
            function = function,
            args = args,
            kwargs = kwargs))
        return function(*args, **kwargs)
    return wrapper_func
