class StopControl:
    """
    This class is used to stop the mining process accross all threads.
    """

    def __init__(self):
        self.stop_requested = False

    def request_stop(self):
        self.stop_requested = True

    def should_stop(self):
        return self.stop_requested
