import logging
import six,random,traceback, random

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractResponseInterceptor, AbstractRequestInterceptor)
from ask_sdk_core.utils import is_intent_name, is_request_type

from typing import Union, Dict, Any, List
from ask_sdk_model.dialog import (
    ElicitSlotDirective, DelegateDirective)
from ask_sdk_model import (
    Response, IntentRequest, DialogState, SlotConfirmationStatus, Slot)
from ask_sdk_model.slu.entityresolution import StatusCode
from aws_ses_email import * 
import pprint

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


valid_intents = [ "swellsuture", "jointPain",
                        "redsuture", "fever", "dailystats", "jointexercises", "bloodpressure"]

# 
intent_to_utterance = {
    "swellsuture" : "swelling around suture", 
    "jointPain" : "pain around joints",
    "redsuture" : "redness around suture",
    "fever" : "fever",
    "dailystats" : " daily stats", 
    "jointexercises": "joint exercises", 
    "bloodpressure" : " bloodpressure",
    "swellcalf" : "swelling around calf"
}

valid_completedstates = [
    "jointPain_complete",
    "swellsuture_complete",
    "redsuture_completedx",
    "fever_completedx",
    "done_with_stats",
    "jointexercises_complete",
    "bloodpressure_complete",
]


beginstates = {
    "jointPain": "jointPain_paincondition",
    "swellsuture" :"swellsuture_swell",
    "redsuture" : "redsuture_beginx",
    "fever" : "fever_beginx",
    "dailystats" : "collectstats",
    "jointexercises" : "jointexercises_doing",
    "bloodpressure" : "bloodpressure_gettingchecked"
}

valid_states = [
    "jointPain_paincondition",
    "jointPain_painscale",
    "jointPain_takingmeds",
    "jointPain_complete",
    #-----
    "swellsuture_complete",
    "swellsuture_swellimprove_ice",
    "swellsuture_swellimprove",
    "swellsuture_swell",
    "swellsuture",   # nothing known TBD DELETE THIS
    "swellcalf" ,# th enext
    #-----------
    "redsuture_beginx",
    "redsuture_improvex",
    "redsuture_improve_pusx",
    "redsuture_completedx",
    "walk",
    #-----fever
    "fever_beginx",
    "fever_collect_temp",
    "fever_completedx",
    #---------
    "collectstats",
    "done_with_stats",

    "jointexercises_doing",
    "jointexercises_complete",

    "bloodpressure_gettingchecked",
    "bloodpressure_gettingsystolic",
    "bloodpressure_gettingdiastolic",
    "bloodpressure_complete"
]

valid_slots = [
"jointPainCondition",
"jointPainScale",
"jointPainMeds",
#----------------
"swellsuture_swelling",
"swellsuture_swelling_swellimproving",
"swellsuture_swellimprove_ice",

#---------
"redsuture_yesNo",
"redsuture_improve",
"redsuture_improve_pus",
#--------------
"fever_yesNo",
"fever_temperaturex",
"fever_completedx",
#----daily stats
"patientname",
"patientdob", 
"Appetite",
"Energy",
"smoking",
"drinking",
"spirometry",

"jointexercises_yesNo",

"bloodpressure_checked",
"bloodpressure_systolic",
"bloodpressure_diastolic"
]

jointPain_state_to_slots = {
     "jointPain_paincondition": ["jointPainCondition"],
     "jointPain_painscale": ["jointPainScale"],
     "jointPain_takingmeds" :["jointPainMeds"]
}

jointexercises_state_to_slots = {
     "jointexercises_doing": ["jointexercises_yesNo"]
}

bloodpressure_state_to_slots = {
     "bloodpressure_gettingchecked": ["bloodpressure_checked"],
     "jointPain_gettingsystolic": ["bloodpressure_systolic"],
     "jointPain_gettingdiastolic" :["bloodpressure_diastolic"]
}


#Order matters ! start with general and go down . potentially more than one slot per state

swellsuture_state_to_slots = {

    "swellsuture_swell" :["swellsuture_swelling"],
    "swellsuture_swellimprove": ["swellsuture_swelling_swellimproving"],
    "swellsuture_swellimprove_ice" :["swellsuture_swellimprove_ice"]
    }

redsuture_state_to_slots = {
    "redsuture_beginx" :["redsuture_yesNo"],
    "redsuture_improvex" : ["redsuture_improve"],
    "redsuture_improve_pusx" : ["redsuture_improve_pus"]
    }
fever_state_to_slots = {
    "fever_beginx" :["fever_yesNo"],
    "fever_collect_temp" :["fever_temperaturex"]
}

def save_context(handler_input):
    current_intent_name = handler_input.request_envelope.request.intent.name
    curstate = get_statex(handler_input, current_intent_name)
    set_session_attr(handler_input, "recover_conv", "lastcontext", curstate)
    set_session_attr(handler_input, "recover_conv", "lastintent", current_intent_name)
    return None

def get_last_context(handler_input):
    intent_name = "recover_conv"
    laststatex = get_session_attr(handler_input, intent_name, "lastcontext")
    lastintent = get_session_attr(handler_input, intent_name, "lastintent")
    return lastintent, laststatex




def save_slots(handler_input, magic = 'xxyyzz'):
    # same magic for all slots
    #current_intent_name = handler_input.request_envelope.request.intent.name
    slot_dict = handler_input.request_envelope.request.intent.slots
    # copy from intent to session_attributes
    if magic not in handler_input.attributes_manager.session_attributes:
        handler_input.attributes_manager.session_attributes[magic] = {} #create it

    for slotx in slot_dict:
        if not(slotx in valid_slots):
            print("DEBUG INVALID SLOT", slotx) #
            raise
        # this is correct syntax details.value not details[value]
        slot_val = slot_dict[slotx].value
        if slotx in valid_slots and slot_val:
            handler_input.attributes_manager.session_attributes[magic][slotx] = slot_val
    save_context(handler_input)
    #print( "save", handler_input.attributes_manager.session_attributes)

def restore_slots(handler_input, magic = 'xxyyzz'):
    # first time
    saved_dict = (handler_input.attributes_manager.session_attributes.get(magic))
    if not saved_dict:
        logger.info("nothing saved")
        return
    #if magic not in handler_input.attributes_manager.session_attributes:
    #   handler_input.attributes_manager.session_attributes[magic] = {} #create it

    # copy from session_attributes to intent

    #print("restore_slots before restoring session_attrib type %s, keys%s "%(type(saved_dict),
    #                  handler_input.attributes_manager.session_attributes[magic].keys()))
    current_slots = handler_input.request_envelope.request.intent.slots
    for slotx, saved_val in saved_dict.items():
        #skip things like statex that are not valid in the handler
        if slotx not in valid_slots:
            continue
        # probably doesnt belong to this intent
        if slotx not in current_slots:
            print("restore_slots slot doesnt exist in  intent handler", slotx)
            continue
        if current_slots[slotx].value != None :
            logger.info("restore_slots not restored %s  has %s "%(slotx , current_slots[slotx].value))
            continue
        # the slot is an object . If a current value exists dont restore
        #logger.info("RESTORE_slots  for update %s %s"%(slotx, saved_val))
        handler_input.request_envelope.request.intent.slots[slotx].value = saved_val



def set_session_attr(handler_input, intent_name, keyx, valx):
    # we could get the name from handler_input.request_envelope.request.intent.name
    # but our program has already checked in ihandle
    sess_attr = handler_input.attributes_manager.session_attributes
    if intent_name not in sess_attr:
        sess_attr[intent_name] = {}
    sess_attr[intent_name][keyx] = valx
    return

def get_session_attr(handler_input, intent_name, keyx):
    sess_attr = handler_input.attributes_manager.session_attributes
    if intent_name not in sess_attr:
        sess_attr[intent_name] = {}
        return None

    valx = sess_attr[intent_name].get(keyx, None)
    return valx

def email_session_attr(handler_input,tox='kneecare.team@gmail.com',fromx='florence.nightingale.care@gmail.com'):
    name = get_session_attr(handler_input, "dailystats", "patientname")
    sess_attr = handler_input.attributes_manager.session_attributes
    body = pprint.pformat(sess_attr, indent=4)
    send_it(html = body, patientname=name, fromx=fromx, tox=tox)

"""
Each conversation goes through several states.
Each state collects one or more slots.
All conversations are initialized with a a begin state, and end in completed
In phase1 : a conversation may not be restarted if all slots are filled
In phase2 : will figure out how to restart the conversation and reset all its slots and states


"""

# Recover conversation order matters for joint pain and joint exercises
def recover_conversation(handler_input , init = False):
    statex = 'iamlost'
    restartconv = []
    #print("recover_conversation", init)
    lastintent, laststate = get_last_context(handler_input)
    # find all the conversation that have not been completed
    speech = ""
    if init:
        speech = "Hello. How are you doing today? When ready, just say 'I am ready for dailystats'. "
        return speech
    print("recover_conversation", init, speech)
    if not init :
        if lastintent and laststate:
            utterance = intent_to_utterance.get(lastintent, lastintent)
            speech += " Our last conversation was about %s . "%utterance
            if laststate not in valid_completedstates:
                speech += " we did not complete it. we could continue %s  "%(utterance)

    # TBD do a better job here
    for intentx in valid_intents:
        statex =  get_statex(handler_input, intentx)
        if statex not in valid_completedstates:
            #tbd: for now append the conversation name, we can change to english word later
            utterx = intent_to_utterance[intentx]
            restartconv.append(utterx)
        # if we found one
    random.shuffle(restartconv)
    if len(restartconv) == 1:
            speech += "Just one more item left to complete. When you are ready say %s"%(restartconv[0])
    elif len(restartconv) > 1 :
            # give two choices of keywords so that user says one of the keywords. If she responds
            # something like 'the first choice' it is TBD
        choices = ' or '.join(restartconv[:2])
        speech += "We could talk about %s . "%(choices)
        
    else:
        email_session_attr(handler_input) # need to do this only at end
        speech += """ Looks like we have all the information we need .   I have emailed your data.
                       Goodbye, DO follow your protocol and See you later tomorrow. """

    return speech

def init_beginstates(handler_input):
    for intentx  in beginstates :
        print(intentx, beginstates[intentx])
        set_statex(handler_input, intentx, beginstates[intentx])


def get_current_slot(intentx, statex):
    if intentx == 'fever' :
        state_to_slots = fever_states_to_slots
    if intentx == 'redsuture':
        state_to_slots = redsuture_state_to_slots
    if intentx == 'swellsuture':
        state_to_slots = swellsuture_state_to_slots
    if intentx == 'jointPain':
        state_to_slots = swellsuture_state_to_slots
    if intentx == 'jointexercises':
        state_to_slots = swellsuture_state_to_slots
    if intentx == 'bloodpressure':
        state_to_slots = swellsuture_state_to_slots
    assert(statex in state_to_slots)
    # TBD we have to check if the slot is filled get_resolved_value_from_handler(handler_input, slot_name)
    # dont return the first one but the one filled ?
    return state_to_slots[statex][0]

def test_statex(handler_input, intent_name = None):
    #TBD check if the statex in the handler_input is consistent with the filled slots
    # the current slot may or may not be filled but all previous ones should be
    return True

def is_current_statex(handler_input, intent_name, statexval):
    try:
        curstate = get_statex(handler_input, intent_name)
        #print("DEBUG is_current_statex ", curstate, statexval,curstate == statexval)
        assert(statexval in valid_states) # no programming error with all these strings
    except Exception as e:
        print(statexval ,e)
        return False

    return (curstate == statexval)

# state has to be without intent because we c

def get_statex(handler_input, intent_name):
    statex = get_session_attr(handler_input,intent_name, "statex")
    logger.info( "current state %s in %s \n"%(intent_name, statex))
    if statex == None:
        print(" NO STATE WRITE CONVERSATION TO FIGURE OUT WHERE TO START lost in %s "%intent_name )
        raise
        #set_statex(handler_input, intent_name,"redsuture_beginx")
        return "iamlost"
    return statex

def set_statex(handler_input, intent_name, statexval):
    assert(statexval in valid_states)
    set_session_attr(handler_input,intent_name, "statex",statexval)
    assert(is_current_statex(handler_input, intent_name, statexval)) # readit after setting
    return

def random_phrase(str_list):
    """Return random element from list."""
    # type: List[str] -> str
    return random.choice(str_list)

# Utility functions

def get_resolved_value(handler_input, slot_name):
    #Resolve the slot name from the request using resolutions.
    # type: (IntentRequest, str) -> Union[str, None]
    request = handler_input.request_envelope.request
    try:
        return (request.intent.slots[slot_name].resolutions.
                resolutions_per_authority[0].values[0].value.name)
    except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
        logger.info("Couldn't resolve {} for request: {}".format(slot_name, request))
        logger.info(str(e))
        return None


def get_raw_value(handler_input, slot_name):
    #Resolve the slot name from the request using resolutions.
    # type: (IntentRequest, str) -> Union[str, None]
    request = handler_input.request_envelope.request
    try:
        return (request.intent.slots[slot_name].value)
    except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
        logger.info("Couldn't find raw value for {} for request: {}".format(slot_name, request))
        logger.info(str(e))
        return None

# done know why this works
def get_resolved_value_from_handler(handler_input, slot_name):
    #return get_resolved_value(handler_input.request_envelope.request, slot_name)
    assert(slot_name in valid_slots)
    grv = get_resolved_value(handler_input, slot_name)
    allslots = get_allslot_value_from_handler(handler_input)
    slotx  = allslots.get(slot_name,None)
    val = None
    if slotx and slotx.get('is_validated', False):
        val = slotx.get('resolved', None)
    #hack
    #if slotx and slotx.get('value', None):
    #    val = slotx.get('value')
    print("DEBUG get_resolved_value_from_handler  ", val,slot_name, slotx)
    print("DEBUG get_resolved_value " , slot_name, grv )
    # for numbers we have a problem there is no resilution
    if val == None :
        val = get_raw_value(handler_input, slot_name)
        print("DEBUG get_resolved_value_from_handler fallback to  raw value", slot_name , val, slotx)
    return val




def get_allslot_value_from_handler(handler_input):
    filled_slots = handler_input.request_envelope.request.intent.slots
    allslots = get_slot_values(filled_slots)
    print("DEBUG SLOTS %s"%allslots)
    return allslots


def get_slot_values(filled_slots):
    """Return slot values with additional info."""
    # type: (Dict[str, Slot]) -> Dict[str, Any]
    slot_values = {}
    #logger.info("Filled slots: {}".format(filled_slots))

    # not sure if jey and slot_item.name are same. It seems to be
    for key, slot_item in six.iteritems(filled_slots):
        name = slot_item.name
        try:
            status_code = slot_item.resolutions.resolutions_per_authority[0].status.code

            if status_code == StatusCode.ER_SUCCESS_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.resolutions.resolutions_per_authority[0].values[0].value.name,
                    "is_validated": True,
                }
            elif status_code == StatusCode.ER_SUCCESS_NO_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.value,
                    "is_validated": False,
                }
            else:
                pass
        except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
            logger.info("Couldn't resolve status_code for slot item: {}".format(slot_item))
            logger.info(e)
            slot_values[name] = {
                "synonym": slot_item.value,
                "resolved": slot_item.value,
                "is_validated": False,
            }
    return slot_values
