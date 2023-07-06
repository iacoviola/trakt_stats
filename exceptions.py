class EmptyResponseException(Exception):
    pass

class OverRateLimitException(Exception):
    pass
    def retry_after(self) -> int:
        return self.retry
    
class ItemNotFoundException(Exception):
    pass