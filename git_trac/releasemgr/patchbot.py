import requests

def patchbot_status(ticket_number):
    r = requests.get('https://patchbot.sagemath.org/ticket/{}/status'.format(ticket_number))
    return r.text
