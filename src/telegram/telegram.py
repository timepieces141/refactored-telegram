'''
This module provides the Telegram.
'''


class Telegram(object):

    '''
    Telegram encapsulates the pieces and parts of a telegram.
    '''

    def __init__(self, sender, recipient, message):
        '''
        Constructs a Telegram instance.

        :param sender:     The sender of the telegram
        :param recipient:  The recipient of the telegram
        :param message:    The message contents
        '''
        self._sender = sender
        self._recipient = recipient
        self._message = message

    @property
    def sender(self):
        return self._sender

    @property
    def recipient(self):
        return self._recipient

    @property
    def message(self):
        return self._message
