import unittest
from main import *
import numpy

class TestBTree(unittest.TestCase):
    def setUp(self):
        """Inicjalizacja drzewa przed każdym testem."""
        self.t = 2  # Minimalny stopień B-drzewa
        self.btree = BTree(self.t)

    def test_empty_tree(self):
        """Testuje, czy drzewo jest początkowo puste."""
        self.assertEqual(self.btree.traverse(), [])

    def test_single_insert(self):
        """Testuje wstawienie jednego klucza do drzewa."""
        self.btree.insert(10, "value10")
        self.assertEqual(self.btree.traverse(), [10])
        node, status = self.btree.search(10)
        self.assertEqual(status, "found")
        self.assertEqual(node.keys, [10])

    def test_multiple_inserts(self):
        """Testuje wstawienie kilku kluczy do drzewa."""
        keys = [20, 10, 30, 25, 35]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        self.assertEqual(self.btree.traverse(), sorted(keys))

    def test_split_root(self):
        """Testuje podział korzenia."""
        keys = [10, 20, 5, 15, 25]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        # Sprawdź, czy korzeń został podzielony
        self.assertEqual(len(self.btree.root.keys), 1)  # Korzeń ma 1 klucz po podziale
        self.assertEqual(self.btree.root.keys[0], 15)  # Środkowy klucz powinien być korzeniem
        # Sprawdź strukturę drzewa po podziale
        left_child = self.btree.root.children[0]
        right_child = self.btree.root.children[1]
        self.assertEqual(left_child.keys, [5, 10])
        self.assertEqual(right_child.keys, [20, 25])

    def test_search_existing_key(self):
        """Testuje wyszukiwanie istniejącego klucza."""
        keys = [50, 30, 70, 10, 40]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        node, status = self.btree.search(30)
        self.assertEqual(status, "found")
        self.assertEqual(node.keys, [10, 30])  # Klucz 30 znajduje się w liściu z kluczami [30, 40]

    def test_search_nonexistent_key(self):
        """Testuje wyszukiwanie klucza, który nie istnieje w drzewie."""
        keys = [10, 20, 30, 40, 50]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        node, status = self.btree.search(35)
        self.assertEqual(status, "not found")
        self.assertEqual(node.keys, [40, 50])  # Klucz 35 nie istnieje, ale znajduje się w przedziale [30, 40]

    def test_tree_height_after_inserts(self):
        """Testuje wysokość drzewa po wielu wstawieniach."""
        keys = [50, 30, 70, 10, 40, 60, 80]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        # Po wstawieniu tych kluczy drzewo powinno mieć 2 poziomy
        self.assertEqual(len(self.btree.root.children), 3)  # Korzeń ma dwóch potomków

    def test_compensation(self):
        """Testuje mechanizm kompensacji między rodzeństwem."""
        keys = [10, 20, 30, 40, 50, 60]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        # Usunięcie sprawi, że węzeł może wymagać kompensacji (niezaimplementowane usuwanie, ale symulacja testu kompensacji)
        left, right = BTreeNode.get_node_sibling(self.btree.root.children[0])
        middle_index = self.btree.root.children.index(self.btree.root.children[0])
        compensated = BTreeNode.compensation_insert(left, right, self.btree.root.children[0], middle_index)
        self.assertTrue(compensated)  # Powinna być możliwa kompensacja

    def test_traverse(self):
        """Testuje przeszukiwanie drzewa w kolejności rosnącej."""
        keys = [7, 3, 1, 5, 9, 8, 6]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        self.assertEqual(self.btree.traverse(), sorted(keys))

    def test_split_and_traverse(self):
        """Testuje wstawienia powodujące podział oraz przeszukiwanie."""
        keys = [50, 30, 70, 10, 40, 60, 80, 90, 20, 25]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        self.assertEqual(self.btree.traverse(), sorted(keys))

    def test_tree_display(self):
        """Testuje wyświetlanie drzewa."""
        keys = [15, 5, 20, 3, 7, 17, 25]
        for key in keys:
            self.btree.insert(key, f"value{key}")
        self.btree.display()
        # Brak automatycznego sprawdzania, ale wizualna weryfikacja wyświetlenia drzewa

    def test_large_data_insert(self):
        keys = numpy.random.choice(1000000, size=1000000).tolist()
        keys = numpy.unique(keys)
        for key in keys:
            self.btree.insert(key, f"value{key}")
        self.assertEqual(self.btree.traverse(), sorted(keys))

    def test_large_data_insert_and_delete(self):
        self.t = 4  # Minimalny stopień B-drzewa
        self.btree = BTree(self.t)

        keys = numpy.random.choice(1000000, size=10000).tolist()
        keys = numpy.unique(keys)
        for key in keys:
            self.btree.insert(key, f"value{key}")
        for key in keys:
            self.btree.delete(key)
        self.assertEqual(self.btree.traverse(), [])

if __name__ == "__main__":
    unittest.main()
