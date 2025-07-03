from intervention.models import MBTIQuestion

QUESTIONS = [
    # EI
    ("You find it easy to introduce yourself to other people.", "EI"),
    ("You prefer group activities over solitary ones.", "EI"),
    # SN
    ("You are more interested in facts than ideas.", "SN"),
    ("You trust experience more than theoretical alternatives.", "SN"),
    # TF
    ("You make decisions based on logic, not feelings.", "TF"),
    ("You value justice over mercy.", "TF"),
    # JP
    ("You prefer to have a to-do list.", "JP"),
    ("You like to have things decided rather than open-ended.", "JP"),
]

def run():
    for text, dichotomy in QUESTIONS:
        MBTIQuestion.objects.get_or_create(text=text, dichotomy=dichotomy)
    print("MBTI questions added.") 