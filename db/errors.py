class DbError(Exception): pass

class AudioCheckingBatch(DbError): pass
class InvalidTransition(DbError): pass
class LockedPerformance(DbError): pass
class SelfTransition(DbError): pass
