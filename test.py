

# num =20
# for x in range(num):
#     a = 16 ** x
#     print(16 ** x, end=' ')
#     print(len(str(a)))

# print()
# for x in range(num):
#     a =36**x
#     print(36 ** x, end=' ')
#     print(len(str(a)))


def get_nums(nums, k):
    new_nums = []
    possible_nums = ['0','1','6','8','9']
    if len(nums) == 0:
        for n in possible_nums:
            new_nums.append(n)
        return get_nums(new_nums, k)

    if len(nums[0]) == k:
        return nums
    
    for i, num in enumerate(nums):
        for n in possible_nums:
            new_nums.append(num + n)
    
    return get_nums(new_nums, k)

def get_nums(nums, k):
    new_nums = []
    possible_nums = ['0','1','6','8','9']
    for n in possible_nums:
        new_nums.append(n)

    while len(new_nums[0]) < k:
        # for i, num in enumerate(new_nums):

        for n in possible_nums:
            new_nums.append(new_nums[0] + n)
        del new_nums[0]
    
    return new_nums


print(get_nums([], 3))

        