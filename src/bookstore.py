from typing import Iterable

import oroshi


class Bookstore:
    def find_records_by_isbn(self, isbn: str) -> Iterable[oroshi.BookRecord]:
        raise NotImplementedError()
