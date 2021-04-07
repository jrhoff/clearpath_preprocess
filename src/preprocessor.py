
import re, logging
from spacy.symbols import ORTH, POS, PUNCT, NUM, NOUN
from spacy.lang.en.stop_words import STOP_WORDS
from src.constants import ILLEGAL_ENDINGS, MIN_SENTENCE_LENGTH, \
    MAX_SENTENCE_LENGTH, BIOPSY_REGIONS, ALIAS_PATTERN

logger = logging.getLogger("SpacyPreProcessor")

class SpacyPreProcessor:

    def __init__(self, model):
        self.model = model

    def catch_alias(self,sentence):
        match = re.search(r"[A-Z] [).|]",sentence)
        while match:
            sentence = sentence.replace(str(match),str(match).replace(' ',''))
            match = re.search(r"[A-Z] [).|]", sentence)
        return sentence

    def next_region_match(self,text,previous_matches):
        matches = [re.search(region, text.lower()) for region in BIOPSY_REGIONS if re.search(region, text.lower())]
        if previous_matches:
            candidates = sorted([m for m in matches if not m.start() in previous_matches],key=lambda x: x.start())
            return candidates[0] if candidates else None
        return sorted(matches,key=lambda x:x.start())[0] if matches else None

    def region_boundary_detection(self, text):

        exhausted_indicies = []
        new_lines = []
        next_region = self.next_region_match(text,exhausted_indicies)
        prev_region_match = None
        while next_region:
            if prev_region_match:
                # if we previously saw a region, insert a linebreak before the current region
                new_line = text[prev_region_match.start():next_region.start()].replace('\n',' ').strip()
                new_lines.append(new_line)
            else:
                new_lines.append(text[0:next_region.start()].replace('\n',' ').strip())
            prev_region_match = next_region
            exhausted_indicies.append(prev_region_match.start())
            next_region = self.next_region_match(text,exhausted_indicies)
        # still have to deal with previous region, just append text as it was...
        if not prev_region_match:
            # we had no region matches, just return original text
            return text
        final_addition = text[prev_region_match.start():].strip()
        new_lines.append(final_addition)

        new_text = re.sub('\n\n+','\n','\n'.join(new_lines))

        return new_text

    def alias_boundary_detection(self,text):
        compress_p = r" [A-Z] [.)]?[ \n]"
        matches = re.findall(compress_p,text)
        for match in matches:
            new = match[0:2] + match[3:]
            text = text.replace(match,new)

        p = r" [A-Z][.)]?[ \n]"
        matches = re.findall(p,text)
        for match in matches:
            if '\n' in match:
                # we want to replace this new line with a space
                new = '\n' + match[0:-1] + ' '
                text = text.replace(match,new)
            else:
                new = '\n' + match[0:]
                text = text.replace(match, new)
        text = re.sub('\n\n+','\n',text)
        text = re.sub('\n ','\n',text)
        text = re.sub('^ ','',text)
        text = re.sub(',\n',', ',text)
        text = re.sub(';\n', '; ', text)
        text = re.sub('\(\n', '( ', text)
        text = re.sub('\'\n', '\' ', text)
        return text

    def brat_tag_format(self, text):
        tokens_record = []
        sents = text.strip().split('\n')
        global_idx = 0
        for num, s in enumerate(sents):
            sent = s + '\n'

            parse = self.model(s)
            tokens_record.append(f"SENTENCE\t{global_idx}\t{global_idx + len(str(parse))}\t{str(parse)}\n")
            local_index = 0
            for i, tok in enumerate(parse):
                token = str(tok)
                start = global_idx + tok.idx
                end = start + len(token)
                pos = tok.pos_

                # we need to handle '/' chars here

                if '/' in token and len(token) > 1:
                    phrase = token.split('/')
                    sub_idx = 0
                    for i, sub_tok in enumerate(phrase):
                        sub_start = start + sub_idx
                        sub_end = sub_start + len(sub_tok)  # !!!
                        sub_text = text[sub_start:sub_end]

                        is_int = False
                        try:
                            x = int(sub_text)
                            is_int = True
                        except:
                            is_int = False
                        pos = 'NUM' if is_int else 'NOUN'
                        # write the subtok
                        if sub_tok:
                            tokens_record.append('token\t{}\t{}\t{}\t{}\n'.format(sub_text, sub_start, sub_end, pos))
                        sub_idx += len(sub_text)
                        if i < (len(phrase) - 1):
                            # write /
                            slash = text[sub_end:sub_end + 1]
                            tokens_record.append('token\t{}\t{}\t{}\t{}\n'.format(slash, sub_end, sub_end + 1, PUNCT))
                            sub_idx += 1
                else:
                    tokens_record.append('token\t{}\t{}\t{}\t{}\n'.format(text[start:end], start, end, pos))
                local_index += len(tok)
            global_idx += len(s) + 1  # account for linebreak
        return tokens_record

    def preprocess_sentences(self, input_text):
        p = self.model(input_text)
        sents = [s for s in p.sents]
        text = ''
        written_sents = 0
        words = ''
        for s in sents:
            compressed = str(s).replace('\n', ' ')
            for i, tok in enumerate(compressed.split()):
                words = words + str(tok) + ' '

            if any([words[-2] in violation for violation in ILLEGAL_ENDINGS.union(STOP_WORDS)] ): # if the final character is an illegal sentence ending don't write
                if len(words.split()) > MAX_SENTENCE_LENGTH:  # unless we are over the max sentence length
                    text = text + words[:-1] + '\n'
                    written_sents += 1
                    words = ''

            else:
                if not len(words.split()) < MIN_SENTENCE_LENGTH: # if the current sentence is over the minimum length, write it witha linebreak
                    text = text + words[:-1] + '\n'
                    written_sents+=1
                    words = ''
        text = text + words # in case the last line was too short
        text = self.region_boundary_detection(text)
        text = self.alias_boundary_detection(text).strip()

        # output brat tags format
        return text, '\n'.join(self.brat_tag_format(text))
