
class Progress():

    def __init__(self):
        self.percent = 0
        self.logs = ''
        self.total = 0
        self.current = 0
        return

    def on_progress(self, percent:int, logs:str):
        self.percent = percent
        self.logs = logs
        return

    def on_log(self, logs:str):
        self.on_progress(self.percent, logs)

    def set_total(self, total:int):
        self.total = total

    def get_total(self):
        return self.total

    def set_current(self, current:int):
        self.current = current
        if self.total!=0:
            self.percent = int(current*100/self.total)
            self.on_progress(self.percent, self.logs)

    def get_current(self):
        return self.current