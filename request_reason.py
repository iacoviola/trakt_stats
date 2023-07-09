from enum import Enum
from functools import total_ordering

@total_ordering
class RequestReason(Enum):
    NO_REASON = -1
    RESULTS_FILE_MISSING = 0
    WATCHED_FILE_MISSING = 1
    WATCHED_FILE_DIFFERENT = 2

    def __lt__(self, other):
        return self.value < other.value
    
    def __gt__(self, other):
        return self.value > other.value
    
    def __eq__(self, other):
        return self.value == other.value