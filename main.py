
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import LanguageTranslatorV3

import time
import os

# Enviroments variables
from dotenv import load_dotenv
load_dotenv()


API_Key_Translator = os.environ["API_Key_Translator"]
Url_Translator = os.environ["Url_Translator"]

API_Key_WA = os.environ["API_Key_WA"]
URL_Assistant = os.environ["URL_Assistant"]
ID_Assistant = os.environ["ID_Assistant"]

# Creating Assistant service object.
assistant_authenticator = IAMAuthenticator(
    API_Key_WA)
assistant = AssistantV2(
    version='2021-11-27',
    authenticator=assistant_authenticator
)
assistant.set_service_url(URL_Assistant)
assistant_id = ID_Assistant

# Creating Language Translator service object.
lt_authenticator = IAMAuthenticator(API_Key_Translator)
language_translator = LanguageTranslatorV3(
    version='2018-05-01',
    authenticator=lt_authenticator
)
language_translator.set_service_url(Url_Translator)

# Starting with empty message to start the conversation.
message_input = {
    'message_type': 'text',
    'text': ''
}

# Contex to maintain the conversation between user and WA.
context = {}

# input/output loop
while message_input['text'] != 'quit':

    # Get user input in Portuguese
    user_input_pt = input('Você: ')

    # Translate user input from Portuguese to English
    translation = language_translator.translate(
        text=user_input_pt,
        source='pt',
        target='en'
    ).get_result()

    user_input_en = translation['translations'][0]['translation']

    # Sending translated input to the Assistant.
    message_input['text'] = user_input_en

    # I'm using this loop below to handle with multiple responses coming from NeuralSeek.
    complete_response = False
    assistant_response_en = ''

    while not complete_response:
        result = assistant.message_stateless(
            assistant_id,
            input=message_input,
            context=context
        ).get_result()

        context = result['context']

        if 'output' in result and 'generic' in result['output']:
            generic_responses = result['output']['generic']
            if generic_responses and len(generic_responses) > 0:
                for response in generic_responses:
                    if response['response_type'] == 'text':
                        assistant_response_en += response['text'] + ' '
                    elif response['response_type'] == 'pause':
                        time.sleep(response['time'])
                    elif response['response_type'] == 'option':
                        assistant_response_en += ' '.join(
                            response['values']) + ' '

        complete_response = 'generic' in result['output'] and len(
            result['output']['generic']) > 0 and not result['output']['generic'][0].get('more_to_come', False)

    if not assistant_response_en.strip():
        # Sorry, i did not understand Assistant's answer.
        assistant_response_en = "Desculpe, não entendi a resposta do assistente."
        #

    # Translate Assistant's response back to Portuguese
    translation = language_translator.translate(
        text=assistant_response_en.strip(),
        source='en',
        target='pt'
    ).get_result()

    assistant_response_pt = translation['translations'][0]['translation']

    # Assistant's response in Portuguese
    print("Assistente:", assistant_response_pt)

    # Waiting for a moment before allowing the user to input again
    time.sleep(1)
