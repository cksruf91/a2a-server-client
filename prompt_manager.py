from pathlib import Path

import yaml


class PromptManager:
    _file = Path('.').joinpath('resource').joinpath('prompt.yaml')
    _prompt = yaml.safe_load(_file.open('r'))

    _a2a = _prompt.get('a2a')
    host_system = _a2a.get('host').get('system')
