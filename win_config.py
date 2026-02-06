import json

json_file_path = "configs/config.json"


# 配置参数命名说明:
# time - the time in seconds since the Epoch
# count - 总数
# no - 计数
# 读取配置文件
def read_json():
    with open(json_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_config(key):
    config = read_json()
    return config.get(key, None)
