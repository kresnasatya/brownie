class TaskRunner:
    def __init__(self, tab):
        self.tab = tab
        self.tasks = []

    def schedule_task(self, task):
        self.tasks.append(task)

    def run(self):
        if len(self.tasks) > 0:
            task = self.tasks.pop(0)
            task.run()
