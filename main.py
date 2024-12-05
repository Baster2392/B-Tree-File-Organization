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

def delete_node_files(tree):
    for index in range(tree.index_for_node):
        os.remove(f"tree_structure/{index}.txt")

def parse_command(command, tree):
    option = command[0]
    match option:
        case '1':
            _, key, value = command.strip().split(';')
            tree.insert(int(key), value)
            print(f"Inserted ({key}, {value})")
        case '2':
            _, key = command.strip().split(';')
            tree.delete(int(key))
            print(f"Deleted ({key})")
        case '3':
            _, key = command.strip().split(';')
            found_node, status = tree.search(int(key))
            if status == "found":
                print(f"Found ({key}, {tree.read_from_main_file(found_node.offsets[found_node.keys.index(int(key))])})")
            else:
                print(f"Not found {key} in tree.")
        case '4':
            tree.display(offsets=False)
        case '5':
            _, key, value = command.strip().split(';')
            tree.delete(int(key))
            tree.insert(int(key), value)
    print(f"Operations: read operations: {tree.read_operations}, write operations: {tree.write_operations}")

if __name__ == '__main__':
    tree = BTree(t=4)
    filepath = f"data/{input("Enter file name: ")}"
    tree.main_file_path = filepath
    parse_file(filepath, tree)
    print("File parsed successfully.")
    while True:
        option = input("Choose an option:\n"
                       "1. Insert\n"
                       "2. Delete\n"
                       "3. Search\n"
                       "4. Display tree\n"
                       "5. Update value\n"
                       "6. Read instructions from file\n"
                       "7. Exit\n"
                       "Enter your choice: ")
        print("Write operations:", tree.write_operations)
        print("Read operations:", tree.read_operations)
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
                    print(f"Found ({key}, {tree.read_from_main_file(found_node.offsets[found_node.keys.index(key)])})")
                else:
                    print(f"Not found {key} in tree.")
            case "4":
                option = input("Display values? (y/n): ")
                tree.display(offsets=True if option == "y" else False)
            case "5":
                key = int(input("Enter key: "))
                value = input("Enter new value: ")
                tree.delete(key)
                tree.insert(key, value)
            case "6":
                filepath = f"instructions/{input('Enter file name: ')}"
                with open(filepath, 'r') as file:
                    for line in file:
                        parse_command(line, tree)
            case "7":
                delete_node_files(tree)
                exit(0)

        input("Press Enter to continue...")
