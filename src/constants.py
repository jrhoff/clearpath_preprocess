"""
OCR Post processing constants are here...
"""
text_numbers = {"one": '1',
                'two': '2',
                'three': '3',
                'four': '4',
                'five': '5',
                'six': '6',
                'seven': '7',
                'eight': '8',
                'nine': '9',
                'ten': '10'}


violations = [
    (r"\r", '\n'),    # replace carriage turns with linux linebreak
    (r"\t", ' '),     # replace tab with space,
    (r"_+", ''),      # get rid of underscore streaks, they are useless to us
    (r"\+", " + "),   # pad all '+' with spaces,
    (r"=", " = "),    # pad all '=' with spaces,
    (r"[cC][mM]", " cm "),    # Try to pad all 'cm' measurements with space, remove double spaces later, #todo mistake here, but kept in bc annotated with it
    (r"\([^\n]", " ( "),
    (r"\)", " ) "),    # pad all parentheses with spaces, we will treat them as tokens
    (r"= +\n", "= "),  # don't allow linebreaks inside equations equations
    (r"  +", ' '),  # replace multi-spaces with one space
    (r"^\n", ''),     # remove empty lines
    (r'Gl[^ ]+on ', 'Gleason '), # Some Gleason mispellings
    (r'gl[^ ]+on ', 'gleason '),  # Some Gleason mispellings (lower)
    (r"8enign", "Benign"),       # Common 'Benign' misread
    (r" +\n", '\n'),      # remove line-final spaces
    (r"\n +", '\n'),       # remove line-intitial spaces
    (r"^ ", ''),
    (r"\n\n+", '\n')
]

# "equation regex":{index : ideal character replacement}

invalid_LHS = r"\b[^ )('\"] \+ [^ )('\"] " ## possibly invalid*

# this is a tuple list to preserve ordering
EQUATIONS = [

    (r"\b[0-9] [+4] [0-9] .{1} [0-9]+\b", "PLUSEQUAL"),               # Assume the first 2 #s are correct, check if we mis-identified '+' or '=',
    (r"\b[0-9]{2} \+ [0-9] = [0-9]+\b", "LHDD"),                     # Check for lefthand double digits
    (r"\b[0-9] \+ [0-9]{2} = [0-9]+\b", "RH_DD"),                     # Check for righthand double digits
    (invalid_LHS + r"[^ )(=]\b", 'INSERT'),                       # check if we are missing the '=' symbol
    (invalid_LHS + r"= [^ )(]{1}", 'ALPHANUM'),                      # Check if we have letters instead of numbers in gleason scores
    (r"\b[0-9] \+ [0-9] = [0-9]+", 'SUM'),                            # Check if all sums are correct

    ## Begin #(# + #) type equations

    (r"\b[0-9] \( [0-9] \+ [0-9] \)|\b[0-9] \( [0-9] *4 *[0-9] \)","GLOB_PLUSEQUAL"),
    (r"\b[0-9] \( [0-9] \+ [0-9] \)", "GLOB_SUM"),
    (r"\b[^ ]+ \( [^ ]+ \+ [^ ]+ \)", "GLOB_ALPHANUM"),
    (r"\b[0-9] \( [0-9]{2} \+ [0-9] \)", "GLOB_LHDD"),                     # Check for lefthand double digits
    (r"\b[0-9] \( [0-9] \+ [0-9]{2} \)", "GLOB_RHDD")                     # Check for righthand double digits

]



special_char_replacement = {
    '§':{'NUM':' 5', 'ALPHA': 'S'},
    '$':{'NUM': '5', 'ALPHA': 'S'},
    'β':{'NUM': '8', 'ALPHA': 'B'},
    'ϐ':{'NUM': '9', 'ALPHA': 'B'}
}

MATH_CONTEXT_INDICATORS = "[:()+={}0-9]"

REGION_KEYWORDS = ['right', 'left', "base", "mid", "apex", "apical", "medial", "lateral", "seminal", "vesicle", 'lesion']


"""
Pre-processing Constants start here
"""

ILLEGAL_ENDINGS = set([":\(\*-+%)"])
MIN_SENTENCE_LENGTH = 2 # tokens*
MAX_SENTENCE_LENGTH = 5000


BASIC_REGIONS = ["base", "mid", "apex"]

MODIFIERS = ["apical", "medial", "lateral"]

BIOPSY_REGIONS = [" right " + r for r in BASIC_REGIONS] + \
                 [" left "  + r for r in BASIC_REGIONS] + \
                 [" right " + m + ' ' + r for r in BASIC_REGIONS for m in MODIFIERS] + \
                 [" left " + m + ' ' + r for r in BASIC_REGIONS for m in MODIFIERS] + \
                 [" right " + r + ' ' + m for r in BASIC_REGIONS for m in MODIFIERS] + \
                 [" left " + r + ' ' + m for r in BASIC_REGIONS for m in MODIFIERS] + \
                 [" right seminal vesicle", " left seminal vesicle","lesion"]
# a set of patterns that we want to denote where a new line should start (before) have represented in a single vector for a biopsy region


ALIAS_PATTERN = r"\s[A-Z][.) \n]"