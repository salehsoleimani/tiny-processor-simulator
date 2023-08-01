#!/usr/bin/env python
#
# Computer Engineering Department, Bu-Ali University, Hamadan, Iran
# Computer Architecture Final Project Template
# Course supervisor and Instructor: Dr. M. Abbasi
# Designed by Neda Motamediraad, Graduate Teaching Assistant
# github.com/nedaraad/TinyProcessorSimulator
# under MIT licence
import curses.ascii
from curses.ascii import isalpha
from typing import Iterable


class TinyBASUSimulator:
    def __init__(self, prediction_method):

        self.regs = [0] * 8  # Initialize the registers
        self.memory = [0] * 512  # Initialize the memory
        self.pc = 0  # Initialize the program counter
        self.num_cycles = 0
        self.num_instructions = 0
        self.num_stalls = 0
        self.prediction_method = prediction_method
        self.BPT = None  # Branch Prediction Table

    def parse_instruction(self, asm_file):
        machine_codes = []

        func = {
            'add': 0b001,
            'sub': 0b010,
            'slt': 0b100
        }
        i_opcodes = {
            'addi': 0b0001,
            'li': 0b0010,
            'lui': 0b0011,
            'lw': 0b0100,
            'sw': 0b0101,
            'beq': 0b1010,
            'bne': 0b1011
        }
        j_opcode = {
            'jmp': 0b1110,
            'jal': 0b1111
        }

        with open(asm_file, 'r') as file:
            lines = file.readlines()
            labels = {}

            for cnt, line in enumerate(lines):
                fields = line.strip().split(', ')
                label = fields[0]
                fields.pop(0)
                fields = label.strip().split(' ') + fields
                nf = len(fields)
                if fields[0][-1] == ':':  # branch label
                    if fields[0][:-1] in labels.keys() and -1 in labels[fields[0][:-1]]:
                        labels[fields[0][:-1]].remove(-1)
                        for address in labels[fields[0][:-1]]:
                            print(address)
                            previous_instruction = machine_codes[address]
                            opcode = (previous_instruction & 0xf000) >> 12
                            # editing instructions with the label specified
                            instruction = (opcode << 12) & 0xF000
                            if opcode in [13, 14]:  # jmp or jal
                                imm = cnt & 0xFFFF
                                instruction += imm & 0x0FFF
                                machine_codes[address] = instruction
                            elif opcode in [10, 11]:  # beq or bne
                                rd = (previous_instruction & 0x0E00) >> 9
                                rs = (previous_instruction & 0x01C0) >> 6

                                instruction += int(cnt) & 0x003F
                                instruction += (rd << 9) & 0x0e00
                                instruction += (rs << 6) & 0x01c0
                                machine_codes[address] = instruction

                    labels[fields[0][:-1]] = cnt
                    fields.pop(0)
                instruction = 0x0000
                if fields[0] in ['add', 'sub', 'slt']:
                    opcode = 0
                    rd = int(fields[1][2:]) if nf > 2 else 0
                    rs = int(fields[2][2:]) if nf > 1 else 0
                    rt = int(fields[3][2:]) if nf > 3 else 0
                    funct = func[fields[0]]
                    instruction += (opcode << 12) & 0xF000
                    instruction += (rd << 9) & 0x0E00
                    instruction += (rs << 6) & 0x01C0
                    instruction += (rt << 3) & 0x0038
                    instruction += funct & 0x0007
                    machine_codes.append(instruction)
                elif fields[0] in ['addi', 'beq', 'bne', 'sw', 'lw']:
                    opcode = i_opcodes[fields[0]]
                    rd = int(fields[1][2:]) if nf > 1 else 0
                    rs = int(fields[2][2:]) if nf > 1 else 0

                    imm = fields[3] if nf > 1 else 0

                    if fields[0] in ['beq', 'bne'] and all(curses.ascii.isalpha(c) for c in imm):
                        # try:
                        if fields[-1].strip() in labels.keys():
                            if isinstance(labels[fields[-1].strip()], Iterable):
                                # imm = labels[fields[-1].strip()][1]

                                labels[fields[-1].strip()].append(cnt)
                                imm = 0
                            else:
                                imm = labels[fields[-1].strip()]
                        else:
                            if fields[-1].strip() in labels.keys():
                                if isinstance(labels[fields[-1].strip()], Iterable):
                                    labels[fields[-1].strip()].append(cnt)
                            else:
                                labels[fields[-1].strip()] = [-1, cnt]
                                imm = 0

                        # except KeyError:
                        #     return print("Wrong asm code, label has not been defined")

                    instruction += (opcode << 12) & 0xF000
                    instruction += (rd << 9) & 0x0E00
                    instruction += (rs << 6) & 0x01C0
                    instruction += int(imm) & 0x003F
                    machine_codes.append(instruction)
                elif fields[0] in ['li', 'lui']:
                    opcode = i_opcodes[fields[0]]
                    rd = int(fields[1][2:]) if nf > 1 else 0
                    imm = int(fields[2]) if nf > 1 else 0
                    instruction += (opcode << 12) & 0xF000
                    instruction += (rd << 9) & 0x0E00
                    instruction += imm
                    machine_codes.append(instruction)
                elif fields[0] in ['jmp', 'jal']:
                    opcode = j_opcode[fields[0]]
                    if fields[-1].isdigit():
                        imm = int(fields[-1].strip())
                    else:
                        if fields[-1].strip() in labels.keys():
                            if isinstance(labels[fields[-1].strip()], Iterable):
                                # imm = labels[fields[-1].strip()][1]
                                labels[fields[-1].strip()].append(cnt)
                                imm = 0
                            else:
                                imm = labels[fields[-1].strip()]
                        else:
                            if fields[-1].strip() in labels.keys():
                                if isinstance(labels[fields[-1].strip()], Iterable):
                                    labels[fields[-1].strip()].append(cnt)
                            else:
                                labels[fields[-1].strip()] = [-1, cnt]
                            imm = 0

                    instruction += (opcode << 12) & 0xF000
                    instruction += imm & 0x0FFF
                    machine_codes.append(instruction)
                else:
                    machine_codes.append(0x0000)

            for address, inst in enumerate(machine_codes):
                self.memory[address] = inst
                print(inst)

    def init_memory(self, data_file):
        # Initialize the memory with content from a files
        with open(data_file, 'r') as file:
            data = file.readlines()
            for i, line in enumerate(data):
                self.memory[256 + i] = int(line.strip())

    def fetch(self):
        instruction = self.memory[self.pc]
        self.pc += 1
        return instruction

    @staticmethod
    def decode(instruction):
        opcode = (instruction >> 12) & 0x000F
        rd = (instruction >> 9) & 0x7
        rs = (instruction >> 6) & 0x7
        rt = (instruction >> 3) & 0x7
        func = instruction & 0x07
        i_imm = instruction & 0x03F
        j_imm = instruction & 0x0FFF
        return opcode, rd, rs, rt, func, i_imm, j_imm

    def execute(self, instruction):
        opcode, rd, rs, rt, func, i_imm, j_imm = instruction
        if opcode == 0:

            if func == 1:  # add
                self.regs[rd] = self.regs[rs] + self.regs[rt]  # add rd, rs, rt

            elif func == 2:  # sub
                self.regs[rd] = self.regs[rs] - self.regs[rt]  # sub rd, rs, rt

            elif func == 4:  # slt
                self.regs[rd] = 1 if self.regs[rs] < self.regs[rt] else 0

        elif opcode == 1:  # addi
            self.regs[rd] = self.regs[rs] + i_imm  # addi rd, rs, imm

        elif opcode == 2:  # li: load immediate
            self.regs[rd] = int(i_imm)  # li rd, imm

        elif opcode == 2:  # li: load upper immediate
            self.regs[rd] = int(i_imm) << 12  # lui rd, imm

        elif opcode == 4:  # lw: load word
            self.regs[rd] = self.memory[self.regs[rs] + i_imm]

        elif opcode == 5:  # sw: store word
            self.memory[self.regs[rs] + i_imm] = self.regs[rd]

        elif opcode == 0b1110:  # jmp to location
            self.pc = self.pc + j_imm

        elif opcode == 0b1111:  # jmp to location
            self.regs[15] = self.pc
            self.pc = self.pc + j_imm

        elif opcode == 0x1010:  # branch equal
            pass

        elif opcode == 0x1010:  # branch not equal
            pass

    def branch_prediction(self, instruction):
        # Perform branch prediction based on the selected method
        if self.prediction_method == 'ST':
            return True

        elif self.prediction_method == 'SN':
            return False
        elif self.prediction_method == 'D1':
            if instruction[0] == '.....':
                return self.BPT['key']
        else:
            pass

    def update_branch_prediction(self, opcode, rs, rt, actual_result):
        # Update the branch prediction table with the actual result
        if self.prediction_method == 'dynamic ...':
            key = (opcode, rs, rt)
            self.BPT[key] = actual_result

    def run(self, timeout):
        while True:
            if self.num_cycles > timeout:
                print('timeout for executing program! Something has bug')
                exit()

            instruction = self.fetch()

            if instruction == 0:
                break  # End of the program

            opcode, rd, rs, rt, func, i_imm, j_imm = self.decode(instruction)

            if opcode == 0xb1010 or opcode == 0xb1011:  # implement prediction
                # Branch instruction
                predicted_result = self.branch_prediction(instruction)
                if predicted_result:
                    # Taken branch
                    self.pc += i_imm
                else:
                    # Not Taken branch
                    pass
                    # Execute the instruction
                    self.execute(instruction)
                    # Update performance metrics
                    self.num_cycles += 1
                    self.num_instructions += 1

                # Update branch prediction
                # Branch instruction
                actual_result = self.pc == (self.pc - 1) + i_imm
                self.update_branch_prediction(opcode, rs, rt, actual_result)

    def report(self, report_file):
        # Print the performance metrics
        print("Performance Metrics:")
        print("Number of Cycles:", self.num_cycles)
        with open(report_file, 'w') as file:
            file.write('Some Report Text')


def tester():
    pass


if __name__ == '__main__':
    tester()
