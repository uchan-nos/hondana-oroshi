from typing import Iterable

import oroshi


class Bookstore:
    def find_records_by_isbn(self, isbn: str) -> Iterable[oroshi.BookRecord]:
        raise NotImplementedError()

    def get_record(self, record_id: int) -> oroshi.BookRecord:
        raise NotImplementedError()

    def add_record(self, record: oroshi.BookRecord):
        raise NotImplementedError()

    def update_record(self, record: oroshi.BookRecord):
        raise NotImplementedError()
