from btree import *


def parse_file(file_path, btree):
    with open(file_path, 'r') as file:
        offset = file.tell()
        line = file.readline()
        while line:
            flag, key, _ = line.strip().split(':')
            key = int(key)
            if flag == '1':
                btree.insert(key, offset, loading_file=True)
            offset = file.tell()
            line = file.readline()
    return btree


if __name__ == '__main__':
    tree = BTree(t=4)
    filepath = f"data/{input("Enter file name: ")}"
    tree.main_file_path = filepath
    new_tree = parse_file(filepath, tree)
    print("File parsed successfully.")
    while True:
        option = input("Choose an option:\n"
                       "1. Insert\n"
                       "2. Delete\n"
                       "3. Search\n"
                       "4. Display tree\n"
                       "5. Update value\n"
                       "6. Exit\n"
                       "Enter your choice: ")
        match option:
            case "1":
                key = int(input("Enter key: "))
                value = input("Enter value: ")
                tree.insert(key, value)
                print(f"Inserted ({key}, {value})")
            case "2":
                key = int(input("Enter key: "))
                tree.delete(key)
                print(f"Deleted ({key})")
            case "3":
                key = int(input("Enter key: "))
                found_node, status = tree.search(key)
                if status == "found":
                    print(f"Found ({key}, {found_node.children[found_node.keys.index(key)]})")
                else:
                    print(f"Not found {key} in tree.")
            case "4":
                option = input("Display values? (y/n): ")
                tree.display(offsets=True if option == "y" else False)
            case "5":
                key = int(input("Enter key: "))
                value = input("Enter new value: ")
                found_node, status = tree.search(key)
                if status == "found":
                    found_node[key] = value
                    print(f"Updated ({key}, {found_node.children[found_node.keys.index(key)]})")
                else:
                    print(f"Not found {key} in tree.")
            case "6":
                exit(0)

        input("Press Enter to continue...")
