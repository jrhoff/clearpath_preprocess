import requests, time
from flask import Flask, render_template, request, jsonify
from src.cleaner import Cleaner
import spacy
from src.preprocessor import SpacyPreProcessor
from src.deidentification import filter_task, namecheck
app = Flask(__name__)

app.config['MAX_CONTENT_PATH'] = '10000000' # 10MB incase of long pathology pdfs

# tells us that when this URL is accessed
# we run the hello_world function

scispacy = spacy.load('en_core_sci_md')   # do this here to keep it loaded into memory, and may as well use for PHI too
PRODUCTION_ENDPOINT = None
TEST_ENDPOINT = None
def get_endpoints():
    endpoints = {}
    with open('endpoints.txt','r') as f:
        for line in f.readlines():
            tupl = line.strip().split()
            endpoints[tupl[0]] = tupl[1]
    
    return endpoints['production'], endpoints['test']


@app.route('/', methods=['POST'])
def split():
    """
    This endpoint expects:
        1 - a file with raw OCR text
        2 - an email address for the patient/submitter of pathology report
    :return:
    """
    PRODUCTION_ENDPOINT, TEST_ENDPOINT = get_endpoints()
    content = request.get_json()
    text, email = content['text'], content['email'].strip()

    # Remove PHI
    de_identified_text = filter_task(text, scispacy)

    # Clean text
    cleaner = Cleaner(de_identified_text)
    cleaned_text = cleaner.text

    # Finally preprocess
    preprocessor = SpacyPreProcessor(scispacy)
    text, tokens_list = preprocessor.preprocess_sentences(cleaned_text)
    m = {'text': text, 'tokens': tokens_list, 'email': email}
    response = requests.post(url=TEST_ENDPOINT, json=m)
    return response.json()



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
