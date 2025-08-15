def get_value(dict, key, default=None):
    if dict is None:
        return default
    return dict.get(key, default)

def set_value(dict, key, value):
    if dict is None:
        pass
    dict[key]=value