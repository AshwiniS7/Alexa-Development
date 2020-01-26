# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""

intent
    bloodpressure

handler
    bloodpressure_checked_handler
    bloodpressure_systolic_handler
    bloodpressure_diastolic_handler
    bloodpressure_do_complete

state The dialog can get completed in any state. So we have to have a completed sate
    "bloodpressure_gettingchecked"
    "bloodpressure_gettingsystolic"
    "bloodpressure_gettingdiastolic"
    "bloodpressure_complete"


slot names
    bloodpressure_checked
    bloodpressure_systolic
    bloodpressure_diastolic

we will use the same slot names for sess_attributes

functions
    get_attr

TBD
    see the get_slots how they checked for resolutions
    restore and save slots to be done by intent to prevent a lot of overcrowding

"""

import logging
import requests
import six
import random

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractResponseInterceptor, AbstractRequestInterceptor)
from ask_sdk_core.utils import is_intent_name, is_request_type

from typing import Union, Dict, Any, List
from ask_sdk_model.dialog import (
    ElicitSlotDirective, DelegateDirective)
from ask_sdk_model.dialog.confirm_intent_directive import ConfirmIntentDirective
from ask_sdk_model import (
    Response, IntentRequest, DialogState, SlotConfirmationStatus, Slot)
from ask_sdk_model.slu.entityresolution import StatusCode

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)

debug = 1


from utils import *
#https://alexa-skills-kit-python-sdk.readthedocs.io/en/latest/api/core.html#ask_sdk_core.attributes_manager.AttributesManager
# three level attributes: request, session and persistence. request is not useful to us. persistence is database

# Request Handler classes
# LaunchRequestHandler is once per skill not per intent


# Particular to general
# suture +swellswellimprove_ice basically completes the conversation
# suture + ice
# everything
# type: (HandlerInput) -> bool
"""
        Be careful
        1. if a one shot is used the dialog state will be STARTED.
        2. Delegate will result in completed but never on elicit.
        3. We need to check this even if state is COMPLETED because shade is not mandatory, so we
           will get completed even if shade is not filled
"""
#last handler only ice
class bloodpressure_diastolic_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("bloodpressure")(handler_input)  and
                  get_statex(handler_input,"bloodpressure") == "bloodpressure_gettingdiastolic" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test
    def handle(self, handler_input):
        #if improve ice are filled simply delegate to go get next slot, if completed it will go to complete
        # we should have all the slots here
        current_intent = handler_input.request_envelope.request.intent

        #if ice is not filled, reprompt for ice
        logger.info("In bloodpressure_diastolic_handler")
        cur_slot_name = "bloodpressure_diastolic"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "bloodpressure"
        statex = get_statex(handler_input,cur_intent_name)

        logger.info("In bloodpressure_diastolic_handler State :%s cur_slot_value   %s"%(statex, cur_slot_value))

        if cur_slot_value == None  :

            # TBD prompt
            prompt = "What is your diastolic pressure? I have %s "%(cur_slot_value)
            reprompt = "What did your monitor read"
            print("debug prompt", prompt, reprompt)
            print("debug", type(cur_slot_value))
            return handler_input.response_builder.speak(
              prompt).ask(reprompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response

        # not improving
        else :
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value)
            # move on to next slot but there is none this should take to completed
            if debug: test_statex(handler_input,"bloodpressure")

            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED #nothing more
            # no further states , complete
            #set_statex(handler_input,"fever", "fever_completedx")

            #save_slots(handler_input,'fever' )
            return bloodpressure_do_complete(handler_input)

# handler get swellimproves , jumps out, or proceeds
class bloodpressure_systolic_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("bloodpressure")(handler_input)  and
                  get_statex(handler_input, "bloodpressure") == "bloodpressure_gettingsystolic" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In bloodpressure_systolic_handler")
        current_intent = handler_input.request_envelope.request.intent

        test_statex(handler_input, "bloodpressure")
        # get the swell improvement from the slot and save it in session attributes
        cur_slot_name = "bloodpressure_systolic"
        next_slot = "bloodpressure_diastolic"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "bloodpressure"

        print(" DEBUG bloodpressure_systolic", cur_slot_value)


        # talking about swelling is improvong
        if cur_slot_value == None:
            # TBD prompt
            prompt = "What is your systolic pressure?"
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response

        # not improving
        else:
            # go to icing.
            # TBD remove this and see if it will go to icing by default on delegate directive
            prompt = "That is good to know. Now, what is your diastolic pressure?"
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value)
            # move to next state
            set_statex(handler_input,cur_intent_name, "bloodpressure_gettingdiastolic")
            save_slots(handler_input,cur_intent_name)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot, updated_intent=current_intent)
              ).response

class bloodpressure_checked_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("bloodpressure")(handler_input)  and
                  get_statex(handler_input,"bloodpressure") == "bloodpressure_gettingchecked" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        current_intent = handler_input.request_envelope.request.intent
        # get the swell improvement from the slot and save it in session attributes
        cur_slot_name = "bloodpressure_checked"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "bloodpressure"
        logger.info("In bloodpressure_checked_handler slotval : %s"%cur_slot_value)
        # we are talkign about the value of swelling

        if cur_slot_value not in ('yes', 'no'):
            logger.info("In bloodpressure_checked_handler not getting value reprompting ")
            prompt = "Please respond with a yes or no. Have you checked your blood pressure?"
            save_slots(handler_input,cur_intent_name)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response
        # no swelling we are done
        elif cur_slot_value == 'no':
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value)
            # no further states
            print("COMPLETED DIALOG\n")
            #we have a bug this doesnt really work because state is not set to completed
            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            save_slots(handler_input,cur_intent_name)
            # changes state and moves on to next intent
            return bloodpressure_do_complete(handler_input)
            """ This thing messes up by getting delegation to extract one more piece of info
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response
            """
        elif cur_slot_value == 'yes':
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value)
            # TBD proper noise on swelling
            set_statex(handler_input, cur_intent_name,'bloodpressure_gettingsystolic')
            save_slots(handler_input,cur_intent_name)

            prompt = "Oh that's great! What is your systolic pressure?"
            next_slot = 'bloodpressure_systolic'
            assert(next_slot in valid_slots)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot,
              updated_intent=current_intent)
              ).response



def bloodpressure_do_complete(handler_input):
    logger.info(" COMPLETING bloodpressure_do_complete")
    test_statex(handler_input,"bloodpressure")

    set_statex(handler_input,"bloodpressure", "bloodpressure_complete")
    save_slots(handler_input, "bloodpressure") # dialog completed  why save
    filled_slots = handler_input.request_envelope.request.intent.slots
    slot_values = get_slot_values(filled_slots)

    try:
        # TBD move as a session variable and build in pieces
        speech = ("""Blood pressure is a {}.
                   """ .format(slot_values["bloodpressure_checked"]["resolved"]) )

        if (slot_values["bloodpressure_checked"]["resolved"] == "yes"):
            diastolic = int(slot_values["bloodpressure_diastolic"]["resolved"])
            systolic = int(slot_values["bloodpressure_systolic"]["resolved"])
            flag = 0

            if (systolic > 110 and systolic < 140):
                speech+=" Systolic pressure is in good range. "
            else:
                speech+=" Systolic pressure is out of range. "
                flag = 1

            if (diastolic > 60 and diastolic < 80):
                speech+=" Diastolic pressure is in good range. "
            else:
                speech+=" Diastolic pressure is out of range. "
                flag = 1

            if flag:
                speech+=" Let me contact your physician. "

        next_conv = recover_conversation(handler_input , init = False)
        speech += next_conv
        # TBD smart way to set something set_statex(handler_input, "swell", "swellcalf")

    except Exception as e:
        speech = ("I am really sorry. I am unable to access part of my "
                      "memory. Please try again later")
        logger.info("Intent: {}: message: {}".format(
              handler_input.request_envelope.request.intent.name, str(e)))

    # this permits transition to other intents
    current_intent = handler_input.request_envelope.request.intent
    return handler_input.response_builder.speak(speech).add_directive(
            ConfirmIntentDirective(
                updated_intent=current_intent
            )).response

    # blocks transition return handler_input.response_builder.speak(speech).response
