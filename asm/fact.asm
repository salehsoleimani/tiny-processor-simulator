lui rx0, 1
lui rx1, 50
loop: beq rx1, rx20, end
mul rx0, rx0, rx1
addi rx1, rx1, -1
jal loop
end: li rx0, 0