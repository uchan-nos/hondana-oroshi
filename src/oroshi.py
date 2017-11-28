import collections
import enum
import sys
from typing import Iterable


BookRecord = collections.namedtuple(
    'BookRecord',
    ['record_id', 'status', 'title', 'isbn10', 'isbn13', 'exists', 'inventoried'])


class RecordStatus(enum.Enum):
    IN_SHELF = 1
    BORROWED = 2
    LOST = 3


class Action:
    def __init__(self, record: BookRecord):
        self._record = record

    @property
    def record(self) -> BookRecord:
        return self._record

    def act(self):
        raise NotImplementedError()

    def _print(self, msg: str):
        print(msg)


class TakeInventory(Action):
    def __init__(self, record: BookRecord):
        super().__init__(record)

    def act(self):
        pass


class RegisterNew(Action):
    def __init__(self, isbn: str):
        super().__init__(None)
        self._isbn = isbn

    def act(self):
        pass


class Discard(Action):
    def __init__(self, record: BookRecord):
        super().__init__(record)

    def act(self):
        self._print('Please discard this book: "{}" (ISBN={})'.format(
            self.record.title, get_isbn(self.record)))


class Investigate(Action):
    def __init__(self, record: BookRecord):
        super().__init__(record)

    def act(self):
        self._print(
            ('This book\'s borrowed on record, but it\'s here.'+
            'Please investigate it: "{}" (ISBN={})').format(
            self.record.title, get_isbn(self.record)))


class Found(Action):
    def __init__(self, record: BookRecord):
        super().__init__(record)

    def act(self):
        pass


def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def read_barcodes(file=sys.stdin) -> (list, str):
    barcodes = []
    for line in file:
        line = line.strip()
        if not line.isdigit() and len(line) != 13 and len(line) != 10:
            return barcodes, line
        barcodes.append(line)

    return barcodes, None


def get_isbn(record: BookRecord) -> str:
    if record.isbn13:
        return record.isbn13
    return record.isbn10


def split_records_by_isbn(records: Iterable[BookRecord]) -> dict:
    result = {}
    for record in records:
        if record.isbn13:
            isbn = record.isbn13
        elif record.isbn10:
            isbn = record.isbn10
        else:
            isbn = 'UNKNOWN_ISBN'

        if isbn not in result:
            result[isbn] = []

        result[isbn].append(record)

    return result


def sort_records(records: Iterable[BookRecord]) -> Iterable[BookRecord]:
    # sorted sorts boolean values in this order:
    #     sorted([True, False]) == [False, True]

    def key(record: BookRecord) -> tuple:
        exists = record.exists == 'o'
        return (record.inventoried, not exists, record.status.value, record.record_id)

    return sorted(records, key=key)


def decide_actions(barcodes: Iterable[str],
                   records: Iterable[BookRecord]) -> Iterable[Action]:
    isbn_record_map = split_records_by_isbn(records)
    for isbn, records in isbn_record_map.items():
        not_inventoried_records = [r for r in records if not r.inventoried]
        isbn_record_map[isbn] = sort_records(not_inventoried_records)

    record_actions = []
    for barcode in barcodes:
        records = isbn_record_map.get(barcode, None)

        if not records:
            record_actions.append(RegisterNew(None))
            continue

        record = records.pop(0)
        if record.exists == 'x':
            action = Discard(record)
        elif record.status is RecordStatus.BORROWED:
            action = Investigate(record)
        elif record.status is RecordStatus.LOST:
            action = Found(record)
        else:
            action = TakeInventory(record)

        record_actions.append(action)

    return record_actions
