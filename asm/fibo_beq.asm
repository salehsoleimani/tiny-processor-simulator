# Part of Assignment. Needs some modifications
      lui rx6, 1          # rx0 = 0x10000 (Fibonacci number F0)
      li rx1, 1
      lui rx0, 0          # rx0 = zero
      addi rx2, rx0, 20   # rx2 = 20 (number of iterations)
      addi rx3, rx0, 2    # rx3 = 2 (counter)
loop: add rx4, rx6, rx1   # rx4 = rx0 + rx1 (Fibonacci number Fn = Fn-1 + Fn-2)
      addi rx6, rx1, 0    # rx0 = rx1 (shift the values for the next iteration)
      addi rx1, rx4, 0    # rx1 = rx4
      addi rx3, rx3, 1    # Increment the counter
      beq rx3, rx2, end   # Branch to last instruction
      jal loop            # Branch to last instruction
end:  add rx4, rx0, rx1   # Store the 20th Fibonacci number in register rx4
