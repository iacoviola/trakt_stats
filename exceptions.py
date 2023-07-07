class EmptyResponseException(Exception):
    def __init__(self, message):
        super().__init__(message)

class OverRateLimitException(Exception):
    def __init__(self, message, retry_after):
        super().__init__(message)
        self.retry = int(retry_after)

    def retry_after(self) -> int:
        return self.retry
    
class ItemNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)