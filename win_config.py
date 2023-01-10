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


def write_json(config):
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def save_config(key, value):
    config = read_json()
    config[key] = value
    with open(json_file_path, 'w') as f:
        json.dump(config, f, indent=4)


def read_config(key):
    config = read_json()
    return config.get(key, None)


def save_video_item(index, key, value):
    config = read_json()
    videos = config.get("videos")
    videos[index][key] = value
    write_json(config)
