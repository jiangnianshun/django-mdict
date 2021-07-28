import json
import urllib.request


def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def create_deck(deck_name):
    return invoke('createDeck', deck=deck_name)


def get_decks():
    return invoke('deckNames')


note = {
    "deckName": "",
    "modelName": "Basic",
    "fields": {
        "Front": "",
        "Back": ""
    },
    "options": {
        "allowDuplicate": False,
        "duplicateScope": "deck",
        "duplicateScopeOptions": {
            "deckName": "Default",
            "checkChildren": False,
            "checkAllModels": False
        }
    },
}


def add_note(deck_name, front_content, back_content):
    note['deckName'] = deck_name
    note['fields']['Front'] = front_content
    note['fields']['Back'] = back_content
    return invoke('addNote', note=note)
