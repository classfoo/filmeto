
class Progress():

    def __init__(self):
        self.percent = 0
        return

    def onProgress(self, percent:int):
        self.percent = percent
        return