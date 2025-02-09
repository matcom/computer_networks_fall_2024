# src/exceptions.py

class SMTPException(Exception):
    pass

class TemporarySMTPException(SMTPException):
    pass

class PermanentSMTPException(SMTPException):
    pass
