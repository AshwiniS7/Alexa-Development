# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""

intent
    jointPain

handler
    jointPain_paincondition_handler
    jointPain_painscale_handler
    jointPain_takingmeds_handler
    jointPain_do_complete
    CompletedjointPainIntent

state The dialog can get completed in any state. So we have to have a completed sate
    "jointPain_beginx"   -- nothing known
    "jointPain_paincondition"  - swelling known or trying to get it to it
    "jointPain_painscale"
    "jointPain_takingmeds"
    "jointPain_complete"


slot names
    jointPainCondition
    jointPainScale
    jointPainMeds

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
class jointPain_takingmeds_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("jointPain")(handler_input)  and
                  get_statex(handler_input,"jointPain") == "jointPain_takingmeds" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test
    def handle(self, handler_input):
        #if improve ice are filled simply delegate to go get next slot, if completed it will go to complete
        # we should have all the slots here
        current_intent = handler_input.request_envelope.request.intent

        #if ice is not filled, reprompt for ice
        logger.info("In jointPain_takingmeds_handler")
        cur_slot_name = "jointPainMeds"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "jointPain"
        statex = get_statex(handler_input,cur_intent_name)

        logger.info("In jointPain_takingmeds_handler State :%s cur_slot_value   %s"%(statex, cur_slot_value))

        if not cur_slot_value in ('yes', 'no'):
            prompt = "I dont understand the response %s . Could you reply with a yes nor no . Did you take your meds?"%(cur_slot_value)
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

            return jointPain_do_complete(handler_input)

            """
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response"""
# handler get swellimproves , jumps out, or proceeds
class jointPain_painscale_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("jointPain")(handler_input)  and
                  get_statex(handler_input, "jointPain") == "jointPain_painscale" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In jointPain_painscale_handler")
        current_intent = handler_input.request_envelope.request.intent

        test_statex(handler_input, "jointPain")
        # get the swell improvement from the slot and save it in session attributes
        cur_slot_name = "jointPainScale"
        next_slot = "jointPainMeds"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "jointPain"

        print(" DEBUG jointPainScale", cur_slot_value)


        # talking about swelling is improvong
        if cur_slot_value == None:
            # TBD prompt
            prompt = "On a scale from 1-10, how is your joint pain?"
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response

        # not improving
        elif cur_slot_value == "10" or cur_slot_value == "9" or cur_slot_value == "8" or cur_slot_value == "7" or cur_slot_value == "6":
            # go to icing.
            # TBD remove this and see if it will go to icing by default on delegate directive
            prompt = "Meds are good for swelling. Have you taken your meds?"
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value)
            # move to next state
            set_statex(handler_input,cur_intent_name, "jointPain_takingmeds")
            save_slots(handler_input,cur_intent_name)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot, updated_intent=current_intent)
              ).response
        # swelling is improving so we can stop
        elif cur_slot_value == "5" or cur_slot_value == "4" or cur_slot_value == "3" or cur_slot_value == "2" or cur_slot_value == "1":
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value)
            # move on to next slot but there is none this should take to completed
            if debug: test_statex(handler_input,cur_intent_name)
            # no further states , complete

            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            current_intent.dialog_state = DialogState.COMPLETED # ??)
            completed_resp = jointPain_do_complete(handler_input)
            return completed_resp
            """

            return handler_input.response_builder.add_directive(
                DelegateDirective(
                updated_intent=current_intent
            )).response
            """
        else:
            print("jointPain_painscale_handler not number %s"%cur_slot_value)
            prompt = "Sorry I am Not able to understand your response %s . Could you give a number for your pain on a scale one to ten "%cur_slot_value
            save_slots(handler_input,cur_intent_name)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
                    ElicitSlotDirective(slot_to_elicit=next_slot,
                    updated_intent = current_intent)
              ).response

class jointPain_paincondition_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("jointPain")(handler_input)  and
                  get_statex(handler_input,"jointPain") == "jointPain_paincondition" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response


        current_intent = handler_input.request_envelope.request.intent
        # get the swell improvement from the slot and save it in session attributes
        cur_slot_name = "jointPainCondition"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "jointPain"
        logger.info("In jointPain_paincondition_handler slotval : %s"%cur_slot_value)
        # we are talkign about the value of swelling

        if cur_slot_value not in ('good', 'bad'):
            logger.info("In jointPain_paincondition_handler not getting value reprompting ")
            prompt = "How is your joint pain?"
            save_slots(handler_input,cur_intent_name)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response
        # no swelling we are done
        elif cur_slot_value == 'good':
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, "good")
            # no further states
            print("COMPLETED DIALOG\n")
            #we have a bug this doesnt really work because state is not set to completed
            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            save_slots(handler_input,cur_intent_name)
            # changes state and moves on to next intent
            return jointPain_do_complete(handler_input)
            """ This thing messes up by getting delegation to extract one more piece of info
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response
            """
        elif cur_slot_value == 'bad':
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, "bad")
            # TBD proper noise on swelling
            set_statex(handler_input, cur_intent_name,'jointPain_painscale')
            save_slots(handler_input,cur_intent_name)

            prompt = "Oh that doesn't sound too good. On a scale from 1 to 10, how is your pain?"
            next_slot = 'jointPainScale'
            assert(next_slot in valid_slots)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot,
              updated_intent=current_intent)
              ).response


# waterfall makes sure if it is red, shade has to be filled otherwise wont get here
# General case of all colors
# TBD if We used Elicit, will state be completed



#waterfall makes sure red is filled shade must be filled. otherwise not needed
#we are not doing anything here maybe we could

'''

class InProgressjointPain_Intent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("jointPain")(handler_input)
                and handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # begin workaround why dialogState not being set to complete
        cur_state = get_statex(handler_input, "jointPain" )
        print("DEBUG CURRENT STATE INPROGRESS JOINT PAIN handler ",cur_state )

        if is_current_statex(handler_input, "jointPain", 'jointPain_complete'):
            print("DEBUG 292 COMPLETING")
            handler_input.request_envelope.request.dialog_state = DialogState.COMPLETED # try again
            completed_resp = jointPain_do_complete(handler_input)
            return completed_resp
        else:
            print("DEBUG 297 NOT COMPLETING")

        if handler_input.request_envelope.request.dialog_state == DialogState.STARTED:

            print(" InProgress jointPain_intent  RESTORE")

            #tbd do a better job of recovery
            restore_slots(handler_input, 'jointPain')
            if not (get_statex(handler_input, "jointPain")):
                set_statex(handler_input, "jointPain", "jointPain_paincondition")

        else:
            # this save is a bit aggressive after after every user responds
            print(" InProgress jointPain_intent SAVE ")
            save_slots(handler_input,'jointPain' ) # dialog not completed

        current_intent = handler_input.request_envelope.request.intent
        prompt = ""
        # go through each of the slots
        for statey in jointPain_state_to_slots:
            for slot_name in jointPain_state_to_slots[statey]:
                 #get_statex(handler_input, "swellsuture" ) == None:
                # dont know why we didnt have a state, Once state is filled a different logic may arise
                # take the first one that hasnt been filled
                current_slot = current_intent.slots[slot_name] #slot object
                if (current_slot.confirmation_status != SlotConfirmationStatus.CONFIRMED
                        and current_slot.resolutions
                        and current_slot.resolutions.resolutions_per_authority[0]):

                    print("DEBUG STATUS CODE SUCCESS ", slot_name, current_slot.resolutions.resolutions_per_authority[0].status.code)
                    # deal with equivalents, ask user to fill in one particular equivalent
                    if current_slot.resolutions.resolutions_per_authority[0].status.code == StatusCode.ER_SUCCESS_MATCH:
                        if len(current_slot.resolutions.resolutions_per_authority[0].values) > 1:
                           print("Setting state", statey,"  TO GET SLOT: ", slot_name)
                           set_statex(handler_input, "jointPain", statey)
                           prompt = "Could you clarify which of these you meant ?  "
                           values = " or ".join([e.value.name for e in current_slot.resolutions.resolutions_per_authority[0].values])
                           prompt += values + " ?"
                           save_slots(handler_input,'jointPain' )
                           return handler_input.response_builder.speak(
                                prompt).ask(prompt).add_directive(
                                       ElicitSlotDirective(
                                               updated_intent = current_intent,
                                               slot_to_elicit=current_slot.name) # may have been restored
                            ).response
                    # otherwise ask user for the slot itself
                    elif current_slot.resolutions.resolutions_per_authority[0].status.code == StatusCode.ER_SUCCESS_NO_MATCH:
                        if True : # current_slot.name in required_slots:
                            # dont understand this why we have to prompt if we are elicitung
                            print("elif Setting state", statey,"  TO GET SLOT: ", slot_name)
                            set_statex(handler_input, "jointPain", statey)

                            prompt = "Could we talk about {}?".format(current_slot.name)
                            save_slots(handler_input,'jointPain' )
                            return handler_input.response_builder.speak(
                                 prompt).ask(prompt).add_directive(
                                     ElicitSlotDirective(
                                         updated_intent = current_intent,
                                        slot_to_elicit=current_slot.name
                                    )).response
        #In case of no synonyms were reach here
        save_slots(handler_input,'jointPain' )
        print("DELEGATE END OF LOOP DEBUG")
        return handler_input.response_builder.add_directive(
            DelegateDirective(
                updated_intent=current_intent
            )).response
'''

def jointPain_do_complete(handler_input):
    logger.info(" COMPLETING jointPain_do_complete")
    test_statex(handler_input,"jointPain")

    set_statex(handler_input,"jointPain", "jointPain_complete")
    save_slots(handler_input, "jointPain") # dialog completed  why save
    filled_slots = handler_input.request_envelope.request.intent.slots
    slot_values = get_slot_values(filled_slots)
    try:
        # TBD move as a session variable and build in pieces
        speech = ("""Joint pain is {}.
                   """ .format(slot_values["jointPainCondition"]["resolved"]) )
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
