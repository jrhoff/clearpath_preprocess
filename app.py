from flask import Flask, render_template, request, jsonify
from src.cleaner import Cleaner
import spacy
from src.preprocessor import SpacyPreProcessor
from src.deidentification import filter_task, namecheck
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'UPLOADS/'
app.config['MAX_CONTENT_PATH'] = '10000000'

# tells us that when this URL is accessed
# we run the hello_world function

scispacy = spacy.load('en_core_sci_md')   # do this here to keep it loaded into memory?
#eng_spacy = spacy.load('en_core_web_sm')  # load spacy english library
@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/submission_form')
def submission():
    return render_template('upload.html')


@app.route('/handle_submission', methods=['POST'])
def split():
    if request.method == 'POST':
        f = request.files['file']
        text = f.read().decode("utf-8")
        # Remove PHI
        de_identified_text = filter_task(text, scispacy)

        # Clean text
        cleaner = Cleaner(de_identified_text)
        cleaned_text = cleaner.text

        # Finally preprocess
        preprocessor = SpacyPreProcessor(scispacy)
        text, tokens_list = preprocessor.preprocess_sentences(cleaned_text)
        m = {'text': text, 'tokens': tokens_list}
        return jsonify(m)

    return 0
