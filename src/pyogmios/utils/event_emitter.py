"""
This module contains the EventEmitter class.

The EventEmitter class can be used to emit events and listen to them.
"""
from typing import Dict

from typing import TypeVar, Callable
from queue import Queue

T = TypeVar("T")


class EventEmitter:
    """
    This class can be used to emit events and listen to them.
    """

    def __init__(self):
        self._callbacks: Dict[str, callable] = {}

    def on(self, event_name, function):
        """
        This function will add a listener to the event emitter.
        :param event_name: The name of the event to listen to.
        :param function: The function to call when the event is emitted.
        :return: The function that was passed as an argument.
        """
        self._callbacks[event_name] = self._callbacks.get(event_name, []) + [function]
        return function

    def emit(self, event_name, *args, **kwargs):
        """
        This function will emit an event.
        :param event_name: The name of the event to emit.
        :param args: The arguments to pass to the listeners.
        :param kwargs: The keyword arguments to pass to the listeners.
        """
        [function(*args, **kwargs) for function in self._callbacks.get(event_name, [])]

    def off(self, event_name, function):
        """
        This function will remove a listener from the event emitter.
        :param event_name: The name of the event to remove the listener from.
        :param function: The function to remove.
        """
        self._callbacks.get(event_name, []).remove(function)


def event_emitter_to_generator(
    event_emitter: EventEmitter, event_name: str, match: Callable[[str], T]
) -> Callable[[], T]:
    """
    This function will return a generator that will yield events as they are received.
    :param event_emitter: The event emitter to listen to.
    :param event_name: The name of the event to listen to.
    :param match: The function to use to match the received event.
    :return: Yielded events.
    """
    events = Queue()
    listeners = Queue()

    def on_event(e: str) -> None:
        """
        This function will be called when an event is received.
        :param e: Received event.
        """
        matched = match(e)
        if matched is not None:
            if not listeners.empty():
                listeners.get()(matched)
            else:
                events.put(matched)

    event_emitter.on(event_name, on_event)

    async def generator():
        """
        This generator will yield events as they are received.
        """
        while True:
            if not events.empty():
                yield events.get()
            else:
                listener = Queue()
                listeners.put(listener)
                yield await listener.get()

    return generator
