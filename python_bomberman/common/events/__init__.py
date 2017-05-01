

class EventDispatcher(object):
    def __init__(self, *args, **kwargs):
        self.events = {}

    def dispatch_event(self, event_name, *args, **kwargs):
        if event_name in self.events:
            for handlers in self.events[event_name]:
                for handler in handlers:
                    if handler(*args, **kwargs) is True:
                        break

    def push_handlers(self, handler, event_name, *handlers):
        if event_name not in self.events:
            raise EventDispatcherException.event_doesnt_exist(event_name)
        handler_id = id(handler)
        if handler_id not  in self.events[event_name]:
            self.events[event_name][handler_id] = []
        self.events[event_name][handler_id].push(handlers)

    def pop_handlers(self, handler):
        handler_id = id(handler)
        for event in self.events:
            if handler_id in self.events[event]:
                self.events[event].pop(handler_id)


class EventDispatcherException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def event_doesnt_exist(cls, event_name):
        return cls("Attempted to add handlers for an event '{}' that doesn't exist".format(event_name))






