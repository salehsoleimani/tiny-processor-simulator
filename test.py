def twos_complement(number, len_bits=6):
    binary_number = bin(number)[2:]
    binary_number = binary_number.zfill(len_bits)
    inverted_number = ''.join('1' if bit == '0' else '0' for bit in binary_number)
    twos = bin(int(inverted_number, 2) + 1)[2:]
    twos = twos.zfill(len_bits)
    return int(twos, 2)


print(twos_complement(63, 12))
