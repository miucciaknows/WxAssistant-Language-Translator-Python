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
assistant_authenticator = IAMAuthenticator(API_Key_WA)
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

# Context to maintain the conversation between user and WA.
context = {}

# Get all available languages for translation
languages = language_translator.list_identifiable_languages().get_result()

# Print the available languages and their codes
print("Languages Available:")
for lang in languages['languages']:
    print(f"- {lang['name']} ({lang['language']})")

# Ask the user which language they want to converse in
user_language_code = input(
    "Please provide the code of the language that you would like to talk with me. Example: de fuer Deutscher, pt para Português, en for English. ONLY DE CODE, PLEASE: ").lower()

# Get the user chosen language
user_language = [lang for lang in languages['languages']
                 if lang['language'] == user_language_code]

# Check if the chosen language exists
if not user_language:
    print("Sorry, I do not get it. Please try again with a valid code. ")
    exit()

# Variables to store translations of 'you' and 'Assistente'
you_translation = None
assistant_translation = None

# Translate the word 'você' to the chosen language via English
you_text_pt = 'você'
translation = language_translator.translate(
    text=you_text_pt,
    source='pt',
    target='en'
).get_result()


you_translation = language_translator.translate(
    text=translation['translations'][0]['translation'],
    source='en',
    target=user_language_code
).get_result()['translations'][0]['translation']

# Insert the translated word 'você' into the input message for the Assistant
message_input['text'] = you_translation

# Input/output loop
while message_input['text'] != 'quit':

    # Get user input in the chosen language
    user_input_code = input(f'{you_translation}:  ')

    # Translate user input to English
    translation = language_translator.translate(
        text=user_input_code,
        source=user_language_code,
        target='en'
    ).get_result()

    user_input_en = translation['translations'][0]['translation']

    # Send translated input to the Assistant.
    message_input['text'] = user_input_en

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
        assistant_response_en = "Sorry, i don't get it the Assistant response"

    # Detect the language of the Assistant's response
    detected_language = language_translator.identify(
        text=assistant_response_en
    ).get_result()

    # Get the detected language code
    detected_language_code = detected_language['languages'][0]['language']

    # Translate the Assistant's response to the chosen language via English
    translation = language_translator.translate(
        text=assistant_response_en.strip(),
        source='en',
        target=user_language_code  # Translate back to the chosen language
    ).get_result()

    assistant_response_user_lang = translation['translations'][0]['translation']

    # Print the Assistant's response in the chosen language
    print(
        f"Assistente ({user_language[0]['name']}):", assistant_response_user_lang)

    time.sleep(1)
