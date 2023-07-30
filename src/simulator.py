#!/usr/bin/env python
#
# Computer Engineering Department, Bu-Ali University, Hamadan, Iran
# Computer Architecture Final Project Template
# Course supervisor and Instructor: Dr. M. Abbasi
# Designed by Neda Motamediraad, Graduate Teaching Assistant
# github.com/nedaraad/TinyProcessorSimulator
# under MIT licence

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
        with open(asm_file, 'r') as file:
            lines = file.readlines()
            for cnt, line in enumerate(lines):
                instruction = 0x0000
                labels = {}
                fields = line.strip().split(',')
                nf = len(fields)
                if fields[0][-1] == ':':  # branch label
                    labels[fields[0]] = cnt
                else:
                    # example for R-Format instructions
                    if fields[0] == 'add':
                        opcode = 0
                        rd = int(fields[1][2:]) if nf > 2 else 0
                        rs = int(fields[2][2:]) if nf > 1 else 0
                        rt = int(fields[3][2:]) if nf > 3 else 0
                        func = 0
                        instruction += (opcode << 12) & 0xF000
                        instruction += (rd << 9) & 0x0700
                        instruction += (rs << 6) & 0x0070
                        instruction += (rt << 3) & 0x0070
                        instruction += func & 0x0007
                        machine_codes.append(instruction)

                    # example for I-Format instructions
                    elif fields[0] == 'addi':
                        opcode = 1
                        rd = int(fields[1][2:]) if nf > 1 else 0
                        rs = int(fields[2][2:]) if nf > 1 else 0
                        imm = int(fields[3]) if nf > 1 else 0
                        instruction += (opcode << 12) & 0xF000
                        instruction += (rd << 9) & 0x0700
                        instruction += (rs << 6) & 0x0070
                        instruction += imm
                        machine_codes.append(instruction)

                    # example for J-Format instructions
                    elif fields[0][0:3] == 'jmp':
                        opcode = 0b1110

                        if fields[0][3:].isdigit():
                            imm = int(fields[0][3:].strip())
                        else:
                            imm = int(labels[fields[0][3:].strip()])
                        instruction += (opcode << 12) & 0xF000
                        instruction += imm & 0x0FFF
                        machine_codes.append(instruction)
                    else:
                        machine_codes.append(0x0000)

            for address, inst in enumerate(machine_codes):
                self.memory[address] = inst

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
