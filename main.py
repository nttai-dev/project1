# Nhận một chuỗi các số nguyên từ người dùng, cách nhau bởi dấu cách
input_str = input("Enter a list of numbers separated by space: ")

# Tách chuỗi thành các chuỗi con và chuyển đổi chúng thành số nguyên
numbers = [int(num) for num in input_str.split()]
print("The list of numbers is:", numbers)