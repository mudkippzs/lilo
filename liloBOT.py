from flask import Flask, request
from pymessenger.bot import Bot
from liloFetch import *

app = Flask(__name__)

ACCESS_TOKEN = "EAAGpLsVZChDIBAKwcqZAwhJwS0zN8gRyIIt0TZAkN5Et0BxXHSaRmyCuFs6ZCKjrXiKrwO5uFhioNix6oWt1WJxdVX63W2NvygZBGDZAXnEDDzXiBrmVJdBvUZBemdJuzyZBEEkroLLwKRb2pmAHZAns7TLos60IcOTLpY1xAgVeeXgZDZD"
VERIFY_TOKEN = "liloHaveABiscuit"

bot = Bot(ACCESS_TOKEN)
rapi = rAPI_Service()
article_Service = articleService()


@app.route("/", methods=['GET', 'POST'])
def receive_message():

    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook."""
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                if message['message'].get('text'):
                    print("Checking User Text:\t" + message['message'].get('text'))
                    if '/' in message['message'].get('text'):
                        microarticle_type = 'filtered'
                        while microarticle_type is 'filtered':
                            microarticle, microarticle_type = get_message(message['message'].get('text'))
                        send_message(recipient_id, microarticle, microarticle_type)
                    else:
                        bot.send_text_message(recipient_id, "Dont do that!")
    return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

#chooses a random message to send to the user
def get_message(text):

    print("[i] Getting article...")

    print("User Text:\t" + str(text))
    user_input = text.replace('/','')
    sub_check = rapi.check_sub_exists(user_input)
    sampleArticle = False
    article_type = False
    print("SUB CHECK:\t" + str(sub_check))
    while article_type is False:
        if sub_check:
            sampleArticle = rapi.sample_article(user_input)
        else:
            sampleArticle = rapi.sample_article('theonion')

        article_type = article_Service.type_check(sampleArticle)

    return sampleArticle, article_type

#uses PyMessenger to send response to user
def send_message(recipient_id, microarticle, microarticle_type):
    #sends user the text message provided via input response parameter
    print("[i] Formatting Article...")
    response = article_Service.format_article(microarticle, microarticle_type)

    print("LINK:\t" + str(microarticle.url))

    if microarticle_type == "image":
        print("[i] Image SRC:\t" + str(microarticle.url))
        microarticle.url = microarticle.url.replace('.gifv','.gif')
        print("[i] Edited Image SRC:\t" + str(microarticle.url))
        image_formats = ['.gif','.gifv','.jpg','.jpeg','.png']
        if microarticle.url[-4:] in image_formats:
            bot.send_image_url(recipient_id, str(microarticle.url))
        else:
            print("[i] Converted image to Article: url has no img.ext")
            bot.send_generic_message(recipient_id, response)


    elif microarticle_type == "video":
        print("[i] Video SRC:\t" + str(microarticle.url))
        bot.send_video_url(recipient_id, str(microarticle.url))
    elif microarticle_type == "article":
        print("[i] Article SRC:\t" + str(microarticle.domain))
        bot.send_generic_message(recipient_id, response)

    print("[i] Response sent...")
    return "success"

if __name__ == "__main__":
    app.run(port=8000, debug=True)
