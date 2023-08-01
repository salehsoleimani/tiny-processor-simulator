lui rx6, 1
li rx1, 1
lui rx0, 0
addi rx2, rx0, 20
addi rx3, rx0, 2
bne rx3, rx2, end
loop: add rx4, rx6, rx1
addi rx6, rx1, 0
jmp end
addi rx1, rx4, 0
bne rx3, rx2, loop
addi rx3, rx3, 1
jal loop
end: add rx4, rx0, rx1