beq rx3, rx2, end
loop: add rx4, rx6, rx1
addi rx6, rx1, 0
jmp end
addi rx1, rx4, 0
bne rx3, rx2, loop
jal loop
end: add rx4, rx0, rx1