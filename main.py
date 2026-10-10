<<<<<<< HEAD
# Nhận một chuỗi các số nguyên từ người dùng, cách nhau bởi dấu cách
input_str = input("Enter a list of numbers separated by space: ")

# Tách chuỗi thành các chuỗi con và chuyển đổi chúng thành số nguyên
numbers = [int(num) for num in input_str.split()]
print("The list of numbers is:", numbers)
=======
print("hello, world")

def isPrime(n):
    if n < 2:
        return False
    elif n == 2:
        return True
    elif n % 2 == 0:
        return False
    else:
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
>>>>>>> 7027c097ec2709e5c4177b5c18a9a3d0e01289dc
