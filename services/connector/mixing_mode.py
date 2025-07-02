import json



#mixing mode functions
def send_to_tts(output):
    print(output)

#mixing mode main
def start_mixing(rezept):

    #startup
    rezept = open('trial_json.txt')
    print("Starting mixing")
    x = json.load(rezept)

    send_to_tts(cocktail_name)

if __name__ == "__main__":
    start_mixing("usp")