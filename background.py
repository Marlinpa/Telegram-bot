from typing import List, Iterable
import os
import json


class Background:
    def __init__(self, left_border: int, right_border: int, space: int, cnt_str: int, vert_space: int, total: int, user_id: int):
        self.left_border = left_border
        self.right_border = right_border
        self.space = space
        self.cnt_str = cnt_str
        self.vert_space = vert_space
        self.total = total

        self.cur_str = 1
        self.cur_page = 1
        self.cursor = left_border
        self.new_line_flag = False

        self.width = {}
        self.height = {}

        letters_stats = os.path.join('letters', f'{user_id}', 'stats.json')
        with open(letters_stats, 'r') as f:
            d = json.load(f)
            self.width = d['width']
            self.height = d['height']

    def switch_line(self):
        self.new_line_flag = False
        if self.cur_str + 1 <= self.cnt_str:
            self.cur_str += 1
            self.cursor = self.left_border if self.cur_page < 2 else self.total + 3 * self.left_border
            return True
        self.cur_page += 1
        self.left_border, self.right_border = self.right_border, self.left_border
        self.cursor = self.total + 3 * self.left_border
        self.cur_str = 1
        assert self.cur_page <= 2
        return False

    def free_line_space(self):
        # total для второй страницы - это на самом деле 2 * self.total
        if self.cur_page == 1:
            return self.total - self.right_border - self.cursor
        return 2 * self.total - self.right_border - self.cursor

    def write_word(self, word):
        y = self.cur_str * self.vert_space
        for letter in word:
            yield [self.cursor, y]
            self.cursor += self.width[letter]

    def apply(self, word: List[int]) -> Iterable[List[int]]:
        if self.new_line_flag:
            self.new_line_flag = False
            self.switch_line()

        length = 0
        for letter in word:
            if letter == -1:
                self.new_line_flag = True
                break
            length += self.width[letter]

        if self.new_line_flag:
            word.pop(-1)

        if self.free_line_space() < length:
            self.switch_line()

        # "yield from" просто возвращает по очереди то же самое, что
        # возвращает yield в write word
        yield from self.write_word(word)

        if self.free_line_space() >= self.space:
            self.cursor += self.space
        else:
            self.switch_line()
