"""
A queue that can be used to store tasks.

This module contains the Queue class.
"""
from collections import deque
from typing import Callable, Any

from promise import Promise


class Queue:
    """
    A queue that can be used to store tasks.
    """

    def __init__(self):
        self._elements = deque()

    def pop(self):
        """
        Remove the first task from the queue.
        :return: The first task from the queue.
        """
        self._elements.pop()

    def dequeue(self):
        """
        Remove the first task from the queue.
        :return: The first task from the queue.
        """
        return self._elements.popleft()

    def unshift(self, element):
        """
        Add a task at the beginning of the queue.
        :param element: The task to be added to the queue.
        :return: None
        """
        self._elements.appendleft(element)

    def promise_unshift(self, element) -> Promise:
        """
        Add a task at the beginning of the queue. The returned Promise will be fulfilled (rejected) when the task is completed successfully (unsuccessfully).
        This promise could be ignored as it will not lead to a 'unhandledRejection'.
        :param element: The task to be added to the queue.
        :return:
        """

        def executor(
            resolve: Callable[[Any], None], reject: Callable[[Exception], None]
        ) -> None:
            """
            The executor function for the Promise.
            :param resolve: The resolve function of the Promise.
            :param reject: The reject function of the Promise.
            :return: None
            """
            try:
                resolve(self.unshift(element))
            except Exception as error:
                reject(error)
            return None

        return Promise(executor)

    def push(self, element):
        """
        Add a task at the end of the queue.
        :param element: The task to be added to the queue.
        :return: None
        """
        self._elements.append(element)

    def promise_push(self, element) -> Promise:
        """
        Add a task at the end of the queue. The returned Promise will be fulfilled (rejected) when the task is
        completed successfully (unsuccessfully).
        This promise could be ignored as it will not lead to a 'unhandledRejection'.
        :param element: The task to be added to the queue.
        :return: A Promise that will be fulfilled (rejected) when the task is completed successfully (unsuccessfully).
        """

        def executor(
            resolve: Callable[[Any], None], reject: Callable[[Exception], None]
        ) -> None:
            """
            The executor function for the Promise.
            :param resolve: The resolve function of the Promise.
            :param reject: The reject function of the Promise.
            :return: None
            """
            try:
                resolve(self.push(element))
            except Exception as error:
                reject(error)
            return None

        return Promise(executor)
