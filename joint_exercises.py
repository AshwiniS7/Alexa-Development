# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""

intent
    jointexercises

handler
    jointexercises_doing_handler
    jointexercises_do_complete

state The dialog can get completed in any state. So we have to have a completed sate
    "jointexercises_doing"  - swelling known or trying to get it to it
    "jointexercises_complete"


slot names
    jointexercises_yesNo

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
class jointexercises_doing_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("jointexercises")(handler_input)  and
                  get_statex(handler_input,"jointexercises") == "jointexercises_doing" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test
    def handle(self, handler_input):
        #if improve ice are filled simply delegate to go get next slot, if completed it will go to complete
        # we should have all the slots here
        current_intent = handler_input.request_envelope.request.intent

        #if ice is not filled, reprompt for ice
        logger.info("In jointexercises_doing_handler")
        cur_slot_name = "jointexercises_yesNo"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "jointexercises"
        statex = get_statex(handler_input,cur_intent_name)

        logger.info("In jointexercises_doing_handler State :%s cur_slot_value   %s"%(statex, cur_slot_value))

        if not cur_slot_value in ('yes', 'no'):
            prompt = "Did you do your joint exercises?"
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit= cur_slot_name, updated_intent=current_intent)
              ).response
        else:
            # we have a value save it
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value)

            #TBD congrat APPLYING ICE IS COOLEST THING TO DO
            # move on to next slot but there is none this should take to completed
            if debug :
                print("expect dialog complete")
                test_statex(handler_input, cur_intent_name) # should pass all slots filled

            # this setting state to co,plete is probably wring not clear

            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED #nothing more

            return jointexercises_do_complete(handler_input)

            """
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response"""

def jointexercises_do_complete(handler_input):
    logger.info(" COMPLETING jointexercises_do_complete")
    test_statex(handler_input,"jointexercises")

    set_statex(handler_input,"jointexercises", "jointexercises_complete")
    save_slots(handler_input, "jointexercises") # dialog completed  why save
    filled_slots = handler_input.request_envelope.request.intent.slots
    slot_values = get_slot_values(filled_slots)

    try:
        # TBD move as a session variable and build in pieces
        # not doing joint exercises
        speech = ("""Joint exercises is a {}.
                   """ .format(slot_values["jointexercises_yesNo"]["resolved"]) )

        if (slot_values["jointexercises_yesNo"]["resolved"] == "no"):
            # has bad joint pain
            if (get_session_attr(handler_input, "jointPain", "jointPainCondition") == "bad"):
                # has not been taking meds
                if (get_session_attr(handler_input, "jointPain", "jointPainMeds") == "no"):
                    speech+=" Please take your pain meds and resume exercise. "
                # has been taking meds
                else:
                    speech+=" That isn't good. Let me contact your physician. "
            # doesn't have joint pain
            else:
                speech+=" Please do your exercises regularly. "


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

'''
class CompletedSwellSutureIntent(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        # we cant test for statex because dialog can end in any statex
        return (is_intent_name("swellsuture")(handler_input)
            and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In Completed swellsuture")
        completed_resp = swellsuture_do_complete(handler_input)
        return completed_resp
#
'''
