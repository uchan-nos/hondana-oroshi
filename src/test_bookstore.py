import unittest

import bookstore
import oroshi
import test_oroshi


class FakeBookstore(bookstore.Bookstore):
    def __init__(self, records):
        # record_id must be unique to each other.
        self._records = records

    def find_records_by_isbn(self, isbn: str):
        return (r for r in self._records if oroshi.get_isbn(r) == isbn)

    def get_record(self, record_id: int):
        for r in self._records:
            if r.record_id == record_id:
                return r

    def add_record(self, record: oroshi.BookRecord):
        self._records.append(record)

    def update_record(self, record: oroshi.BookRecord):
        r = self.get_record(record.record_id)
        if r is None:
            raise RuntimeError('not found any records with ID', record.record_id)
        self._records.remove(r)
        self._records.append(record)


class BookstoreTest(unittest.TestCase):
    def setUp(self):
        records = [test_oroshi.FAKE_RECORD1, test_oroshi.FAKE_RECORD2,
                   test_oroshi.FAKE_RECORD31]
        self._instance = FakeBookstore(records)

    def test_find_records_by_isbn(self):
        records = list(self._instance.find_records_by_isbn(test_oroshi.ISBN1))
        self.assertEqual(len(records), 2)
        self.assertEqual(oroshi.get_isbn(records[0]), test_oroshi.ISBN1)

        records = list(self._instance.find_records_by_isbn(test_oroshi.ISBN3))
        self.assertEqual(len(records), 1)
        self.assertEqual(oroshi.get_isbn(records[0]), test_oroshi.ISBN3)

    def test_get_record(self):
        record = self._instance.get_record(1)
        self.assertEqual(record.record_id, 1)

        record = self._instance.get_record(2)
        self.assertEqual(record.record_id, 2)

    def test_add_record(self):
        records = list(self._instance.find_records_by_isbn(test_oroshi.ISBN2))
        self.assertEqual(len(records), 0)

        self._instance.add_record(test_oroshi.FAKE_RECORD30)

        records = list(self._instance.find_records_by_isbn(test_oroshi.ISBN2))
        self.assertEqual(len(records), 1)
        self.assertEqual(oroshi.get_isbn(records[0]), test_oroshi.ISBN2)

    def test_update_record(self):
        def get_not_inventoried_record(isbn):
            for record in self._instance.find_records_by_isbn(isbn):
                if not record.inventoried:
                    return record

        nir = get_not_inventoried_record(test_oroshi.ISBN1)
        record = oroshi.BookRecord(nir.record_id, nir.status, nir.title,
                                   nir.isbn10, nir.isbn13, nir.exists, True)
        self._instance.update_record(record)

        record = self._instance.get_record(nir.record_id)
        self.assertTrue(record.inventoried)
