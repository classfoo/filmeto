
from utils.progress_utils import Progress


class BaseModelResult():

    def __init__(self):
        return

    def get_image(self):
        return None

class BaseModel():

    def __init__(self):
        return

    async def text2image(self,prompt:str,save_dir:str, progress:Progress):
        return
