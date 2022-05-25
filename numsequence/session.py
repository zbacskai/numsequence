from numsequence.events import EventType, AcknowledgeEvent, NumberEvent, FinishAcknowledged
import random
import hashlib
SESSIONS = {}

def cosntruct_messaeges(in_list, batch_size):
    counter = 0
    ret_list = []
    inner_list = []
    print(batch_size)
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
    def __init__(self, number_of_numbers, batch_size):
        print('-----')
        self.number_of_numbers = number_of_numbers
        self.batch_size = batch_size
        self.numbers = [random.randint(0, 100) for _ in range(0, number_of_numbers)]
        self.messages = cosntruct_messaeges(self.numbers, self.batch_size)
        print(f'{self.numbers}')
        print(f'{self.messages}')

    def handle_event(self, event):
        if event.type == EventType.INIT or event.type == EventType.CONTINUE:
            return AcknowledgeEvent()

        if event.type == EventType.RECEIVE:
            return NumberEvent(self.messages[event.message_index])

        if event.type == EventType.FINISH:
            chksum = hashlib.md5(f'{self.numbers}'.encode())
            chksum = chksum.hexdigest()
            print(f'{chksum}')
            return FinishAcknowledged(chksum)

        return None


class SessionException(Exception):
    def __init__(self, msg):
        super(SessionException, self).__init__(msg)

class SessionHandlerFactory():
    def __init__(self):
        pass

    def get_session(self, event):
        if event.type == EventType.INIT:
            print('HERE')
            if event.client_id in SESSIONS:
                raise SessionException(f'{event.client_id} already exist')

            SESSIONS[event.client_id] = SessionHandler(event.number_of_numbers, event.batch_size)
            return SESSIONS[event.client_id]

        elif event.type == EventType.CONTINUE:
            if event.client_id not in SESSIONS:
                raise SessionException(f'{event.client_id} does not exist in store')
            return SESSIONS[event.client_id]

        raise SessionException(f'Invalid Event Type: {event.type}')
