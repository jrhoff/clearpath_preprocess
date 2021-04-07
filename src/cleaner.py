import re, glob, io, logging
from src.constants import text_numbers, violations, invalid_LHS, \
    EQUATIONS, special_char_replacement, MATH_CONTEXT_INDICATORS, REGION_KEYWORDS
logger = logging.getLogger("Cleaner")


class Cleaner:

    def __init__(self, text):
        self.text = self._clean_violations(text)

    def switch(self, case, tokens):
        if case == "PLUSEQUAL":
            return self.plus_equals_verify(tokens)
        elif case == "INSERT":
            return self.insert_equals(tokens)
        elif case == 'ALPHANUM':
            return self.alphanum_verify(tokens)
        elif case == 'SUM':
            return self.sum_verify(tokens)
        elif case == "LHDD":
            return self.double_digit_fix(tokens,'LH')
        elif case == "RHDD":
            return self.double_digit_fix(tokens,'RH')
        else:

            logger.warning(f'Unkown Case encountered: {case}')
            return None, None

    def swap_log_handler(self, filename):
        file_handler = logging.FileHandler(filename, 'a+')
        for hdlr in logger.handlers[:]:  # remove all old handlers
            logger.removeHandler(hdlr)
        logger.addHandler(file_handler)
        return None

    def pad_biopsy_regions(self,text):
        locations = []
        lowered = text.lower()
        iters = [re.finditer(keyword,lowered) for keyword in REGION_KEYWORDS]
        for iter in iters:
            for match in iter:
                locations.append( (match.start(),match.end()))

        for loc in locations: # pad all occurences of keywords with space
            cased_word = text[loc[0]:loc[1]]
            text = re.sub(text[loc[0]:loc[1]]," " +text[loc[0]:loc[1]] + " ",text)
        text = re.sub(r"  +"," ",text)  #remove double spaces
        return text



    def _clean_violations(self,text):

        for violation, replacement in violations:
            text = re.sub(violation, replacement, text)
        return text



    def alphanum_verify(self, tokens):
        change = False
        # 0, 2, and 4 indicies should be digits, if not, get most likely digit
        try:
            tok0, tok2, tok4 = tokens[0], tokens[2], tokens[4]
        except:
            print(tokens)
        if not tok0.isdigit():
            if tok2.isdigit() and tok4.isdigit():
                tokens[0] = str(int(tok4) - int(tok2))
                tok0 = tokens[0]
            change = True
        if not tok2.isdigit():
            if tok0.isdigit() and tok4.isdigit():
                tokens[2] = str(int(tok4) - int(tok0))
                tok2 = tokens[2]
            change = True
        if not tok4.isdigit() and tok0.isdigit() and tok2.isdigit():
            tokens[4] = str(int(tok0) + int(tok2))
            change = True

        return tokens, change

    def sum_verify(self,tokens):

        if len([tok.isdigit() for tok in tokens if tok.isdigit()]) != 3:
            debug = True
            logger.warning(f"Unable to fix equation: {' '.join(tokens)}")
            return tokens, False
        change = False
        tok0, tok2, tok4 = int(tokens[0]), int(tokens[2]), int(tokens[4])

        if tok2 > 5 and tok0 > 5:
            logger.warning(f"Unable to fix equation, both greater than 5: {' '.join(tokens)}")
            return tokens, False

        if tok0 > 5:
            tok0 = tok4 - tok2
            tokens[0] = str(tok0)
            change = True

        if tok2 > 5:
            tok2 = tok4 - tok0
            tokens[2] = str(tok2)
            change = True

        if not tok0 + tok2 == tok4:
            diff = tok4 - tok0 - tok2
            if diff < 0:  # if the difference is negative, then the sum is smaller than its components, just get the correct sum
                tokens[4] = str(int(tokens[0]) + int(tokens[2]))
                change = True
        return tokens, change

    def plus_equals_verify(self,tokens):
        change = False
        if tokens[1] != '+':
            tokens[1] = '+'
            change = True
        if tokens[3] != '=':
            tokens[3] = '='
            change = True
        return tokens, change

    def insert_equals(self,tokens):
        sum = tokens.pop()
        tokens.append('=')
        tokens.append(sum)
        tokens, change = self.alphanum_verify(tokens)
        tokens, change = self.sum_verify(tokens)
        return tokens, True

    def double_digit_fix(self,tokens,side):
        change = False
        tok0, tok2, tok4 = tokens[0], tokens[2], tokens[4]
        if side == 'RH':
            # we have 2 digits on the RHS
            summ = int(tokens[4])
            num1 = int(tok0)
            leftover = str(summ - num1)
            if leftover in tok2:
                tokens[2] = leftover
                change = True

        elif side == 'LH':
            # we have 2 digits on the LHS
            summ = int(tokens[4])
            num2 = int(tok2)
            leftover = str(summ - num2)
            if leftover in tok0:
                tokens[0] = leftover
                change = True
        return tokens, change

    def reformat_equation(self, tokens, to_format):
        if to_format == "BASIC":
            if len(tokens) < 5:
                if len(tokens[2]) == 3 and tokens[2][1] == '4':
                    debug = True
                    return [tokens[2][0]] + [tokens[2][1]] + [tokens[2][2]] + ['='] + [tokens[0]]
            return [tokens[2]] + [tokens[3]] + [tokens[4]] + ['='] + [tokens[0]]
        else:
            return [tokens[4]] + ['('] + [tokens[0]] + ['+'] + [tokens[2]] + [')']

    def parse_equation(self,text, mode, filename):
        tokens = text.split()
        change = False
        if 'GLOB' in mode:
            tokens = self.reformat_equation(tokens, "BASIC")
            temp_mode = mode.split('_')[1]
            tokens, change = self.switch(temp_mode, tokens)
            tokens = self.reformat_equation(tokens, "GLOB")

        else:
            tokens, change = self.switch(mode,tokens)
        if change:
            new_text = ' '.join(tokens)
            logger.warning(f'Fix in {mode} mode\n'
                       f'\t{text}\t --->\n'
                       f'\t{new_text}')
            return new_text
        return False


    def fix_equations(self, directory):
        self.swap_log_handler('equation_switch.log')
        num_fixes = 0
        for f in glob.glob(dir + '*.txt'):
            file = io.open(f, 'r',encoding='utf-8')
            logger.warning(f'Checking File {file.name} for unacceptable equations...\n')
            text = file.read()
            for EQUATION, MODE in EQUATIONS:
                matches = re.findall(EQUATION,text)
                if MODE == "GLOB_ALPHANUM" and matches:
                    debug = True
                fixed_equations = [self.parse_equation(match, MODE,file.name) for match in matches]
                for i, fix in enumerate(fixed_equations):
                    if fix:
                        text = text.replace(matches[i],fix)
                        num_fixes +=1
            # write to file
            file.close()
            out = open(f, 'w+')
            out.write(text)
        logger.warning(f'Done fixing equations. {num_fixes} equations fixed.')


    def find_context(self,index, line):

        if 'gleason' in line.lower():
            if line[index-2:index].lower() == 'on':
                return 'ALPHA'  # most likely Gleason's with the apostrophe not recognized
            return 'NUM'
        previous_char = line[max(index-1,0)]
        next_char = line[min(index+1,len(line))]
        previous_matches = re.match(MATH_CONTEXT_INDICATORS,previous_char)
        next_matches = re.match(MATH_CONTEXT_INDICATORS,next_char)
        if previous_matches or next_matches:
            return 'NUM'
        return 'ALPHA'

    def resolve_encoding_issues(self, directory):
        self.swap_log_handler('character_switch.log')
        used = set([])
        for f in glob.glob(directory + '*.txt'):
            file = io.open(f, 'r', encoding='utf-8')
            new_lines = []
            logger.warning(file.name)

            for line in file.readlines():
                temp_line = line
                chars = line.replace(' ','')
                for char in special_char_replacement:
                    if char in line:
                        context = self.find_context(chars.index(char),chars)
                        used.add(char)
                        temp_line = temp_line.replace(char,special_char_replacement[char][context])
                        logger.warning(f"Context of {char} determined to be {context} in:\n\n"
                                       f"{line}--->\n"
                                       f"{temp_line.encode('utf-8').decode()}\n")

                new_lines.append(temp_line)
            debug = True
            file.close()
            out = open(f, 'w+')
            for line in new_lines:
                out.write(line)
        return None

    def resolve_text_numbers(self, text):
        tokens = text.split(' ')
        for i,tok in enumerate(tokens):
            if tok.lower().strip() in text_numbers:
                tokens[i] = text_numbers[tok.lower()]
                print(f'REPLACEMENT MADE:\t {tok}\t {text_numbers[tok.lower()]}')
                if '\n' in tok:
                    tokens[i] = tokens[i] + '\n'

        new_text = re.sub('\n\n+', '\n', ' '.join(tokens))
        return new_text
