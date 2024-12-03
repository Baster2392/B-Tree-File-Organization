from btree import *


def parse_file(file_path, btree):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                key, value = line.strip().split(':')
                key = int(key)
                value = list(map(int, value.strip(' []').split(',')))
                btree.insert(key, value)
        return btree
    except Exception as e:
        print(f"Błąd podczas parsowania pliku: {e}")
        return None


if __name__ == '__main__':
    tree = BTree(t=4)
    while True:
        option = input("Choose an option:\n"
                       "1. Insert\n"
                       "2. Delete\n"
                       "3. Search\n"
                       "4. Display tree\n"
                       "5. Update value\n"
                       "6. Reorganise\n"
                       "7. Read file\n"
                       "8. Exit\n"
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
                tree.display(values=True if option == "y" else False)
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
                pass
            case "7":
                new_tree = parse_file(f"data/{input("Enter file name: ")}", tree)
                print("File parsed successfully.")
            case "8":
                exit(0)

        input("Press Enter to continue...")
