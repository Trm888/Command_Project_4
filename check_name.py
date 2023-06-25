import re


class FullNameCheck:
    key = 'is_full_name'

    pattern = re.compile(r'^(?:[A-ZА-Я][a-zа-я]{1,} ){1,2}[A-ZА-Я][a-zа-я]{1,}$')

    def check(self, message):
        return self.pattern.match(message)
