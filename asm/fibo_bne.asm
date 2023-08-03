beq rx3, rx2, end
loop: add rx4, rx6, rx1
addi rx3, rx0, 2
addi rx6, rx1, 0
addi rx1, rx4, 0
bne rx3, rx2, loop
addi rx3, rx3, 1
end: add rx4, rx0, rx1