import io
import unittest
from unittest import mock

import oroshi


ISBN1 = '9784789849944'
ISBN2 = '9784839919849'
ISBN3 = '4810180778'

IN_SHELF = oroshi.RecordStatus.IN_SHELF
BORROWED = oroshi.RecordStatus.BORROWED
LOST = oroshi.RecordStatus.LOST

FAKE_RECORD1  = oroshi.BookRecord(1,  IN_SHELF, 'book1', '', ISBN1, 'o', True)
FAKE_RECORD2  = oroshi.BookRecord(2,  IN_SHELF, 'book1', '', ISBN1, 'o', False)
FAKE_RECORD3  = oroshi.BookRecord(3,  IN_SHELF, 'book1', '', ISBN1, 'x', True)
FAKE_RECORD4  = oroshi.BookRecord(4,  IN_SHELF, 'book1', '', ISBN1, 'x', False)
FAKE_RECORD11 = oroshi.BookRecord(11, BORROWED, 'book1', '', ISBN1, 'o', True)
FAKE_RECORD12 = oroshi.BookRecord(12, BORROWED, 'book1', '', ISBN1, 'o', False)
FAKE_RECORD13 = oroshi.BookRecord(13, BORROWED, 'book1', '', ISBN1, 'x', True)
FAKE_RECORD14 = oroshi.BookRecord(14, BORROWED, 'book1', '', ISBN1, 'x', False)
FAKE_RECORD21 = oroshi.BookRecord(21, LOST,     'book1', '', ISBN1, 'o', True)
FAKE_RECORD22 = oroshi.BookRecord(22, LOST,     'book1', '', ISBN1, 'o', False)
FAKE_RECORD23 = oroshi.BookRecord(23, LOST,     'book1', '', ISBN1, 'x', True)
FAKE_RECORD24 = oroshi.BookRecord(24, LOST,     'book1', '', ISBN1, 'x', False)
FAKE_RECORD30 = oroshi.BookRecord(30, IN_SHELF, 'book2', '', ISBN2, 'o', False)
FAKE_RECORD31 = oroshi.BookRecord(31, IN_SHELF, 'book3', ISBN3, '', 'o', False)


class OroshiFuncTest(unittest.TestCase):

    def test_read_barcodes(self):
        inp = io.StringIO('{}\n{}\n'.format(ISBN1, ISBN2))
        barcodes, last = oroshi.read_barcodes(inp)
        self.assertEqual(barcodes, [ISBN1, ISBN2])
        self.assertEqual(last, None)

    def test_read_barcodes2(self):
        inp = io.StringIO('{}\nhogera\n'.format(ISBN1))
        barcodes, last = oroshi.read_barcodes(inp)
        self.assertEqual(barcodes, [ISBN1])
        self.assertEqual(last, 'hogera')

    def test_get_isbn(self):
        self.assertEqual(oroshi.get_isbn(FAKE_RECORD1), ISBN1)
        self.assertEqual(oroshi.get_isbn(FAKE_RECORD31), ISBN3)

    def test_action(self):
        action = oroshi.Action(FAKE_RECORD1)
        self.assertEqual(action.record, FAKE_RECORD1)
        self.assertEqual(action.isbn, ISBN1)

    def test_split_records_by_isbn(self):
        records = [FAKE_RECORD1, FAKE_RECORD2, FAKE_RECORD3, FAKE_RECORD4,
                   FAKE_RECORD11, FAKE_RECORD12, FAKE_RECORD13, FAKE_RECORD14,
                   FAKE_RECORD21, FAKE_RECORD22, FAKE_RECORD23, FAKE_RECORD24,
                   FAKE_RECORD30]
        isbn_record_map = oroshi.split_records_by_isbn(records)

        self.assertIsInstance(isbn_record_map, dict)
        self.assertEqual(len(isbn_record_map), 2)
        self.assertEqual(len(isbn_record_map[ISBN1]), 12)
        self.assertEqual(len(isbn_record_map[ISBN2]), 1)

        self.assertEqual(isbn_record_map[ISBN1][0].isbn13, ISBN1)
        self.assertEqual(isbn_record_map[ISBN2][0].isbn13, ISBN2)

    def test_sort_records(self):
        # 棚卸していないレコード優先
        self.assertEqual(
            oroshi.sort_records([FAKE_RECORD1, FAKE_RECORD2]),
            [FAKE_RECORD2, FAKE_RECORD1])

        # 本が存在する（"o"）レコード優先
        self.assertEqual(
            oroshi.sort_records([FAKE_RECORD4, FAKE_RECORD2]),
            [FAKE_RECORD2, FAKE_RECORD4])

        # 棚にあるレコード優先
        self.assertEqual(
            oroshi.sort_records([FAKE_RECORD12, FAKE_RECORD2, FAKE_RECORD22]),
            [FAKE_RECORD2, FAKE_RECORD12, FAKE_RECORD22])

    def test_decide_actions_バーコードに対応するレコードがちょうどある(self):
        # FAKE_RECORD2, FAKE_RECORD30: 棚卸しておらず、本棚に存在する
        fake_records = [FAKE_RECORD2, FAKE_RECORD30]
        barcodes = [ISBN1, ISBN2]
        actions = oroshi.decide_actions(barcodes, fake_records, None)

        self.assertEqual(len(actions), 2)

        self.assertIsInstance(actions[0], oroshi.TakeInventory)
        self.assertEqual(actions[0].record, FAKE_RECORD2)

        self.assertIsInstance(actions[1], oroshi.TakeInventory)
        self.assertEqual(actions[1].record, FAKE_RECORD30)

    def test_decide_actions_バーコードに対応するレコードが無い(self):
        fake_records = []
        barcodes = [ISBN1]
        actions = oroshi.decide_actions(barcodes, fake_records, None)

        self.assertEqual(len(actions), 1)

        self.assertIsInstance(actions[0], oroshi.RegisterNew)
        self.assertIsNone(actions[0].record)
        self.assertEqual(actions[0].isbn, ISBN1)

    def test_decide_actions_あるISBNのバーコードがレコードより多い(self):
        # FAKE_RECORD2: 棚卸しておらず、本棚に存在する
        fake_records = [FAKE_RECORD2]
        barcodes = [ISBN1, ISBN1]
        actions = oroshi.decide_actions(barcodes, fake_records, None)

        self.assertEqual(len(actions), 2)

        self.assertIsInstance(actions[0], oroshi.TakeInventory)
        self.assertEqual(actions[0].record, FAKE_RECORD2)

        self.assertIsInstance(actions[1], oroshi.RegisterNew)
        self.assertIsNone(actions[1].record)

    def test_decide_actions_棚卸済レコードは無視(self):
        # decide_actions は既に棚卸済みのレコードを無視する
        fake_records = [
            FAKE_RECORD1, FAKE_RECORD3,
            FAKE_RECORD11, FAKE_RECORD13,
            FAKE_RECORD21, FAKE_RECORD23]
        action, = oroshi.decide_actions([ISBN1], fake_records, None)
        self.assertIsInstance(action, oroshi.RegisterNew)
        self.assertIsNone(action.record)

    def test_decide_actions_本が存在せず棚にある(self):
        # 存在しないはずの本なので捨てる。
        action, = oroshi.decide_actions([ISBN1], [FAKE_RECORD4], None)
        self.assertIsInstance(action, oroshi.Discard)
        self.assertEqual(action.record, FAKE_RECORD4)

    def test_decide_actions_本が存在せず借りられている(self):
        # バーコードが読み取れたということは、その本は事実そこにある。
        # つまり、誰にも借りられていないので捨てて良い。
        action, = oroshi.decide_actions([ISBN1], [FAKE_RECORD14], None)
        self.assertIsInstance(action, oroshi.Discard)
        self.assertEqual(action.record, FAKE_RECORD14)

    def test_decide_actions_本が存在せず紛失している(self):
        # バーコードが読み取れたということは、その本は事実そこにある。
        # つまり、誰にも借りられていないので捨てて良い。
        action, = oroshi.decide_actions([ISBN1], [FAKE_RECORD24], None)
        self.assertIsInstance(action, oroshi.Discard)
        self.assertEqual(action.record, FAKE_RECORD24)

    def test_decide_actions_本が存在し借りられている(self):
        # バーコードが読み取れたということは、その本は事実そこにある。
        # 誰にも借りられていないがステータスがそのままの可能性がある。
        action, = oroshi.decide_actions([ISBN1], [FAKE_RECORD12], None)
        self.assertIsInstance(action, oroshi.Investigate)
        self.assertEqual(action.record, FAKE_RECORD12)

    def test_decide_actions_本が存在し紛失している(self):
        # バーコードが読み取れたということは、その本は事実そこにある。
        # 紛失中ステータスを発見ステータスに変える。
        action, = oroshi.decide_actions([ISBN1], [FAKE_RECORD22], None)
        self.assertIsInstance(action, oroshi.Found)
        self.assertEqual(action.record, FAKE_RECORD22)

    def test_show_action_selections(self):
        stdout = io.StringIO()
        actions = oroshi.decide_actions([ISBN1], [FAKE_RECORD2], None)
        oroshi.show_action_selections(
            (oroshi.ActionSelection(True, a) for a in actions), file=stdout)

        stdout.seek(0)
        _ = stdout.readline()
        line = stdout.readline()
        self.assertIn('[*]', line)
        self.assertIn(ISBN1, line)
        self.assertIn(FAKE_RECORD2.title, line)
        self.assertIn(oroshi.TakeInventory(None, None).name, line)

    def test_show_action_selections_not_selected(self):
        stdout = io.StringIO()
        actions = oroshi.decide_actions([ISBN1], [FAKE_RECORD2], None)
        oroshi.show_action_selections(
            (oroshi.ActionSelection(False, a) for a in actions), file=stdout)

        stdout.seek(0)
        _ = stdout.readline()
        line = stdout.readline()
        self.assertIn('[ ]', line)

    def test_show_action_selections_register_new(self):
        stdout = io.StringIO()
        actions = oroshi.decide_actions([ISBN1], [], None)
        oroshi.show_action_selections(
            (oroshi.ActionSelection(True, a) for a in actions), file=stdout)

        stdout.seek(0)
        _ = stdout.readline()
        line = stdout.readline()
        self.assertIn(ISBN1, line)
        self.assertNotIn(FAKE_RECORD2.title, line)
        self.assertIn(oroshi.RegisterNew(None).name, line)

    def test_select_actions(self):
        stdin = io.StringIO('1\ndo\n')
        stdout = io.StringIO()
        actions = oroshi.decide_actions(
            [ISBN1, ISBN1, ISBN2],
            [FAKE_RECORD2, FAKE_RECORD22, FAKE_RECORD30], None)
        action_selection = oroshi.select_actions(actions, stdin=stdin, stdout=stdout)

        self.assertEqual(len(action_selection), 3)
        self.assertTrue(action_selection[0].selected)
        self.assertIsInstance(action_selection[0].action, oroshi.TakeInventory)
        self.assertFalse(action_selection[1].selected)
        self.assertIsInstance(action_selection[1].action, oroshi.Found)
        self.assertTrue(action_selection[2].selected)
        self.assertIsInstance(action_selection[2].action, oroshi.TakeInventory)


class FakePrinter:
    def __init__(self):
        self.called = False

    def __call__(self, msg: str):
        self.msg = msg
        self.called = True


class FakeBookstore(oroshi.Bookstore):
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


class TakeInventoryTest(unittest.TestCase):
    def setUp(self):
        records = [FAKE_RECORD2]
        self._bookstore = FakeBookstore(records)
        self._instance = oroshi.TakeInventory(FAKE_RECORD2, self._bookstore)

    def test_act(self):
        self.assertFalse(self._bookstore.get_record(2).inventoried)
        self._instance.act()
        self.assertTrue(self._bookstore.get_record(2).inventoried)


class DiscardTest(unittest.TestCase):
    def setUp(self):
        self._instance = oroshi.Discard(FAKE_RECORD4)
        self._instance._print = FakePrinter()

    def test_act(self):
        self._instance.act()
        self.assertTrue(self._instance._print.called)
        self.assertIn('book1', self._instance._print.msg)
        self.assertIn(ISBN1, self._instance._print.msg)


class InvestigateTest(unittest.TestCase):
    def setUp(self):
        self._instance = oroshi.Investigate(FAKE_RECORD12)
        self._instance._print = FakePrinter()

    def test_act(self):
        self._instance.act()
        self.assertTrue(self._instance._print.called)
        self.assertIn('book1', self._instance._print.msg)
        self.assertIn(ISBN1, self._instance._print.msg)


class BookstoreTest(unittest.TestCase):
    def setUp(self):
        records = [FAKE_RECORD1, FAKE_RECORD2,
                   FAKE_RECORD31]
        self._instance = FakeBookstore(records)

    def test_find_records_by_isbn(self):
        records = list(self._instance.find_records_by_isbn(ISBN1))
        self.assertEqual(len(records), 2)
        self.assertEqual(oroshi.get_isbn(records[0]), ISBN1)

        records = list(self._instance.find_records_by_isbn(ISBN3))
        self.assertEqual(len(records), 1)
        self.assertEqual(oroshi.get_isbn(records[0]), ISBN3)

    def test_get_record(self):
        record = self._instance.get_record(1)
        self.assertEqual(record.record_id, 1)

        record = self._instance.get_record(2)
        self.assertEqual(record.record_id, 2)

    def test_add_record(self):
        records = list(self._instance.find_records_by_isbn(ISBN2))
        self.assertEqual(len(records), 0)

        self._instance.add_record(FAKE_RECORD30)

        records = list(self._instance.find_records_by_isbn(ISBN2))
        self.assertEqual(len(records), 1)
        self.assertEqual(oroshi.get_isbn(records[0]), ISBN2)

    def test_update_record(self):
        def get_not_inventoried_record(isbn):
            for record in self._instance.find_records_by_isbn(isbn):
                if not record.inventoried:
                    return record

        nir = get_not_inventoried_record(ISBN1)
        record = oroshi.BookRecord(nir.record_id, nir.status, nir.title,
                                   nir.isbn10, nir.isbn13, nir.exists, True)
        self._instance.update_record(record)

        record = self._instance.get_record(nir.record_id)
        self.assertTrue(record.inventoried)


class OroshiTest(unittest.TestCase):
    def setUp(self):
        records = [FAKE_RECORD1, FAKE_RECORD2, FAKE_RECORD31]
        self._bookstore = FakeBookstore(records)
        self._stdin = io.StringIO()
        self._stdout = io.StringIO()
        self._instance = oroshi.Oroshi(
            self._bookstore, stdin=self._stdin, stdout=self._stdout)

    def test_scan_one(self):
        self._stdin.write('{}\nEND_OF_BARCODE\ndo\n'.format(ISBN1))
        self._stdin.seek(0)
        self._instance.run()
        r = self._bookstore.get_record(2)
        self.assertTrue(r.inventoried)
