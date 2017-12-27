#!/usr/bin/python3

import pykintone
import pykintone.model
import pykintone.structure
from typing import Iterable

import oroshi


class RawBookRecord(pykintone.model.kintoneModel):
    def __init__(self):
        super().__init__()
        self.title = ''
        self.isbn10 = ''
        self.isbn13 = ''
        self.exists = ''
        self.inventoried = None
        self.type = ''

    def __str__(self):
        return 'RawBookRecord[{} {}{} exists={} invent={} type={}]'.format(
            self.title, self.isbn10, self.isbn13, self.exists,
            self.inventoried, self.type)

    @staticmethod
    def from_book_record(record: oroshi.BookRecord):
        raw_inventoried = ['済み'] if record.inventoried else []

        raw_record = RawBookRecord()
        raw_record.record_id = record.record_id
        raw_record.title = record.title
        raw_record.isbn10 = record.isbn10
        raw_record.isbn13 = record.isbn13
        raw_record.exists = record.exists
        raw_record.inventoried = raw_inventoried
        raw_record.type = record.type

        return raw_record


STATUS_MAP = {
    '本棚にあります': oroshi.RecordStatus.IN_SHELF,
    'レンタル中': oroshi.RecordStatus.BORROWED,
    'レンタル中(まであと一歩)': oroshi.RecordStatus.BORROWED,
    '紛失中': oroshi.RecordStatus.LOST,
}


class RawBookRecordWithStatus(RawBookRecord):
    def __init__(self):
        super().__init__()
        self.status = ''
        self._property_details.append(pykintone.structure.PropertyDetail(
            'status',
            pykintone.structure.FieldType.STATUS,
            field_name='処理状況'))

    def __str__(self):
        return 'RawBookRecordWithStatus[{} {}{} exists={} invent={} {}]'.format(
            self.title, self.isbn10, self.isbn13, self.exists,
            self.inventoried, self.status)

    def to_book_record(self) -> oroshi.BookRecord:
        status = STATUS_MAP[self.status]
        inventoried = len(self.inventoried) > 0
        return oroshi.BookRecord(
            record_id=self.record_id,
            status=status,
            title=self.title,
            isbn10=self.isbn10,
            isbn13=self.isbn13,
            exists=self.exists,
            inventoried=inventoried,
            type=self.type)


class KintoneBookstore(oroshi.Bookstore):
    def __init__(self, kintone_app):
        self._kintone_app = kintone_app

    def find_records_by_isbn(self, isbn: str) -> Iterable[oroshi.BookRecord]:
        if len(isbn) == 10:
            query = 'isbn10 = "{}"'.format(isbn)
        elif len(isbn) == 13:
            query = 'isbn13 = "{}"'.format(isbn)
        else:
            raise ValueError('ISBN length must be 10 or 13', isbn)

        records = self._kintone_app.select(query).models(RawBookRecordWithStatus)
        return (r.to_book_record() for r in records)

    def get_record(self, record_id: int) -> oroshi.BookRecord:
        record = self._kintone_app.get(record_id)
        return record.model(RawBookRecordWithStatus).to_book_record()

    def add_record(self, record: oroshi.BookRecord):
        return self._kintone_app.create(RawBookRecord.from_book_record(record))

    def update_record(self, record: oroshi.BookRecord):
        return self._kintone_app.update(RawBookRecord.from_book_record(record))

    def found(self, record_id: int):
        return self._kintone_app.proceed_by_id(record_id, '発見')


def main():
    kinapp = pykintone.load('kintone.yml').app(app_name='hondana')
    bookstore = KintoneBookstore(kinapp)
    o = oroshi.Oroshi(bookstore)
    o.run_once()


if __name__ == '__main__':
    main()
