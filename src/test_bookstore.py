import unittest

import bookstore
import oroshi
import test_oroshi


class FakeBookstore(bookstore.Bookstore):
    def __init__(self, records):
        self._records = records

    def find_records_by_isbn(self, isbn: str):
        return (r for r in self._records if oroshi.get_isbn(r) == isbn)


class BookstoreTest(unittest.TestCase):
    def setUp(self):
        records = [test_oroshi.FAKE_RECORD1, test_oroshi.FAKE_RECORD2,
                   test_oroshi.FAKE_RECORD30, test_oroshi.FAKE_RECORD31]
        self._instance = FakeBookstore(records)

    def test_find_records_by_isbn(self):
        records = list(self._instance.find_records_by_isbn(test_oroshi.ISBN1))
        self.assertEqual(len(records), 2)
        self.assertEqual(oroshi.get_isbn(records[0]), test_oroshi.ISBN1)

        records = list(self._instance.find_records_by_isbn(test_oroshi.ISBN3))
        self.assertEqual(len(records), 1)
        self.assertEqual(oroshi.get_isbn(records[0]), test_oroshi.ISBN3)
