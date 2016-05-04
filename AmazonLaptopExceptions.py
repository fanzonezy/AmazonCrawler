class CannotGetPageError(Exception):
    def __init___(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)