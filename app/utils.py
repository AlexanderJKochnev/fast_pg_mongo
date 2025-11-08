# app/utils.py
from pathlib import Path
import re


def get_path_to_root(name: str = '.env'):
    """
        get path to file or directory in root directory
    """
    try:
        for k in range(1, 10):
            env_path = Path(__file__).resolve().parents[k] / name
            if env_path.exists():
                break
        else:
            env_path = None
            raise Exception('environment file is not found')
        return env_path
    except Exception:
        return None


def plural(single: str) -> str:
    """
    возвращает множественное число прописными буквами по правилам англ языка
    :param single:  single name
    :type name:     str
    :return:        plural name
    :rtype:         str
    """
    name = single.lower()
    if name.endswith('model'):
        name = name[0:-5]
    if not name.endswith('s'):
        if name.endswith('y'):
            name = f'{name[0:-1]}ies'
        else:
            name = f'{name}s'
    return name


def parse_unique_violation2(error_msg: str) -> dict:
    """
    Парсит сообщение об ошибке уникальности и извлекает:
    - название поля (constraint)
    - значение, которое вызвало конфликт

    Пример:
    Input: 'duplicate key value violates unique constraint "ix_foods_name"
            DETAIL: Key (name)=(Game (venison)) already exists.'
    Output: ('name', 'Game (venison)')
    """
    tmp = error_msg.split('DETAIL:  Key ', 1)
    tmp = tmp[1].split('already exists')
    result = tmp[0]
    if '=' in result:
        key, val = result.split('=')
        key = key.strip()[1:-1]
        val = val.strip()[1:-1]
        key = [a.strip() for a in key.split(',')]
        val = re.sub(r'\(([^)]*)\)', replace_commas_in_parentheses, val)
        val = [a.strip().replace('@', ',') for a in val.split(',', len(key))]
        val = [int(a) if a.isnumeric() else a for a in val]
        if all((key, val)):
            return dict(zip(key, val))


def replace_commas_in_parentheses(match, rep: str = '@'):
    # match.group(1) — содержимое внутри скобок
    inner = match.group(1)
    # Заменяем запятые на '@' только внутри скобок
    inner_replaced = inner.replace(',', '@')
    # Возвращаем скобки с изменённым содержимым
    return f"({inner_replaced})"
