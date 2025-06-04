# Unit and integration tests for PCBDetectApp and modules
import unittest
from pcb_detect.config_manager import ConfigManager
from pcb_detect.board_manager import BoardManager
from pcb_detect.batch_manager import BatchManager

class TestConfigManager(unittest.TestCase):
    def test_defaults(self):
        cm = ConfigManager()
        self.assertIn('confidence', cm.config)
        self.assertIn('delay', cm.config)

class TestBoardManager(unittest.TestCase):
    def test_add_edit_delete_set(self):
        bm = BoardManager()
        bm.add_set('TestSet', {'Resistor': 1})
        self.assertIn('TestSet', bm.sets)
        bm.edit_set('TestSet', {'Resistor': 2})
        self.assertEqual(bm.sets['TestSet']['Resistor'], 2)
        bm.delete_set('TestSet')
        self.assertNotIn('TestSet', bm.sets)

class TestBatchManager(unittest.TestCase):
    def test_create_delete_batch(self):
        bm = BatchManager()
        name = bm.create_batch('UnitTestBatch')
        self.assertIn(name, bm.batches)
        bm.delete_batch(name)
        self.assertNotIn(name, bm.batches)

if __name__ == '__main__':
    unittest.main()
