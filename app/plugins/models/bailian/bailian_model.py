import requests

class BaiLianModel():

    def __init__(self):
        return

    def text2img(self,prompt:str,save_path:str):
        #存储文件到指定目录
        content = requests.get("https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/917a958a-0e57-4398-9936-c82f3267ecc6/original=true,quality=90/AiDaily0822_00273_.jpeg").content
        with open(save_path, 'wb') as file:
            file.write(content)
        return