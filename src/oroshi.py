import collections
import enum
import sys
from typing import Iterable


BookRecord = collections.namedtuple(
    'BookRecord',
    ['record_id', 'status', 'title', 'isbn10', 'isbn13', 'exists', 'inventoried'])
RecordAction = collections.namedtuple('RecordAction', ['record', 'action'])


class RecordStatus(enum.Enum):
    IN_SHELF = 1
    BORROWED = 2
    LOST = 3


class Action:
    def act(self):
        raise NotImplementedError()


class TakeInventory(Action):
    def act(self):
        pass


class RegisterNew(Action):
    def act(self):
        pass


class Discard(Action):
    def act(self):
        pass


class Investigate(Action):
    def act(self):
        pass


class Found(Action):
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
                   records: Iterable[BookRecord]) -> Iterable[RecordAction]:
    isbn_record_map = split_records_by_isbn(records)
    for isbn, records in isbn_record_map.items():
        not_inventoried_records = [r for r in records if not r.inventoried]
        isbn_record_map[isbn] = sort_records(not_inventoried_records)

    record_actions = []
    for barcode in barcodes:
        try:
            records = isbn_record_map[barcode]
        except KeyError:
            records = None

        if not records:
            record_actions.append(RecordAction(None, RegisterNew()))
            continue

        record = records.pop(0)
        if record.exists == 'x':
            action = Discard()
        elif record.status is RecordStatus.BORROWED:
            action = Investigate()
        elif record.status is RecordStatus.LOST:
            action = Found()
        else:
            action = TakeInventory()

        record_actions.append(RecordAction(record, action))

    return record_actions
