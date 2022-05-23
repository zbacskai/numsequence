from enum import Enum


class EventType(Enum):
    INIT = 1
    ACKNOWLEDGE = 2
    RECEIVE = 3
    NUMBERS = 4
    FINISH = 5
    FINISH_ACKNOWLEDGED = 6
    CONTINUE = 7


class Event():
    def __init__(self, type):
        self.type = type


class InitEvent(Event):
    def __init__(self, client_id, number_of_numbers, batch_size):
        super(InitEvent, self).__init__(EventType.INIT)
        self.client_id = client_id
        self.number_of_numbers = number_of_numbers
        self.batch_size = batch_size


class AcknowledgeEvent(Event):
    def __init__(self):
        super(AcknowledgeEvent, self).__init__(EventType.ACKNOWLEDGE)


class ReceiveEvent(Event):
    def __init__(self, message_index):
        super(ReceiveEvent, self).__init__(EventType.RECEIVE)
        self.message_index = message_index


class NumbersEvent(Event):
    def __init__(self, numbers):
        super(NumbersEvent, self).__init__(EventType.NUMBERS)
        self.numbers = numbers


class FinishEvent(Event):
    def __init__(self):
        super(FinishEvent, self).__init__(EventType.FINISH)


class FinishAcknowledged(Event):
    def __init__(self, checksum):
        super(FinishAcknowledged, self).__init__(EventType.FINISH_ACKNOWLEDGED)
        self.cheksum = checksum


class ContinueEvent(Event):
    def __init__(self, client_id, message_index):
        super(ContinueEvent, self).__init__()
        self.client_id = client_id
        self.message_index = message_index
