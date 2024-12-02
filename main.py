class BTreeNode:
    def __init__(self, t, ancestor=None, is_leaf=True):
        self.t = t  # Max number of keys in one node
        self.keys = []
        self.data = []
        self.children = []
        self.ancestor = ancestor
        self.is_leaf = is_leaf

    @staticmethod
    def get_node_sibling(node):
        if node.ancestor is None:
            return None, None
        if len(node.ancestor.children) == 1:
            return None, None

        this_index = node.ancestor.children.index(node)
        if this_index == 0:
            return None, node.ancestor.children[this_index + 1]
        elif this_index == len(node.ancestor.children) - 1:
            return node.ancestor.children[this_index - 1], None
        else:
            return node.ancestor.children[this_index - 1], node.ancestor.children[this_index + 1]

    @staticmethod
    def compensation_insert(left, right, node, middle_index):
        if left is None and right is None:
            return False
        if right is not None:
            if len(right.keys) < right.t:
                BTreeNode.compensate(node, right, node.ancestor, middle_index + 1)
                return True
        if left is not None:
            if len(left.keys) < left.t:
                BTreeNode.compensate(left, node, node.ancestor, middle_index)
                return True
        return False

    @staticmethod
    def compensation_delete(left, right, node, middle_index):
        if left is None and right is None:
            return False
        if right is not None and len(right.keys) > right.t // 2 and len(right.keys) + len(node.keys) > right.t:
            BTreeNode.compensate(node, right, node.ancestor, middle_index + 1, operation="delete")
            return True
        if left is not None and len(left.keys) > left.t // 2 and len(left.keys) + len(node.keys) > left.t:
            BTreeNode.compensate(left, node, node.ancestor, middle_index, operation="delete")
            return True
        return False

    @staticmethod
    def compensate(left, right, ancestor, middle_index, operation="insert"):
        keys = []
        data = []
        children = []

        split_index = left.t if operation == "insert" else left.t // 2
        if operation == "delete" and split_index % 2 == 1:
            split_index += 1

        # add items in right order
        keys.extend(left.keys)
        data.extend(left.data)
        children.extend(left.children)
        keys.append(ancestor.keys[middle_index])
        data.append(ancestor.data[middle_index])
        keys.extend(right.keys)
        data.extend(right.data)
        children.extend(right.children)

        # fill left page
        left.keys = keys[:split_index]
        left.data = data[:split_index]
        left.children = children[:split_index + 1]

        # fill middle index
        ancestor.keys[middle_index] = keys[split_index]
        ancestor.data[middle_index] = data[split_index]

        # fill right page
        right.keys = keys[split_index + 1:]
        right.data = data[split_index + 1:]
        right.children = children[split_index + 1:]

    @staticmethod
    def split(node, btree):
        # Sprawdź, czy węzeł wymaga podziału
        if len(node.keys) <= node.t:
            return

        # Utwórz nowy węzeł po podziale
        new_node = BTreeNode(node.t, ancestor=node.ancestor, is_leaf=node.is_leaf)

        # Znajdź środkowy indeks i klucz
        middle_index = len(node.keys) // 2
        middle_key = node.keys[middle_index]
        middle_data = node.data[middle_index]

        # Przenieś prawe klucze i dane do nowego węzła
        new_node.keys = node.keys[middle_index + 1:]
        new_node.data = node.data[middle_index + 1:]

        # Jeśli węzeł nie jest liściem, przenieś odpowiednie dzieci
        if not node.is_leaf:
            new_node.children = node.children[middle_index + 1:]
            for child in new_node.children:
                child.ancestor = new_node

        # Skróć obecny węzeł do kluczy i danych przed środkowym kluczem
        node.keys = node.keys[:middle_index]
        node.data = node.data[:middle_index]
        if not node.is_leaf:
            node.children = node.children[:middle_index + 1]

        # Jeśli węzeł nie ma nadrzędnego, utwórz nowy korzeń
        if node.ancestor is None:
            new_root = BTreeNode(node.t, is_leaf=False)
            new_root.keys = [middle_key]
            new_root.data = [middle_data]
            new_root.children = [node, new_node]
            node.ancestor = new_root
            new_node.ancestor = new_root
            btree.root = new_root
            return

        # Wstaw środkowy klucz do węzła nadrzędnego
        ancestor = node.ancestor
        insert_position = 0
        while insert_position < len(ancestor.keys) and ancestor.keys[insert_position] < middle_key:
            insert_position += 1

        ancestor.keys.insert(insert_position, middle_key)
        ancestor.data.insert(insert_position, middle_data)
        ancestor.children.insert(insert_position + 1, new_node)

        # Ustaw wskaźnik nadrzędny dla nowego węzła
        new_node.ancestor = ancestor

        # Rekurencyjnie podziel węzeł nadrzędny, jeśli to konieczne
        BTreeNode.split(ancestor, btree)

    @staticmethod
    def merge(left, right, ancestor, middle_index, btree):
        """
        Łączy dwa węzły: left i right. Klucz z ancestor[middle_index] jest przenoszony do węzła lewego.
        """
        if left is None or right is None or ancestor is None:
            return False  # Nie można wykonać merge, jeśli brakuje elementów

        # Przenieś klucz z ancestor do lewego węzła
        left.keys.append(ancestor.keys[middle_index])
        left.data.append(ancestor.data[middle_index])

        # Dodaj klucze i dzieci z prawego węzła do lewego
        left.keys.extend(right.keys)
        left.data.extend(right.data)
        left.children.extend(right.children)

        # Ustaw ancestor dla dzieci prawego węzła na left
        for child in right.children:
            child.ancestor = left

        # Usuń klucz i dziecko z ancestor
        ancestor.keys.pop(middle_index)
        ancestor.data.pop(middle_index)
        ancestor.children.remove(right)

        # Jeśli ancestor stał się pusty, ustaw left jako nowy korzeń drzewa
        if len(ancestor.keys) == 0 and ancestor == btree.root:
            btree.root = left
            return True

        return False  # Merge zakończony, ale korzeń się nie zmienił

    def __repr__(self):
        return f"Keys: {self.keys}, Values: {self.data}, IsLeaf: {self.is_leaf}, Children: {len(self.children)}"


class BTree:
    def __init__(self, t):
        self.root = BTreeNode(t)
        self.t = t
        self.read_write_operations = 0

    def traverse(self):
        """Zwraca listę wszystkich kluczy w drzewie w kolejności"""
        result = []
        self._traverse_helper(self.root, result)
        return result

    def _traverse_helper(self, node, result):
        i = 0
        while i < len(node.keys):
            # Odwiedź poddrzewo przed aktualnym kluczem
            if not node.is_leaf:
                self._traverse_helper(node.children[i], result)
            # Dodaj aktualny klucz
            result.append(node.keys[i])
            i += 1
        # Odwiedź ostatnie poddrzewo
        if not node.is_leaf:
            self._traverse_helper(node.children[i], result)

    def search(self, k, node=None):
        """Wyszukiwanie klucza k w B-drzewie"""
        self.read_write_operations += 1  # Symulacja odczytu strony dyskowej

        if node is None:
            node = self.root

        i = 0
        while i < len(node.keys) and k > node.keys[i]:
            i += 1

        if i < len(node.keys) and node.keys[i] == k:
            return node, "found"

        if node.is_leaf:
            return node, "not found"

        return self.search(k, node.children[i])

    def insert(self, key, value):
        node, status = self.search(key)
        if status == "found":
            return

        if node is None:
            node = self.root

        # insert new key if node is not full
        if len(node.keys) <= self.t:
            self.insert_into_node(key, value, node)

        if len(node.keys) > self.t:
            # overflow
            # try compensation
            left, right = BTreeNode.get_node_sibling(node)
            if node.ancestor is not None:
                if BTreeNode.compensation_insert(left, right, node, node.ancestor.children.index(node) - 1):
                    return
            # compensation impossible
            # make a split
            BTreeNode.split(node, self)

    def delete(self, key):
        node, status = self.search(key)
        if status == "not found":
            print("Not found")
            return
        key_index = node.keys.index(key)
        if not node.is_leaf:
            neighbour_key, neighbour_node, type = self.find_predecessor(key)
            if neighbour_key is None:
                neighbour_key, neighbour_node, type = self.find_successor(key)
            if neighbour_key is None:
                return
            # replace deleting value with neighbor
            neighbour_index = len(neighbour_node.keys) - 1 if type == "predecessor" else 0
            neighbour_value = neighbour_node.data[neighbour_index]
            node.keys[key_index] = neighbour_key
            node.data[key_index] = neighbour_value
            # remove predecessor from its old node
            neighbour_node.keys.remove(neighbour_key)
            neighbour_node.data.remove(neighbour_value)
            self.compensate_and_merge(neighbour_node)
        else:
            node.keys.remove(key)
            node.data.remove(node.data[key_index])
            self.compensate_and_merge(node)

    def compensate_and_merge(self, node):
        if node == self.root:
            return
        if node.ancestor is None:
            return
        if len(node.keys) <= self.t // 2:
            # print("Compensating/merging...")
            left, right = BTreeNode.get_node_sibling(node)
            middle_index = node.ancestor.children.index(node) - 1
            if BTreeNode.compensation_delete(left, right, node, middle_index):
                return
            if left is not None and len(left.keys) + len(node.keys) < self.t and len(left.keys) >= self.t // 2:
                middle_index = node.ancestor.children.index(left) - 1
                BTreeNode.merge(left, node, node.ancestor, middle_index + 1, self)
            elif right is not None and len(right.keys) + len(node.keys) < self.t and len(right.keys) >= self.t // 2:
                middle_index = node.ancestor.children.index(right) - 1
                BTreeNode.merge(node, right, node.ancestor, middle_index, self)
            # print("After compensation/merge...")
            # self.display()
            self.compensate_and_merge(node.ancestor)

    def find_predecessor(self, key):
        node, status = self.search(key)
        if status == "not found":
            return None, None, None

        # Znajdź indeks klucza w węźle
        i = node.keys.index(key)

        if not node.is_leaf:
            # Przechodzimy do prawego poddrzewa klucza (lewa strona węzła)
            predecessor_node = node.children[i]
            while not predecessor_node.is_leaf:
                predecessor_node = predecessor_node.children[-1]
            if len(predecessor_node.keys) == 0:
                return None, None, None
            return predecessor_node.keys[-1], predecessor_node, "predecessor"
        else:
            # Szukamy w węźle nadrzędnym, jeśli nie ma dzieci
            while node.ancestor is not None:
                ancestor = node.ancestor
                index_in_parent = ancestor.children.index(node)
                if index_in_parent > 0:
                    return ancestor.keys[index_in_parent - 1], ancestor, "predecessor"
                node = ancestor

            # Nie znaleziono poprzednika (klucz jest najmniejszy w drzewie)
            return None, None, None

    def find_successor(self, key):
        node, status = self.search(key)
        if status == "not found":
            return None, None, None  # Klucz nie istnieje

        # Znajdź indeks klucza w węźle
        i = node.keys.index(key)

        if not node.is_leaf:
            # Przechodzimy do lewego poddrzewa klucza (prawa strona węzła)
            successor_node = node.children[i + 1]
            while not successor_node.is_leaf:
                successor_node = successor_node.children[0]
            if len(successor_node.keys) == 0:
                return None, None, None
            return successor_node.keys[0], successor_node, "successor"
        else:
            # Szukamy w węźle nadrzędnym, jeśli nie ma dzieci
            while node.ancestor is not None:
                ancestor = node.ancestor
                index_in_parent = ancestor.children.index(node)
                if index_in_parent < len(ancestor.keys):
                    return ancestor.keys[index_in_parent], ancestor, "successor"
                node = ancestor

            # Nie znaleziono następcy (klucz jest największy w drzewie)
            return None, None, None

    def insert_into_node(self, key, value, node):
        i = 0
        while i < len(node.keys):
            if key <= node.keys[i]:
                node.keys.insert(i, key)
                node.data.insert(i, value)
                return
            i += 1

        node.keys.insert(i, key)
        node.data.insert(i, value)

    def reorganize(self):
        """Operacja reorganizacji drzewa, jeśli wymagana"""
        print("Reorganizacja drzewa... (niezrealizowana, demonstracja mechanizmu).")

    def display(self, node=None, level=0):
        """Wyświetla zawartość drzewa B w czytelnej formie"""
        if node is None:
            node = self.root

        print("-" * level + str(node.keys) + str(node.data) + " Children: " + str(len(node.children)))
        for child in node.children:
            self.display(child, level + 1)


if __name__ == "__main__":
    b_tree = BTree(t=3)

    records1 = [10, 12, 20, 5, 6, 13, 30, 7, 34, 67, 34, 98, 45, 1, 35, 44, 47, 51, 69, 70,
                18, 23, 102, 61, 22, 80, 81, 82, 55, 66, 11, 0, 150, -1, -2, -3, -4, 9, 77, 105, 107, 106, -10,
                -11, -12, -13, -14, -15, -16, -17, -18, -19, -20, 200, 201, 202, 203, 204, 205, 206, 207, 208, 46, 43]
    records2 = [10, 20, 15, 2, 30, 12, 23, 22, 55, 9, 32, 11, 15, 111, 102, 97, 18, 27]

    i = 0

    for record in records1:
        print(f"Wstawianie (key: {record}, value: {i}):")
        # inp = input("Press key...")
        b_tree.insert(record, i)
        i += 1
        print(f"Po wstawieniu (key: {record}, value: {i}):")
        b_tree.display()
        print(f"Operacje odczytu/zapisu: {b_tree.read_write_operations}")

    print("Przegląd całego drzewa:")
    print(b_tree.traverse())
    inp = input("Press key...")

    for record in records1:
        # key = input("Klucz do usuniecia: ")
        b_tree.delete(record)
        print(f"Po usunieciu {record}:")
        b_tree.display()

    print("Przegląd całego drzewa:")
    print(b_tree.traverse())
