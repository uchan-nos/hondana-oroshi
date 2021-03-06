# 
import collections
import enum
import sys
from typing import Iterable


BookRecord = collections.namedtuple(
    'BookRecord',
    ['record_id', 'status', 'title', 'isbn10', 'isbn13',
     'exists', 'inventoried', 'type'])
ActionSelection = collections.namedtuple(
    'ActionSelection', ['selected', 'action'])


class RecordStatus(enum.Enum):
    IN_SHELF = 1
    BORROWED = 2
    LOST = 3


class Bookstore:
    def find_records_by_isbn(self, isbn: str) -> Iterable[BookRecord]:
        raise NotImplementedError()

    def get_record(self, record_id: int) -> BookRecord:
        raise NotImplementedError()

    def add_record(self, record: BookRecord):
        raise NotImplementedError()

    def update_record(self, record: BookRecord):
        raise NotImplementedError()

    def found(self, record_id: int):
        raise NotImplementedError()


class Action:
    def __init__(self, record: BookRecord):
        self._record = record

    @property
    def record(self) -> BookRecord:
        return self._record

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def isbn(self) -> str:
        return get_isbn(self._record)

    def act(self):
        raise NotImplementedError()

    def _print(self, msg: str):
        print(msg)


class TakeInventory(Action):
    def __init__(self, record: BookRecord, bookstore: Bookstore):
        super().__init__(record)
        self._bookstore = bookstore

    def act(self):
        new_record = self.record._replace(inventoried=True)
        self._bookstore.update_record(new_record)


class RegisterNew(Action):
    def __init__(self, isbn: str, bookstore: Bookstore):
        super().__init__(None)
        self._isbn = isbn
        self._bookstore = bookstore

    def act(self):
        record = BookRecord(
            record_id=None,
            status=RecordStatus.IN_SHELF,
            title='NO_TITLE',
            isbn10=self._isbn if len(self._isbn) == 10 else None,
            isbn13=self._isbn if len(self._isbn) == 13 else None,
            exists='o',
            inventoried=True,
            type='未分類（要変更）')
        self._bookstore.add_record(record)

    @property
    def isbn(self) -> str:
        return self._isbn


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
    def __init__(self, record: BookRecord, bookstore: Bookstore):
        super().__init__(record)
        self._bookstore = bookstore

    def act(self):
        r = self.record
        self._bookstore.found(r.record_id)
        new_record = r._replace(inventoried=True)
        self._bookstore.update_record(new_record)


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
                   records: Iterable[BookRecord],
                   bookstore: Bookstore) -> Iterable[Action]:
    isbn_record_map = split_records_by_isbn(records)
    for isbn, records in isbn_record_map.items():
        not_inventoried_records = [r for r in records if not r.inventoried]
        isbn_record_map[isbn] = sort_records(not_inventoried_records)

    record_actions = []
    for barcode in barcodes:
        records = isbn_record_map.get(barcode, None)

        if not records:
            record_actions.append(RegisterNew(barcode, bookstore))
            continue

        record = records.pop(0)
        if record.exists == 'x':
            action = Discard(record)
        elif record.status is RecordStatus.BORROWED:
            action = Investigate(record)
        elif record.status is RecordStatus.LOST:
            action = Found(record, bookstore)
        else:
            action = TakeInventory(record, bookstore)

        record_actions.append(action)

    return record_actions


def show_action_selections(
        action_selections: Iterable[ActionSelection], *, file=sys.stdout):
    actsels = list(action_selections)
    actname_max = max(len(s.action.name) for s in actsels)
    isbn_max = max(len(s.action.isbn) for s in actsels)
    line_format = (
        '{:3}: {:3} {:' + str(actname_max) + '}  {:'
        + str(isbn_max) + '}  {} ({})\n')

    # show header
    file.write(line_format.format(
        'sel', 'Idx', 'Action', 'ISBN', 'Book title', 'Type'))

    for i, actsel in enumerate(actsels):
        record =  actsel.action.record
        title = record.title if record else 'no-title'
        record_type = record.type if record else 'no-type'
        file.write(line_format.format(
             '[*]' if actsel.selected else '[ ]', i,
             actsel.action.name,  actsel.action.isbn, title, record_type))


def select_actions(actions: Iterable[Action], *, stdin=None, stdout=None) \
        -> Iterable[ActionSelection]:
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout

    selections = [ActionSelection(True, a) for a in actions]
    while True:
        show_action_selections(selections, file=stdout)

        while True:
            print('"do", "quit", or an index> ', file=stdout, end='', flush=True)
            cmd = stdin.readline()
            if cmd == '':
                sys.exit(0)
            cmd = cmd.strip()

            if cmd == 'do':
                return selections
            if cmd == 'quit':
                sys.exit(0)
            if cmd.isdigit():
                index = int(cmd)
                try:
                    sel = selections[index]
                    selections[index] = ActionSelection(not sel.selected, sel.action)
                except IndexError:
                    print('Index must be in range {} - {}.'.format(0, index),
                          file=stdout, flush=True)
                break

    return selections


class Oroshi:
    def __init__(self, bookstore: Bookstore, *, stdin=None, stdout=None):
        self._bookstore = bookstore
        self._stdin = sys.stdin if stdin is None else stdin
        self._stdout = sys.stdout if stdout is None else stdout

    def run_once(self):
        print('Scan barcodes', file=self._stdout, flush=True)
        barcodes, last_line = read_barcodes(self._stdin)

        records = []
        for barcode in set(barcodes):
            records.extend(self._bookstore.find_records_by_isbn(barcode))

        actions = decide_actions(barcodes, records, self._bookstore)
        action_selections = select_actions(
            actions, stdin=self._stdin, stdout=self._stdout)
        for actsel in action_selections:
            if not actsel.selected:
                continue
            actsel.action.act()
