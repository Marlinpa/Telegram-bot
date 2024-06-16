from enum import Enum


class Symbols(Enum):
    NewLine = -1
    Tab = -2


def letters_to_files(text: str):
    ans = []
    cur = []
    for i in text:
        if i == " " or i == "\t":
            ans.append(cur)
            cur = []
        elif i == '\n':
            cur.append(Symbols.NewLine.value)
            ans.append(cur)
            cur = []
        elif i.isalpha():
            # алфавит в компьютере выглядит как: а, б, в, ..., э, ю, я, ё
            # поэтому пришлось накидать небольшой костыль
            num = ord(i) - ord('а')
            if i > 'е':
                num += 1
            elif i == 'ё':
                num = 6
            cur.append(str(num))
        else:
            raise Exception(f"Unsupported symbol: {i}")
    if len(cur) != 0:
        ans.append(cur)
    return ans

