      li rx6, 1          # rx6 = 0x1 (Fibonacci number F0)
      li rx1, 1          # rx1 = 0x1 (Fibonacci number F1)
      lui rx0, 0          # rx0 = zero
      addi rx2, rx0, 20   # rx2 = 20 (number of iterations)
      addi rx3, rx0, 2    # rx3 = 2 (counter)
loop: add rx4, rx6, rx1   # rx4 = rx0 + rx1 (Fibonacci number Fn = Fn-1 + Fn-2)
      addi rx6, rx1, 0    # rx0 = rx1 (shift the values for the next iteration)
      addi rx1, rx4, 0    # rx1 = rx4
      addi rx3, rx3, 1    # Increment the counter
      bne rx3, rx2, loop  # Branch back to the loop if the counter != 20
      add rx4, rx0, rx1   # Store the 20th Fibonacci number in register rx4
