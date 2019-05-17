# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This sample shows how to use different types of rich cards.
"""
import copy
import json
from aiohttp import web
from botbuilder.schema import (Activity, ActivityTypes, Attachment,
                               ActionTypes, CardAction,
                               CardImage, MediaUrl, ThumbnailUrl,
                               Fact)
from botbuilder.core import (BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext,
                             ConversationState, MemoryStorage, UserState, CardFactory)
"""Import AdaptiveCard content from adjacent file"""


APP_ID = ''
APP_PASSWORD = ''
PORT = 9000
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Create MemoryStorage, UserState and ConversationState
memory = MemoryStorage()
# Commented out user_state because it's not being used.
# user_state = UserState(memory)
conversation_state = ConversationState(memory)

# Register both State middleware on the adapter.
# Commented out user_state because it's not being used.
# ADAPTER.use(user_state)
ADAPTER.use(conversation_state)


# Methods to generate cards

# Reads in json files, used to create adaptive cards
def read_in_jsons():
    with open ("fightercard.json", "rb") as file_in:
        fight_card_json = json.load(file_in)
    with open("ufc_237_fighters.json", "rb") as file_in:
        fighter_information = json.load(file_in)
    return fight_card_json, fighter_information
    
# Returns list of json formatted adaptive cards for each fight_card_dicts
# List also contains information used by create_menu_string():
def create_fightnight_cards(fight_card_json, fighter_information):
    fights = []
    for k, v in fighter_information.items():
    # red corner data
        fight = copy.deepcopy(fight_card_json)
    
        fight["body"][0]["items"][0]["columns"][0]['items'][0]['text'] = v["red_corner"]["nickname"]
        fight["body"][0]["items"][0]["columns"][0]['items'][1]['text'] =v["red_corner"]["fullname"]
        fight["body"][0]["items"][0]["columns"][0]['items'][2]['url'] = v["red_corner"]["img_url"]
        fight["body"][0]["items"][0]["columns"][0]['items'][3]['facts'][0]['value'] = v["red_corner"]["record"]
        fight["body"][0]["items"][0]["columns"][0]['items'][3]['facts'][1]['value'] = v["red_corner"]["country"]
        fight["body"][0]["items"][0]["columns"][0]['items'][3]['facts'][2]['value'] = v["red_corner"]["height"]
        fight["body"][0]["items"][0]["columns"][0]['items'][3]['facts'][3]['value'] = v["red_corner"]["reach"]

    #blue corner data
        fight["body"][0]["items"][0]["columns"][2]['items'][0]['text'] = v["blue_corner"]["nickname"] 
        fight["body"][0]["items"][0]["columns"][2]['items'][1]['text'] = v["blue_corner"]["fullname"] 
        fight["body"][0]["items"][0]["columns"][2]['items'][2]['url'] = v["blue_corner"]["img_url"] 
        fight["body"][0]["items"][0]["columns"][2]['items'][3]['facts'][0]['value']= v["blue_corner"]["record"]
        fight["body"][0]["items"][0]["columns"][2]['items'][3]['facts'][1]['value']= v["blue_corner"]["country"]
        fight["body"][0]["items"][0]["columns"][2]['items'][3]['facts'][2]['value']= v["blue_corner"]["height"]
        fight["body"][0]["items"][0]["columns"][2]['items'][3]['facts'][3]['value'] = v["blue_corner"]["reach"]

    #bout data
        fight["body"][0]["items"][0]["columns"][1]['items'][0]['text'] = v["weight_class"]
        fight["body"][0]["items"][0]["columns"][1]['items'][1]['text'] = v["bout_type"]
    
        keywords = ["%s" % (v["red_corner"]["fullname"]),
                    "%s" % (v["blue_corner"]["fullname"]),
                    "%s vs. %s" % (v["red_corner"]["fullname"], v["blue_corner"]["fullname"])]
    
        fights.append([fight, keywords, v["fight_number"]])
        
    return(fights)  

# Creates string to displayed in menu card that lists fights
def create_menu_string():
    fight_card_template, fight_info = read_in_jsons()
    fight_card_dicts = create_fightnight_cards(fight_card_template, fight_info)
    menu_string = "Which fight would you like to see?\n"
    counter = 1
    for i in fight_card_dicts:
        s = "(%d) %s\n" % (i[2], i[1][2])
        counter += 1
        menu_string = menu_string + s
        
    return(menu_string)
  
async def create_reply_activity(request_activity: Activity, text: str, attachment: Attachment = None) -> Activity:
    activity = Activity(
        type=ActivityTypes.message,
        channel_id=request_activity.channel_id,
        conversation=request_activity.conversation,
        recipient=request_activity.from_property,
        from_property=request_activity.recipient,
        text=text,
        service_url=request_activity.service_url)
    if attachment:
        activity.attachments = [attachment]
    return activity


async def handle_message(context: TurnContext) -> web.Response:
    # Access the state for the conversation between the user and the bot.
    state = await conversation_state.get(context)
    if hasattr(state, 'in_prompt'):
        if state.in_prompt:     
            state.in_prompt = False
            return await card_response(context)
            
        else:
            state.in_prompt = True
            menu_text =  create_menu_string()
            prompt_message = await create_reply_activity(context.activity, menu_text)
            await context.send_activity(prompt_message)
            return web.Response(status=202)
    else:
        state.in_prompt = True
        menu_text =  create_menu_string()
        prompt_message = await create_reply_activity(context.activity, menu_text)
        await context.send_activity(prompt_message)
        return web.Response(status=202)


async def card_response(context: TurnContext) -> web.Response:
    response = context.activity.text.strip()

# Creates choice dictionary for users to determine which fight they want to see
# Numbers, <Red Corner> vs. <Blue Corner>, <Red_Corner>, and <Blue_Corner> all accepted    
    fight_card_json, fighter_information = read_in_jsons()
    fight_night = create_fightnight_cards(fight_card_json, fighter_information)
    choice_dict = {}
    for i in fight_night:
        choice_dict[str(i[2])] = i[0]
        for j in i[1]:
            choice_dict[j] = i[0]

    # If the stripped response from the user is not found in our choice_dict, default to None
    choice = choice_dict.get(response, None)
    # If the user's choice was not found, respond saying the bot didn't understand the user's response.
    if not choice:
        not_found = await create_reply_activity(context.activity, 'Sorry, I didn\'t understand that. :( Please try again.')
        await context.send_activity(not_found)
        return web.Response(status=202)
    else:
        card = CardFactory.adaptive_card(choice)
        # for func in choice:
            # card = func()
        response = await create_reply_activity(context.activity, '', card)
        await context.send_activity(response)
        return web.Response(status=200)


async def handle_conversation_update(context: TurnContext) -> web.Response:
    if context.activity.members_added[0].id != context.activity.recipient.id:
        response = await create_reply_activity(context.activity, 'Hello fight fan! I\'m the Fight Night Bot, ' +
                                               'here to give you all of the important details about upcoming combat sports events.\n\n' +
                                               'Type anything to see who is fighting on the main card.')
        await context.send_activity(response)
    return web.Response(status=200)


async def unhandled_activity() -> web.Response:
    return web.Response(status=404)


async def request_handler(context: TurnContext) -> web.Response:
    if context.activity.type == 'message':
        return await handle_message(context)
    elif context.activity.type == 'conversationUpdate':
        return await handle_conversation_update(context)
    else:
        return await unhandled_activity()


async def messages(req: web.web_request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers['Authorization'] if 'Authorization' in req.headers else ''
    try:
        return await ADAPTER.process_activity(activity, auth_header, request_handler)
    except Exception as e:
        raise e


app = web.Application()
app.router.add_post('/', messages)

try:
    web.run_app(app, host='localhost', port=PORT)
except Exception as e:
    raise e
