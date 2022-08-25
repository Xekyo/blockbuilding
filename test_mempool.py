import unittest
from mempool import Mempool
from transaction import Transaction

class TestMempool(unittest.TestCase):


    def setUp(self):
        self.testDict = {
            "123": Transaction("123", 100, 100, [], ["abc"]),
            "abc": Transaction("abc", 100, 100, ["123"], []),
            "nop": Transaction("nop", 1000, 100, [], ["qrs"]),  # medium feerate
            "qrs": Transaction("qrs", 10000, 100, ["nop"], ["tuv"]),  # high feerate
            "tuv": Transaction("tuv", 100, 100, ["qrs"], []),  # low feerate
            "xyz": Transaction("xyz", 10, 10, [], [])
        }


    def test_parse_from_TXT(self):
        mempool = Mempool()
        mempool.fromTXT("data/mempoolTXT")
        txids = [
            "01123eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "b5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "8a2ba899956359eb278f6daffc8ae0f5dfb631a67dbfe57687f665b20bcf063e"
        ]
        keys = mempool.getTxs().keys()
        for txid in txids:
            self.assertEqual(True, txid in keys)


    def get_mempool_json(self):
        mempool = Mempool()
        mempool.fromJSON("data/mini-mempool.json")
        return mempool


    def test_parse_from_JSON(self):
        expectedTxids = [
            "01123eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "a5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "b5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "9a9b73b2a6ea86a495662d5e90cda9fadbf70c470231dff6b4f9286707f30812",
            "154ff366005101ed97c044782d82e3abf44073968bd0db21c9f5b27296aa3de2",
            "6a2ba899956359eb278f6daffc8ae0f5dfb631a67dbfe57687f665b20bcf063e",
            "88b75cf4ef99814d1f3f2245800b93aa400e92cfeae763f1334f3059232204a7",
            "8a2ba899956359eb278f6daffc8ae0f5dfb631a67dbfe57687f665b20bcf063e"
        ]
        expectedTxids.sort()

        mempool = self.get_mempool_json()
        txids = list(mempool.getTxs().keys())
        txids.sort()
        self.assertEqual(expectedTxids, txids)


    def test_backfill_relatives(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        self.assertIn('nop', mempool.txs['tuv'].ancestors)
        self.assertNotIn('nop', mempool.txs['tuv'].parents)
        self.assertIn('tuv', mempool.txs['nop'].descendants)
        self.assertNotIn('tuv', mempool.txs['nop'].children)


    def test_mempool_fee(self):
        txs = self.get_mempool_json().getTxs()
        self.assertEqual(
            13120,
            txs["88b75cf4ef99814d1f3f2245800b93aa400e92cfeae763f1334f3059232204a7"].fee
        )


    def test_drop_tx(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        self.assertIn('qrs', mempool.txs.keys())
        mempool.dropTx('qrs')
        self.assertNotIn('qrs', mempool.txs.keys())
        self.assertNotIn('qrs', mempool.txs['nop'].children)
        self.assertIn('qrs', mempool.txs['tuv'].parents)


    def test_drop_tx_called_twice_throws(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        self.assertIn('qrs', mempool.txs.keys())
        mempool.dropTx('qrs')
        self.assertNotIn('qrs', mempool.txs.keys())
        with self.assertRaises(KeyError):
            mempool.dropTx('qrs')


    def test_remove_confirmed_tx(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        self.assertIn('qrs', mempool.txs.keys())
        mempool.removeConfirmedTx('qrs')
        self.assertNotIn('qrs', mempool.txs.keys())
        with self.assertRaises(KeyError):
            mempool.removeConfirmedTx('qrs')

if __name__ == '__main__':
    unittest.main()
