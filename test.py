def fibonacci(n):       
    first = 0  
    second = 1  
    sum =0  
    if n == 0 or n == 1:   return n  
    cur = 0  
    for i in range(n -1):   
        cur = first + second   
        if cur % 2 == 0: sum += cur   
        first = second   
        second = cur  

    return sum

print(fibonacci(9))