import os

BLOCK_SIZE = 32


class BTreeNode:
    def __init__(self, t, index, ancestor=None, is_leaf=True):
        self.t = t  # Max number of keys in one node
        self.index = index
        self.keys = []
        self.offsets = []
        self.children = []
        self.ancestor = ancestor
        self.is_leaf = is_leaf

    @staticmethod
    def get_node_sibling(node, ancestor_node, btree):
        if ancestor_node is None:
            return None, None
        if len(ancestor_node.children) == 1:
            return None, None

        this_index = ancestor_node.children.index(node.index)
        if this_index == 0:
            return None, BTree.read_node_from_drive(btree, ancestor_node.children[this_index + 1])
        elif this_index == len(ancestor_node.children) - 1:
            return BTree.read_node_from_drive(btree, ancestor_node.children[this_index - 1]), None
        else:
            return BTree.read_node_from_drive(btree, ancestor_node.children[this_index - 1]), BTree.read_node_from_drive(btree, ancestor_node.children[this_index + 1])

    @staticmethod
    def compensation_insert(left, right, node, ancestor_node, middle_index, btree):
        if left is None and right is None:
            return False
        if right is not None:
            if len(right.keys) < right.t:
                BTreeNode.compensate(node, right, ancestor_node, middle_index + 1, btree, operation="insert")
                return True
        if left is not None:
            if len(left.keys) < left.t:
                BTreeNode.compensate(left, node, ancestor_node, middle_index, btree, operation="insert")
                return True
        return False

    @staticmethod
    def compensation_delete(left, right, node, ancestor_node, middle_index, btree):
        if left is None and right is None:
            return False
        if right is not None and len(right.keys) > right.t // 2 and len(right.keys) + len(node.keys) > right.t:
            BTreeNode.compensate(node, right, ancestor_node, middle_index + 1, btree, operation="delete")
            return True
        if left is not None and len(left.keys) > left.t // 2 and len(left.keys) + len(node.keys) > left.t:
            BTreeNode.compensate(left, node, ancestor_node, middle_index, btree, operation="delete")
            return True
        return False

    @staticmethod
    def compensate(left, right, ancestor, middle_index, btree, operation="insert"):
        keys = []
        offsets = []
        children = []

        split_index = left.t if operation == "insert" else left.t // 2
        if operation == "delete" and split_index % 2 == 1:
            split_index += 1

        # add items in right order
        keys.extend(left.keys)
        offsets.extend(left.offsets)
        children.extend(left.children)
        keys.append(ancestor.keys[middle_index])
        offsets.append(ancestor.offsets[middle_index])
        keys.extend(right.keys)
        offsets.extend(right.offsets)
        children.extend(right.children)

        # fill left page
        left.keys = keys[:split_index]
        left.offsets = offsets[:split_index]
        left.children = children[:split_index + 1]

        # fill middle index
        ancestor.keys[middle_index] = keys[split_index]
        ancestor.offsets[middle_index] = offsets[split_index]

        # fill right page
        right.keys = keys[split_index + 1:]
        right.offsets = offsets[split_index + 1:]
        right.children = children[split_index + 1:]

        # save modified modes
        BTree.write_node_to_drive(btree, left)
        BTree.write_node_to_drive(btree, right)
        BTree.write_node_to_drive(btree, ancestor)

    @staticmethod
    def split(node, btree):
        # check if node has to be divided
        if len(node.keys) <= node.t:
            return

        # Create a new node
        new_node = BTreeNode(node.t, btree.index_for_node, ancestor=node.ancestor, is_leaf=node.is_leaf)
        btree.index_for_node += 1

        # get middle item
        middle_index = len(node.keys) // 2
        middle_key = node.keys[middle_index]
        middle_offset = node.offsets[middle_index]

        # move right items to new node
        new_node.keys = node.keys[middle_index + 1:]
        new_node.offsets = node.offsets[middle_index + 1:]

        # if node is not a leaf, move children to a new node
        if not node.is_leaf:
            new_node.children = node.children[middle_index + 1:]
            for child in new_node.children:
                child_node = btree.read_node_from_drive(child)
                child_node.ancestor = new_node.index
                btree.write_node_to_drive(child_node)

        # cut moved data
        node.keys = node.keys[:middle_index]
        node.offsets = node.offsets[:middle_index]
        if not node.is_leaf:
            node.children = node.children[:middle_index + 1]

        # create new root
        if node.ancestor is None:
            new_root = BTreeNode(node.t, btree.index_for_node, is_leaf=False)
            btree.index_for_node += 1
            new_root.keys = [middle_key]
            new_root.offsets = [middle_offset]
            new_root.children = [node.index, new_node.index]
            node.ancestor = new_root.index
            new_node.ancestor = new_root.index
            btree.root = new_root.index
            btree.write_node_to_drive(new_root)
            btree.write_node_to_drive(node)
            btree.write_node_to_drive(new_node)
            return

        # move middle key to ancestor node
        ancestor = btree.read_node_from_drive(node.ancestor)
        insert_position = 0
        while insert_position < len(ancestor.keys) and ancestor.keys[insert_position] < middle_key:
            insert_position += 1

        ancestor.keys.insert(insert_position, middle_key)
        ancestor.offsets.insert(insert_position, middle_offset)
        ancestor.children.insert(insert_position + 1, new_node.index)

        new_node.ancestor = ancestor.index
        btree.write_node_to_drive(node)
        btree.write_node_to_drive(new_node)
        btree.write_node_to_drive(ancestor)
        BTreeNode.split(ancestor, btree)

    @staticmethod
    def merge(left, right, ancestor, middle_index, btree):
        if left is None or right is None or ancestor is None:
            return

        # move key from ancestor to new node
        left.keys.append(ancestor.keys[middle_index])
        left.offsets.append(ancestor.offsets[middle_index])

        # add keys and children from right node to left node
        left.keys.extend(right.keys)
        left.offsets.extend(right.offsets)
        left.children.extend(right.children)

        # set ancestor node for children of right node to left
        for child in right.children:
            child_node = btree.read_node_from_drive(child)
            child_node.ancestor = left.index
            btree.write_node_to_drive(child_node)

        # delete key and children from ancestor
        ancestor.keys.pop(middle_index)
        ancestor.offsets.pop(middle_index)
        ancestor.children.remove(right.index)

        btree.write_node_to_drive(ancestor)
        btree.write_node_to_drive(left)
        btree.delete_node(right)

        if len(ancestor.keys) == 0 and ancestor.index == btree.root:
            btree.root = left.index

    def __repr__(self):
        return f"Keys: {self.keys}, Values: {self.offsets}, IsLeaf: {self.is_leaf}, Children: {len(self.children)}"


class BTree:
    def __init__(self, file=None, t=4):
        self.root = 0
        self.t = t
        self.main_file_path = file
        self.index_for_node = 0
        # counters
        self.write_operations = 0
        self.read_operations = 0
        # create first file
        root_node = BTreeNode(t, self.index_for_node, None, True)
        self.index_for_node += 1
        self.write_node_to_drive(root_node)

    def traverse(self):
        result = []
        self._traverse_helper(self.root, result)
        return result

    def _traverse_helper(self, node_index, result):
        node = self.read_node_from_drive(node_index)
        i = 0
        while i < len(node.keys):
            if not node.is_leaf:
                self._traverse_helper(node.children[i], result)
            result.append(node.keys[i])
            i += 1
        if not node.is_leaf:
            self._traverse_helper(node.children[i], result)

    def search(self, k, node_index=None):
        if node_index is None:
            node_index = self.root
        node = self.read_node_from_drive(node_index)
        i = 0
        while i < len(node.keys) and k > node.keys[i]:
            i += 1

        if i < len(node.keys) and node.keys[i] == k:
            return node, "found"

        if node.is_leaf:
            return node, "not found"

        return self.search(k, node.children[i])

    def insert(self, key, value, loading_file=False):
        node, status = self.search(key)
        if status == "found":
            return

        if node is None:
            node = self.read_node_from_drive(self.root)

        # insert new key if node is not full
        if len(node.keys) <= self.t:
            if not loading_file:
                value = self.insert_to_main_file(key, value)
            self.insert_into_node(key, value, node)

        if len(node.keys) > self.t:
            # overflow
            # try compensation
            ancestor_node = self.read_node_from_drive(node.ancestor)
            left, right = BTreeNode.get_node_sibling(node, ancestor_node, self)
            if ancestor_node is not None:
                if BTreeNode.compensation_insert(left, right, node, ancestor_node, ancestor_node.children.index(node.index) - 1, self):
                    return
            # compensation impossible
            # make a split
            BTreeNode.split(node, self)
        else:
            self.write_node_to_drive(node)

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
            # remove from main file
            self.delete_from_main_file(node.offsets[key_index])
            # replace deleting value with neighbor
            neighbour_index = len(neighbour_node.keys) - 1 if type == "predecessor" else 0
            neighbour_offset = neighbour_node.offsets[neighbour_index]
            node.keys[key_index] = neighbour_key
            node.offsets[key_index] = neighbour_offset
            # remove predecessor from its old node
            neighbour_node.keys.remove(neighbour_key)
            neighbour_node.offsets.remove(neighbour_offset)
            self.compensate_and_merge(neighbour_node)
        else:
            offset = int(node.offsets[key_index])
            node.keys.remove(key)
            node.offsets.remove(offset)
            # remove from main file
            self.delete_from_main_file(offset)
            self.compensate_and_merge(node)

    def compensate_and_merge(self, node):
        if node == self.root:
            return
        if node.ancestor is None:
            return
        if len(node.keys) <= self.t // 2:
            # print("Compensating/merging...")
            ancestor_node = self.read_node_from_drive(node.ancestor)
            left, right = BTreeNode.get_node_sibling(node, ancestor_node, self)
            middle_index = ancestor_node.children.index(node.index) - 1
            if BTreeNode.compensation_delete(left, right, node, ancestor_node, middle_index, self):
                return
            if left is not None and len(left.keys) + len(node.keys) < self.t:
                middle_index = ancestor_node.children.index(left.index) - 1
                BTreeNode.merge(left, node, ancestor_node, middle_index + 1, self)
            elif right is not None and len(right.keys) + len(node.keys) < self.t:
                middle_index = ancestor_node.children.index(right.index) - 1
                BTreeNode.merge(node, right, ancestor_node, middle_index, self)
            # print("After compensation/merge...")
            # self.display()
            self.compensate_and_merge(ancestor_node)

    def find_predecessor(self, key):
        node, status = self.search(key)
        if status == "not found":
            return None, None, None

        # Find the index of the key in the node
        i = node.keys.index(key)
        if not node.is_leaf:
            # Move to the right subtree of the key (left side of the node)
            predecessor_node = self.read_node_from_drive(node.children[i])
            while not predecessor_node.is_leaf:
                predecessor_node = self.read_node_from_drive(predecessor_node.children[-1])
            if len(predecessor_node.keys) == 0:
                return None, None, None
            return predecessor_node.keys[-1], predecessor_node, "predecessor"
        else:
            # Search in the parent node if there are no children
            while node.ancestor is not None:
                ancestor = self.read_node_from_drive(node.ancestor)
                index_in_parent = ancestor.children.index(node)
                if index_in_parent > 0:
                    return ancestor.keys[index_in_parent - 1], ancestor, "predecessor"
                node = ancestor

            # No predecessor found (key is the smallest in the tree)
            return None, None, None

    def find_successor(self, key):
        node, status = self.search(key)
        if status == "not found":
            return None, None, None  # Key does not exist

        # Find the index of the key in the node
        i = node.keys.index(key)
        if not node.is_leaf:
            # Move to the left subtree of the key (right side of the node)
            successor_node = self.read_node_from_drive(node.children[i + 1])
            while not successor_node.is_leaf:
                successor_node = self.read_node_from_drive(successor_node.children[0])
            if len(successor_node.keys) == 0:
                return None, None, None
            return successor_node.keys[0], successor_node, "successor"
        else:
            # Search in the parent node if there are no children
            while node.ancestor is not None:
                ancestor = self.read_node_from_drive(node.ancestor)
                index_in_parent = ancestor.children.index(node.index)
                if index_in_parent < len(ancestor.keys):
                    return ancestor.keys[index_in_parent], ancestor, "successor"
                node = ancestor
            # No successor found (key is the largest in the tree)
            return None, None, None

    @staticmethod
    def insert_into_node(key, offset, node):
        i = 0
        while i < len(node.keys):
            if key <= node.keys[i]:
                node.keys.insert(i, key)
                node.offsets.insert(i, offset)
                return
            i += 1

        node.keys.insert(i, key)
        node.offsets.insert(i, offset)

    def display(self, node=None, level=0, offsets=True):
        if node is None:
            node = self.read_node_from_drive(self.root)

        print("-" * level + str(node.keys) + (str(node.offsets) if offsets else "") + " Children: " + str(len(node.children)))
        for child in node.children:
            child_node = self.read_node_from_drive(child)
            self.display(child_node, level + 1, offsets)

    def read_from_main_file(self, offset):
        with open(self.main_file_path, 'r') as f:
            f.seek(offset)
            _, _, value = f.readline().strip().split(':')
            return value

    def insert_to_main_file(self, key, value):
        with open(self.main_file_path, 'a') as f:
            offset = f.tell()
            f.write("1: " + str(key) + ": " + str(value) + "\n")
        return offset

    def delete_from_main_file(self, value):
        with open(self.main_file_path, 'r+') as f:
            f.seek(value)
            line = f.readline()
            print(f"Original line: {line}")

            new_line = line.replace('1', '0', 1)
            print(f"Modified line: {new_line}")

            f.seek(value)
            f.write(new_line)

    def write_node_to_drive(self, node):
        with open(f"tree_structure/{node.index}.txt", "w") as f:
            f.write(str(node.t) + '\n')
            f.write(str(node.ancestor)+ '\n')
            f.write(str(node.is_leaf)+ '\n')
            f.write(str(node.keys)+ '\n')
            f.write(str(node.offsets)+ '\n')
            f.write(str(node.children)+ '\n')
        self.write_operations += 1


    def read_node_from_drive(self, node_index):
        if node_index is None:
            return None

        with open(f"tree_structure/{node_index}.txt", "r") as f:
            t = int(f.readline().strip())
            node = BTreeNode(t, node_index)
            anc = f.readline().strip()
            if anc == "None":
                node.ancestor = None
            else:
                node.ancestor = int(anc)
            node.is_leaf = True if f.readline().strip() == "True" else False
            line = f.readline().strip()
            node.keys = [] if line == "[]" else list(map(int, line.strip()[1:-1].split(',')))
            line = f.readline().strip()
            node.offsets = [] if line == "[]" else list(map(int, line.strip()[1:-1].split(',')))
            line = f.readline().strip()
            node.children = [] if line == "[]" else list(map(int, line.strip()[1:-1].split(',')))
            self.write_operations += 1
            return node

    @staticmethod
    def delete_node(node):
        os.remove(f"tree_structure/{node.index}.txt")
        del node


if __name__ == "__main__":
    b_tree = BTree(t=4)

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

    print("Przegląd całego drzewa:")
    print(b_tree.traverse())
    # inp = input("Press key...")

    for record in records1:
        key = int(input("Klucz do usuniecia: "))
        b_tree.delete(key)
        print(f"Po usunieciu {key}:")
        b_tree.display()

    print("Przegląd całego drzewa:")
    print(b_tree.traverse())
