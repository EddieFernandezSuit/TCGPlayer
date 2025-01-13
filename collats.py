

def calc_collatz(num):
    collatz = {
        'nums': [num],
        'divides': 0,
    }
    while num > 1:
        if num % 2 == 0:
            num = int(num/2)
            collatz['divides'] += 1
        else:
            num *= 3
            num += 1
        collatz['nums'].append(num)
    
    return collatz

def calc_collatz_divides(num):
    return calc_collatz(num)['divides']


def check_divides():
    while True:
        number = int(input('Number: '))
        all_divides = []

        for num in range(1, 2 ** number):
            all_divides.append(calc_collatz_divides(num))
        max_divides = max(all_divides)
        print(max_divides)
        # print()

def collatz_step(num):
    did_divide = 0
    if num % 2 == 0:
        num = int(num / 2)
        did_divide = 1
    else:
        num = num * 3 + 1
    return num, did_divide

def divides_until_smaller_num(num):
    original_num = num
    divides = 0

    while num >= original_num and num != 1:
        num, did_divide = collatz_step(num)
        
        divides += did_divide
        # print(num)
        # print(divides)

    # print(divides, end=' ')
    return divides


# while True:
#     num = int(input("Enter: "))
#     divides_until_smaller_num(num)


# print(calc_collatz(31))

# while True:
#     end_num = int(input("Enter: "))
#     maxx = 0
#     for num in range(1,end_num + 1):
#         divides = divides_until_smaller_num(num)
#         if divides > maxx:
#             maxx = divides
    
#     print(maxx)
