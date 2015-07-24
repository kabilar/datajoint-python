from operator import itemgetter, attrgetter
import itertools
from nose.tools import assert_true
from numpy.testing import assert_array_equal, assert_equal
import numpy as np

from . import schema
import datajoint as dj


class TestFetch:
    def __init__(self):
        self.subject = schema.Subject()
        self.lang = schema.Language()

    def test_getitem(self):
        """Testing Fetch.__getitem__"""

        np.testing.assert_array_equal(sorted(self.subject.project().fetch(), key=itemgetter(0)),
                                      sorted(self.subject.fetch[dj.key], key=itemgetter(0)),
                                      'Primary key is not returned correctly')

        tmp = self.subject.fetch(order_by=['subject_id'])

        for column, field in zip(self.subject.fetch[:], [e[0] for e in tmp.dtype.descr]):
            np.testing.assert_array_equal(sorted(tmp[field]), sorted(column), 'slice : does not work correctly')

        subject_notes, key, real_id = self.subject.fetch['subject_notes', dj.key, 'real_id']
        #
        np.testing.assert_array_equal(sorted(subject_notes), sorted(tmp['subject_notes']))
        np.testing.assert_array_equal(sorted(real_id), sorted(tmp['real_id']))
        np.testing.assert_array_equal(sorted(key, key=itemgetter(0)),
                                      sorted(self.subject.project().fetch(), key=itemgetter(0)))

        for column, field in zip(self.subject.fetch['subject_id'::2], [e[0] for e in tmp.dtype.descr][::2]):
            np.testing.assert_array_equal(sorted(tmp[field]), sorted(column), 'slice : does not work correctly')

    def test_order_by(self):
        """Tests order_by sorting order"""
        langs = schema.Language.contents

        for ord_name, ord_lang in itertools.product(*2 * [['ASC', 'DESC']]):
            cur = self.lang.fetch.order_by('name=' + ord_name, 'language=' + ord_lang)()
            langs.sort(key=itemgetter(2), reverse=ord_lang == 'DESC')
            langs.sort(key=itemgetter(1), reverse=ord_name == 'DESC')
            for c, l in zip(cur, langs):
                assert_true(np.all(cc == ll for cc, ll in zip(c, l)), 'Sorting order is different')

    def test_order_by_default(self):
        """Tests order_by sorting order with defaults"""
        langs = schema.Language.contents

        cur = self.lang.fetch.order_by('language', 'name=DESC')()
        langs.sort(key=itemgetter(1), reverse=True)
        langs.sort(key=itemgetter(2), reverse=False)

        for c, l in zip(cur, langs):
            assert_true(np.all([cc == ll for cc, ll in zip(c, l)]), 'Sorting order is different')

    def test_order_by_direct(self):
        """Tests order_by sorting order passing it to __call__"""
        langs = schema.Language.contents

        cur = self.lang.fetch(order_by=['language', 'name=DESC'])
        langs.sort(key=itemgetter(1), reverse=True)
        langs.sort(key=itemgetter(2), reverse=False)
        for c, l in zip(cur, langs):
            assert_true(np.all([cc == ll for cc, ll in zip(c, l)]), 'Sorting order is different')

    def test_limit_to(self):
        """Test the limit_to function """
        langs = schema.Language.contents

        cur = self.lang.fetch.limit_to(4)(order_by=['language', 'name=DESC'])
        langs.sort(key=itemgetter(1), reverse=True)
        langs.sort(key=itemgetter(2), reverse=False)
        assert_equal(len(cur), 4, 'Length is not correct')
        for c, l in list(zip(cur, langs))[:4]:
            assert_true(np.all([cc == ll for cc, ll in zip(c, l)]), 'Sorting order is different')

    def test_from_to(self):
        """Test the from_to function """
        langs = schema.Language.contents

        cur = self.lang.fetch.from_to(2, 6)(order_by=['language', 'name=DESC'])
        langs.sort(key=itemgetter(1), reverse=True)
        langs.sort(key=itemgetter(2), reverse=False)
        assert_equal(len(cur), 4, 'Length is not correct')
        for c, l in list(zip(cur, langs[2:6])):
            assert_true(np.all([cc == ll for cc, ll in zip(c, l)]), 'Sorting order is different')

    def test_iter(self):
        """Test iterator"""
        langs = schema.Language.contents

        cur = self.lang.fetch.order_by('language', 'name=DESC')
        langs.sort(key=itemgetter(1), reverse=True)
        langs.sort(key=itemgetter(2), reverse=False)
        for (_, name, lang), (_, tname, tlang) in list(zip(cur, langs)):
            assert_true(name == tname and lang == tlang, 'Values are not the same')

    def test_keys(self):
        """test key iterator"""
        langs = schema.Language.contents
        langs.sort(key=itemgetter(1), reverse=True)
        langs.sort(key=itemgetter(2), reverse=False)

        cur = self.lang.fetch.order_by('language', 'name=DESC')['entry_id']
        cur2 = [e['entry_id'] for e in self.lang.fetch.order_by('language', 'name=DESC').keys()]

        keys, _, _ = list(zip(*langs))
        for k, c, c2 in zip(keys, cur, cur2):
            assert_true(k == c == c2, 'Values are not the same')

    def test_fetch1(self):
        key = {'entry_id': 0}
        true = schema.Language.contents[0]

        dat = (self.lang & key).fetch1()
        for k, (ke, c) in zip(true, dat.items()):
            assert_true(k == c == (self.lang & key).fetch1[ke], 'Values are not the same')

    def test_copy(self):
        """Test whether modifications copy the object"""
        f = self.lang.fetch
        f2 = f.order_by('name')
        assert_true(f.behavior['order_by'] is None and len(f2.behavior['order_by']) == 1, 'Object was not copied')

    def test_overwrite(self):
        """Test whether order_by overwrites duplicates"""
        f = self.lang.fetch.order_by('name =   DeSc ')
        f2 = f.order_by('name')
        assert_true(f2.behavior['order_by'] == ['name'], 'order_by attribute was not overwritten')