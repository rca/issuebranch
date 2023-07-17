class BaseBackend(object):
    ACTIVE_COLUMN = "In Progress"

    def __init__(self, issue_number):
        self.issue_number = issue_number

    @property
    def prefix(self):
        raise NotImplementedError()
