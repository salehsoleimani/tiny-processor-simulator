lui rx6, 1
  li rx1, 1
  lui rx0, 0
  addi rx2, rx0, 4
  addi rx3, rx0, 1
loop: add rx4, rx0, rx1
  addi rx0, rx1, 0
  addi rx1, rx4, 0
  addi rx3, rx3, 1
  beq rx3, rx2, end
  jal loop
end: add rx4, rx0, rx1