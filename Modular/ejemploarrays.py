number_string = "1,5,7,8.1,900"
number_list = [float(num) for num in number_string.split(',')]

print(number_list)
number_string = ','.join([str(num) for num in number_list])
print(number_string)
