import requests

def patchbot_status(ticket_number):
    # until https://github.com/sagemath/sage-patchbot/pull/150 is merged:
    r = requests.get('https://patchbot.sagemath.org/ticket/{}/status.svg'.format(ticket_number))
    if "0.0507-64.833-64.833 46.117-46.117" in r.text:
        return "TestsPassed"
    return "TestsFailed"
