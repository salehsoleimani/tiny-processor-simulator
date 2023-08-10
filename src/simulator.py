import time
from typing import Iterable


def twos_complement(number, len_bits=6):
    binary_number = bin(number)[2:]
    binary_number = binary_number.zfill(len_bits)
    inverted_number = ''.join('1' if bit == '0' else '0' for bit in binary_number)
    twos = bin(int(inverted_number, 2) + 1)[2:]
    twos = twos.zfill(len_bits)
    return int(twos, 2)


def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


class TinyBASUSimulator:

    def __init__(self, prediction_method):

        self.total_jumps = 0
        self.correct_predictions = 0
        self.regs = [0] * 8  # Initialize the registers
        self.memory = [0] * 512  # Initialize the memory
        self.pc = 0  # Initialize the program counter
        self.num_cycles = 0
        self.num_instructions_executed = 0
        self.num_instructions = 0
        self.num_stalls = 0
        self.prediction_method = prediction_method
        self.BPT = {}  # Branch Prediction Table
        self.flush = 0
        self.runtime = 0

    def parse_instruction(self, asm_file):
        machine_codes = []

        func = {
            'add': 0b001,
            'sub': 0b010,
            'slt': 0b100,
            'mul': 0b011,  # Optional
            'div': 0b101,  # Optional
            'slly': 0b000,  # Optional
            'srly': 0b110,  # Optional
        }
        i_opcodes = {
            'addi': 0b0001,
            'li': 0b0010,
            'lui': 0b0011,
            'lw': 0b0100,
            'sw': 0b0101,
            'beq': 0b1010,
            'bne': 0b1011,
            'sll': 0b0111,  # Optional
            'srl': 0b1001,  # Optional
            'sra': 0b1100,  # Optional
        }
        j_opcode = {
            'jmp': 0b1110,
            'jal': 0b1111
        }

        with open(asm_file, 'r') as file:
            lines = file.readlines()
            labels = {}

            self.num_instructions = len(lines)

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
                            previous_instruction = machine_codes[address]
                            opcode = (previous_instruction & 0xf000) >> 12
                            # editing instructions with the label specified
                            instruction = (opcode << 12) & 0xF000
                            if opcode in [13, 14]:  # jmp or jal
                                # store the difference between addresses to jump
                                imm = (cnt - address - 1) & 0xFFFF
                                instruction += imm & 0x0FFF
                                machine_codes[address] = instruction
                            elif opcode in [10, 11]:  # beq or bne
                                rd = (previous_instruction & 0x0E00) >> 9
                                rs = (previous_instruction & 0x01C0) >> 6
                                # store the difference between addresses to jump
                                instruction += int(cnt - address - 1) & 0x003F
                                instruction += (rd << 9) & 0x0e00
                                instruction += (rs << 6) & 0x01c0
                                machine_codes[address] = instruction
                    labels[fields[0][:-1]] = cnt
                    fields.pop(0)
                instruction = 0x0000
                if fields[0] in ['add', 'sub', 'slt', 'mul', 'div', 'slly', 'srly']:

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

                elif fields[0] in ['addi', 'beq', 'bne', 'sw', 'lw', 'sll', 'srl', 'sra']:
                    # addi rx3, rx0, 1

                    opcode = i_opcodes[fields[0]]
                    rd = int(fields[1][2:]) if nf > 1 else 0
                    rs = int(fields[2][2:]) if nf > 1 else 0

                    imm = fields[3] if nf > 1 else 0

                    if fields[0] in ['beq', 'bne'] and not imm.isdigit():
                        try:
                            if fields[-1].strip() in labels.keys():
                                if isinstance(labels[fields[-1].strip()], Iterable):
                                    # if label has been defined after instruction
                                    # and another instruction before this instruction have used this label too
                                    labels[fields[-1].strip()].append(cnt)
                                    imm = 0
                                else:
                                    # if label is defined before this instruction
                                    # store the difference between addresses to jump
                                    imm = labels[fields[-1].strip()] - cnt - 1
                            else:
                                # if label has been defined after instruction
                                labels[fields[-1].strip()] = [-1, cnt]
                                imm = 0

                        except KeyError:
                            return print("Wrong asm code, label has not been defined!")

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
                                labels[fields[-1].strip()].append(cnt)
                                imm = 0
                            else:
                                imm = labels[fields[-1].strip()] - cnt - 1
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
        opcode, rd, rs, rt, func, i_imm, j_imm = self.decode(instruction)

        if opcode == 0:

            if func == 0:  # slly
                self.regs[rd] = self.regs[rs] << self.regs[rt]

            elif func == 1:  # add
                self.regs[rd] = self.regs[rs] + self.regs[rt]  # add rd, rs, rt

            elif func == 2:  # sub
                self.regs[rd] = self.regs[rs] - self.regs[rt]  # sub rd, rs, rt

            elif func == 3:  # mul
                self.regs[rd] = self.regs[rs] * self.regs[rt]

            elif func == 4:  # slt
                self.regs[rd] = 1 if self.regs[rs] < self.regs[rt] else 0

            elif func == 5:  # div
                self.regs[rd] = self.regs[rs] / self.regs[rt]

            elif func == 6:  # srly
                self.regs[rd] = self.regs[rs] >> self.regs[rt]

        elif opcode == 1:  # addi
            self.regs[rd] = self.regs[rs] + int(i_imm)  # addi rd, rs, imm

        elif opcode == 2:  # li: load immediate
            self.regs[rd] = int(i_imm)  # li rd, imm

        elif opcode == 3:  # lui: load upper immediate
            self.regs[rd] = int(i_imm) << 10  # lui rd, imm

        elif opcode == 4:  # lw: load word
            self.regs[rd] = self.memory[self.regs[rs] + int(i_imm)]

        elif opcode == 5:  # sw: store word
            self.memory[self.regs[rs] + int(i_imm)] = self.regs[rd]

        elif opcode == 7:  # sll
            self.regs[rd] = self.regs[rs] << int(i_imm)

        elif opcode == 9:  # srl
            self.regs[rd] = self.regs[rs] >> int(i_imm)

        elif opcode == 12:  # sra
            self.regs[rd] = sign_extend(self.regs[rs], int(i_imm))

        elif opcode == 0b1110:  # jmp to location
            if bin(j_imm)[2:].zfill(12)[0] == '1':
                self.pc -= twos_complement(int(j_imm), len_bits=12)
            else:
                self.pc += int(j_imm)

        elif opcode == 0b1111:  # jal to location
            if bin(j_imm)[2:].zfill(12)[0] == '1':
                self.pc -= twos_complement(int(j_imm), len_bits=12)
            else:
                self.pc += int(j_imm)
            self.regs[7] = self.pc + 1

        elif opcode == 0x1010:  # branch equal
            if self.regs[rs] == self.regs[rd]:  # beq rd, rs, imm
                if bin(i_imm)[2:].zfill(6)[0] == '1':
                    self.pc -= twos_complement(int(i_imm))
                else:
                    self.pc += int(i_imm)
            else:
                self.pc += 1

        elif opcode == 0x1011:  # branch not equal
            if self.regs[rs] != self.regs[rd]:  # bne rd, rs, imm
                if bin(i_imm)[2:].zfill(6)[0] == '1':
                    self.pc -= twos_complement(int(i_imm))
                else:
                    self.pc += int(i_imm)
            else:
                self.pc += 1

    def branch_prediction(self, instruction):
        # Perform branch prediction based on the selected method
        if self.prediction_method == 'ST':
            return True
        elif self.prediction_method == 'SN':
            return False
        elif self.prediction_method == 'D1':
            opcode, rd, rs, rt, func, i_imm, j_imm = self.decode(instruction)
            key = (opcode, rs, rt)
            return self.BPT.get(key, True)
        elif self.prediction_method == 'D2':
            opcode, rd, rs, rt, func, i_imm, j_imm = self.decode(instruction)
            key = (opcode, rs, rt)

            if key not in self.BPT:
                self.BPT[key] = 'WT'

            prediction = self.BPT[key]

            if prediction in ('ST', 'WT'):
                return True
            elif prediction in ('SNT', 'WNT'):
                return False
        elif self.prediction_method == 'IQ':
            opcode, rd, rs, rt, func, i_imm, j_imm = self.decode(instruction)
            key = (opcode, rs, rt)

            if key not in self.BPT:
                self.BPT[key] = 'SN'

            prediction = self.BPT[key]

            if prediction in ('ST', 'WT3', 'WT2', 'WT1'):
                return True
            elif prediction in ('WN3', 'WN2', 'WN1', 'SN'):
                return False
        else:
            pass

    def update_branch_prediction(self, opcode, rs, rt, actual_result):
        if self.prediction_method == 'D1':
            key = (opcode, rs, rt)
            self.BPT[key] = actual_result
        elif self.prediction_method == 'D2':
            key = (opcode, rs, rt)

            prediction = self.BPT[key]

            if actual_result:
                if prediction == 'WT':
                    self.BPT[key] = 'ST'
                elif prediction == 'WNT':
                    self.BPT[key] = 'WT'
                elif prediction == 'SNT':
                    self.BPT[key] = 'WNT'
            else:
                if prediction == 'ST':
                    self.BPT[key] = 'WT'
                elif prediction == 'WT':
                    self.BPT[key] = 'WNT'
                elif prediction == 'WNT':
                    self.BPT[key] = 'SNT'
        elif self.prediction_method == 'IQ':
            key = (opcode, rs, rt)

            prediction = self.BPT[key]

            if actual_result:
                if prediction == 'WT3':
                    self.BPT[key] = 'ST'
                elif prediction == 'WT2':
                    self.BPT[key] = 'WT3'
                elif prediction == 'WT1':
                    self.BPT[key] = 'WT2'
                elif prediction == 'WN3':
                    self.BPT[key] = 'WT1'
                elif prediction == 'WN2':
                    self.BPT[key] = 'WN3'
                elif prediction == 'WN1':
                    self.BPT[key] = 'WN2'
                elif prediction == 'SN':
                    self.BPT[key] = 'WN1'
            else:
                if prediction == 'SN':
                    self.BPT[key] = 'WN1'
                elif prediction == 'WN1':
                    self.BPT[key] = 'WN2'
                elif prediction == 'WN2':
                    self.BPT[key] = 'WN3'
                elif prediction == 'WN3':
                    self.BPT[key] = 'WT1'
                elif prediction == 'WT1':
                    self.BPT[key] = 'WT2'
                elif prediction == 'WT2':
                    self.BPT[key] = 'WT3'
                elif prediction == 'WT3':
                    self.BPT[key] = 'ST'

    def run(self, timeout):
        start = time.time()
        while True:
            if self.num_cycles > timeout:
                print('timeout for executing program! Something has bug')
                exit()

            instruction = self.fetch()

            if instruction == 0:
                break  # End of the program

            opcode, rd, rs, rt, func, i_imm, j_imm = self.decode(instruction)

            if opcode == 10 or opcode == 11:  # implement prediction
                # Branch instruction
                predicted_result = self.branch_prediction(instruction)
                if predicted_result:
                    self.flush += 3

                    # Taken branch
                    if bin(i_imm)[2:].zfill(6)[0] == '1':
                        self.pc -= twos_complement(int(i_imm))
                    else:
                        self.pc += int(i_imm)

                    self.num_stalls += 1
                else:
                    instruction = self.fetch()
                    # Not Taken branch
                    # Execute the instruction
                    self.execute(instruction)
                    # Update performance metrics
                    self.num_cycles += 3
                    self.num_instructions_executed += 1

                if opcode == 10:  # beq
                    actual_result = self.regs[rs] == self.regs[rd]
                else:  # bne
                    actual_result = self.regs[rs] != self.regs[rd]

                # Update branch prediction
                self.update_branch_prediction(opcode, rs, rt, actual_result)

            else:
                self.execute(instruction)
                self.num_cycles += 1
                self.num_instructions_executed += 1

        self.runtime = (time.time() - start) * 1000

    def report(self, report_file):
        ipc = self.num_instructions_executed / self.num_cycles if self.num_cycles > 0 else 0

        num_correct_predictions = self.num_instructions_executed - self.num_stalls
        prediction_accuracy = (
                                      num_correct_predictions / self.num_instructions_executed) * 100 if self.num_instructions_executed > 0 else 0
        #   total cycles / total number of cycles that would've been required without any stalls
        speedup = self.num_cycles / (self.num_cycles + self.num_stalls) if (
                                                                                   self.num_cycles + self.num_stalls) > 0 else 0

        with open(report_file, 'w') as file:
            file.write('tiny processor report file\n')
            file.write('simulation runtime: ' + str(self.runtime) + 'ms\n')
            file.write('number of instructions: ' + str(self.num_instructions) + '\n')
            file.write('number of simulation cycles: ' + str(self.num_cycles) + '\n')
            file.write('number of executed instructions: ' + str(self.num_instructions_executed) + '\n')
            file.write('number of stalls: ' + str(self.num_stalls) + '\n')
            file.write('prediction accuracy: ' + str(prediction_accuracy) + '\n')
            file.write('speedup: ' + str(speedup) + '\n')
            file.write('IPC(Instructions Per Cycle): ' + str(ipc) + '\n')
            file.write('\n')
            file.write('program counter value: ' + str(self.pc) + '\n')
            file.write('register value:\n')
            for i, register in enumerate(self.regs):
                file.write(f'regs[{i}]:{hex(register)}\n')
            file.write('\nmemory content value:\n')
            for i, mem in enumerate(self.memory):
                if mem != 0:
                    file.write(f'memory[{i}] = {hex(mem)}\n')

            file.write('others is 0x0000')
