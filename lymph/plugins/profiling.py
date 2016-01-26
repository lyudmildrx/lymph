from __future__ import absolute_import, unicode_literals

import cProfile
import functools
import pstats
import marshal
import itertools

from lymph.core import trace
from lymph.core.plugins import Plugin
from lymph.web.interfaces import WebServiceInterface


class Profiler(object):
    def __init__(self, interface, method, call_args, call_kwargs):
        # TODO: ############################################################3
        # TODO: ############################################################3
        # Consider https://github.com/srlindsay/gevent-profiler/blob/master/gevent_profiler/__init__.py
        # Make a config option? Both profilers could serve a purpose
        self.profiler = cProfile.Profile()
        self.interface = interface
        self.method_name = method.__name__
        self.call_args = call_args
        self.call_kwargs = call_kwargs

    def __enter__(self):
        self.profiler.enable()

    def __exit__(self, *args):
        self.profiler.disable()
        stats = pstats.Stats(self.profiler)
        self.interface.emit('profiling-data', {
            'stats': marshal.dumps(stats.stats),
            'details': {
                'name': self.interface.name,
                'method': self.method_name,
                'args': str(self.call_args),
                'kwargs': str(self.call_kwargs),
                'trace_id': trace.get_id(),
            }
        })
        self.profiler.clear()


def with_profiling(interface):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            with Profiler(interface, func, args, kwargs):
                return func(*args, **kwargs)
        return wrapped
    return wrapper


class ProfilingPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super(ProfilingPlugin, self).__init__()

    def on_interface_installation(self, interface):
        wrapper = with_profiling(interface)
        for methods in (interface.methods, interface.event_handlers):
            for method in methods.values():
                method.decorate(wrapper)

        if isinstance(interface, WebServiceInterface):
            interface.handle = wrapper(interface.handle)
