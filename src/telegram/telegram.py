'''
This module provides the Telegram.
'''


class Telegram:
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
        '''
        Provides access to the sender.
        '''
        return self._sender

    @property
    def recipient(self):
        '''
        Provides access to the recipient.
        '''
        return self._recipient

    @property
    def message(self):
        '''
        Retrieve the message.
        '''
        return self._message
