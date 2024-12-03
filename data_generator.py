import random


def generate_records(file_name, num_records):
    unique_keys = set()
    with open(file_name, 'w') as file:
        for _ in range(num_records):
            while True:
                key = random.randint(1, num_records * 10)
                if key not in unique_keys:
                    unique_keys.add(key)
                    break

            value = list(random.choices(range(10), k=random.randint(1, 30)))

            file.write(f"{key}: {sorted(value)}\n")
    print(f"Plik '{file_name}' został wygenerowany z {num_records} rekordami.")


filename = input("Podaj nazwę pliku: ")
size = int(input("Podaj wielkość pliku: "))
generate_records(f"data/{filename}.txt", size)
