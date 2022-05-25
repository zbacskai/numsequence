from numsequence.events import EventType, AcknowledgeEvent, NumberEvent, FinishAcknowledged
import random
import hashlib
import os

TEST_MODE = os.environ.get('TEST_MODE') is not None
CLIENT_INFORMATION_TIMEOUT_SEC = 30

def construct_messaeges(in_list, batch_size):
    counter = 0
    ret_list = []
    inner_list = []
    for x in in_list:
        if (counter % batch_size) == 0:
            if counter != 0:
                ret_list.append(inner_list)
            inner_list = [x]
        else:
            inner_list.append(x)
        counter += 1

    if len(inner_list) > 0:
        ret_list.append(inner_list)

    return ret_list


class SessionHandler():
    def __init__(self, number_of_numbers, batch_size, client_id):
        self.number_of_numbers = number_of_numbers
        self.batch_size = batch_size
        if TEST_MODE:
            random.seed(client_id)
        self.numbers = [random.randint(0, 100) for _ in range(0, number_of_numbers)]
        self.messages = construct_messaeges(self.numbers, self.batch_size)

    def handle_event(self, event):
        if event.type == EventType.INIT or event.type == EventType.CONTINUE:
            return AcknowledgeEvent()

        if event.type == EventType.RECEIVE:
            return NumberEvent(self.messages[event.message_index])

        if event.type == EventType.FINISH:
            chksum = hashlib.md5(f'{self.numbers}'.encode())
            chksum = chksum.hexdigest()
            return FinishAcknowledged(chksum)

        return None


class SessionException(Exception):
    def __init__(self, msg):
        super(SessionException, self).__init__(msg)


class SessionHandlerFactory():
    def __init__(self, session_sorage):
        self._session_storage = session_sorage

    def get_session_handler(self, event):
        if event.type == EventType.INIT:
            if self._session_storage.get(event.client_id) is not None:
                raise SessionException(f'{event.client_id} already exist')

            session_handler = SessionHandler(event.number_of_numbers, event.batch_size, event.client_id)
            self._session_storage.set(event.client_id, session_handler, CLIENT_INFORMATION_TIMEOUT_SEC)
            return session_handler

        elif event.type == EventType.CONTINUE:
            session_handler = self._session_storage.get(event.client_id)
            if session_handler is None:
                raise SessionException(f'{event.client_id} does not exist in store')
            return session_handler

        raise SessionException(f'Invalid Event Type: {event.type}')
