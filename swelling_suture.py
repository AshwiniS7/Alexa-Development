# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""

intent
    swellsuture

handler
    swellsuture_swellimprove_ice_handler
    swellsuture_swellimprove_handler
    CompletedSwellSutureIntent

state The dialog can get completed in any state. So we have to have a completed sate
    "swellsuture_complete"
    "swellsuture_swellimprove_ice"
    "swellsuture_swellimprove
    "swellsuture_swell"  - swelling known or trying to get it to it
    swellsuture   -- nothing known
    swellcalf. -- th enext 


slot names
    swellsuture_swelling
    swellsuture_swelling_swellimproving
    swellsuture_swellimprove_ice

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

swellsuture_slotprompt = {"swellsuture_swelling":"Is there any swelling around your suture area?", 
                        "swellsuture_swelling_swellimproving":"Is the swelling around your suture area improving?",
                        "swellsuture_swellimprove_ice":"Are you applying ice to the swelling?"}

class swellsuture_improve_ice_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("swellsuture")(handler_input)  and 
                 is_current_statex(handler_input, intent_name='swellsuture', statexval='swellsuture_swellimprove_ice') and
                  #get_statex(handler_input,"swellsuture") == "" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test
    def handle(self, handler_input):
        #if improve ice are filled simply delegate to go get next slot, if completed it will go to complete
        # we should have all the slots here  

        #if ice is not filled, reprompt for ice 
        logger.info("In swellsuture_swellimprove_ice_handler")
        cur_slot_name = "swellsuture_swellimprove_ice"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "swellsuture"
        statex = get_statex(handler_input,"swellsuture")
        
        logger.info("In swellsuture_swellimprove_ice_handler State :   %s"%statex  )

        if not cur_slot_value:
            prompt = " Did you try icing ?"
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit= cur_slot_name, updated_intent=current_intent)
              ).response
        elif cur_slot_value in ( 'yes', 'no'):
            # we have a value save it
            set_session_attr(handler_input, "swellsuture_ice",  cur_slot_name, cur_slot_value )

            #TBD congrat APPLYING ICE IS COOLEST THING TO DO 
            # move on to next slot but there is none this should take to completed
            if debug : 
                print("expect dialog complete")
                test_statex(handler_input, "swellsuture") # should pass all slots filled

            # this setting state to co,plete is probably wring not clear

            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED #nothing more
            
            return swellsuture_do_complete(handler_input)
            """
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response"""
# handler get swellimproves , jumps out, or proceeds 
class swellsuture_swellimprove_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("swellsuture")(handler_input)  and 
                  get_statex(handler_input, "swellsuture") == "swellsuture_swellimprove" and 
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In swellsuture_swellimprove_handler")
        current_intent = handler_input.request_envelope.request.intent

        test_statex(handler_input, "swellsuture") 
        # get the swell improvement from the slot and save it in session attributes 
        cur_slot_name = "swellsuture_swelling_swellimproving"
        next_slot = "swellsuture_swellimprove_ice"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "swellsuture"

        print(" DEBUG swellsuture_swellimprove", cur_slot_value)


        # talking about swelling is improvong 
        if cur_slot_value == None:
            # TBD prompt 
            prompt = "Is your swelling improving? "
            
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response

        # not improving 
        elif cur_slot_value == 'no': 
            # go to icing. 
            # TBD remove this and see if it will go to icing by default on delegate directive
            prompt = "Icing is good for swelling. Did you ice your swelling? "
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # move to next state 
            set_statex(handler_input,"swellsuture", "swellsuture_swellimprove_ice")
            save_slots(handler_input,'swellsuture' )
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot, updated_intent=current_intent)
              ).response
        # swelling is improving so we can stop
        elif cur_slot_value == 'yes' :
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # move on to next slot but there is none this should take to completed
            if debug: test_statex(handler_input,"swellsuture") 
            # no further states , complete 

            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            current_intent.dialog_state = DialogState.COMPLETED # ??)
            #completed_resp = swellsuture_do_complete(handler_input)
            return swellsuture_do_complete(handler_input)
            """

            return handler_input.response_builder.add_directive(
                DelegateDirective(
                updated_intent=current_intent
            )).response
            """
        else:
            print("swellsuture_swellimprove_handler  neither yes nor no %s"%cur_slot_value) 
            prompt = "Did you apply ice to your swelling ?"
            save_slots(handler_input,'swellsuture' )
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
                    ElicitSlotDirective(slot_to_elicit='suture_ice',
                    updated_intent = current_intent)
              ).response

class swellsuture_swell_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("swellsuture")(handler_input)  and 
                  get_statex(handler_input,"swellsuture") == "swellsuture_swell" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        #print("DEBUG swellsuture_swell_handler can_handle" , is_intent_name("swellsuture")(handler_input),get_statex(handler_input,"swellsuture") , handler_input.request_envelope.request.dialog_state , "returning", test)
        return test


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
      
        current_intent = handler_input.request_envelope.request.intent
        # get the swell improvement from the slot and save it in session attributes 
        cur_slot_name = "swellsuture_swelling"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "swellsuture"
        logger.info(" DEBUG In swellsuture_swell_handler slotval : %s"%cur_slot_value)
        # we are talkign about the value of swelling 
        
        if cur_slot_value != "yes" and cur_slot_value != "no":
            logger.info("DEBUG In swellsuture_swell_handler not getting value reprompting ")
            prompt = "Do you have swelling around the suture? "
            save_slots(handler_input,'swellsuture' )
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit='swellsuture_swelling', updated_intent=current_intent)
              ).response
        # no swelling we are done 
        elif cur_slot_value == 'no': 
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # no further states 
            print("COMPLETED DIALOG\n")
            #we have a bug this doesnt really work because state is not set to completed 
            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            save_slots(handler_input,'swellsuture' )
            # changes state and moves on to next intent 
            return swellsuture_do_complete(handler_input)
            """ This thing messes up by getting delegation to extract one more piece of info 
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response
            """
        elif cur_slot_value == 'yes': 
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # TBD proper noise on swelling
            set_statex(handler_input, "swellsuture",'swellsuture_swellimprove')
            save_slots(handler_input,'swellsuture' )

            prompt = " A little swelling is expected. Is it improving"
            next_slot = 'swellsuture_swelling_swellimproving'
            assert(next_slot in valid_slots)
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot,
              updated_intent=current_intent)
              ).response
        else:
            print ("crash and burn swellsuture_swell_handler")
            if debug: raise

# waterfall makes sure if it is red, shade has to be filled otherwise wont get here 
# General case of all colors
# TBD if We used Elicit, will state be completed



#waterfall makes sure red is filled shade must be filled. otherwise not needed
#we are not doing anything here maybe we could


class InProgressswellsuture_Intent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("swellsuture")(handler_input)
                and handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # begin workaround why dialogState not being set to complete
        cur_state = get_statex(handler_input, "swellsuture" )
        print("DEBUG CURRENT STATE INPROGRESSSUTURE handler ",cur_state )

        if is_current_statex(handler_input, "swellsuture", 'swellsuture_completed'):
            print("DEBUG 292 COMPLETING")
            handler_input.request_envelope.request.dialog_state = DialogState.COMPLETED # try again 
            completed_resp = swellsuture_do_complete(handler_input)
            return completed_resp
        else:
            print("DEBUG 297 NOT COMPLETING")

        if handler_input.request_envelope.request.dialog_state == DialogState.STARTED:
        
            print(" debug InProgress suture_intent  RESTORE")

            #tbd do a better job of recovery
            restore_slots(handler_input, 'swellsuture')
            if not (get_statex(handler_input, "swellsuture")):
                set_statex(handler_input, "swellsuture", "swellsuture_swell")
           
        else:
            # this save is a bit aggressive after after every user responds
            print(" debug InProgress suture_intent SAVE ")
            save_slots(handler_input,'swellsuture' ) # dialog not completed 

        current_intent = handler_input.request_envelope.request.intent
        prompt = "..."
        # go through each of the slots 
        for statey in swellsuture_state_to_slots:
            for slot_name in swellsuture_state_to_slots[statey]:
                 #get_statex(handler_input, "swellsuture" ) == None:
                # dont know why we didnt have a state, Once state is filled a different logic may arise 
                # take the first one that hasnt been filled
                current_slot = current_intent.slots[slot_name] #slot object
                if (current_slot.confirmation_status != SlotConfirmationStatus.CONFIRMED
                        and current_slot.resolutions
                        and current_slot.resolutions.resolutions_per_authority[0]):

                    print("DEBUG STATUS CODE SUCCESS ", slot_name, 
                        current_slot.resolutions.resolutions_per_authority[0].status.code, "num resolutions",
                        len(current_slot.resolutions.resolutions_per_authority[0].values))
                    # deal with equivalents, ask user to fill in one particular equivalent
                    if current_slot.resolutions.resolutions_per_authority[0].status.code == StatusCode.ER_SUCCESS_MATCH:
                        if True or len(current_slot.resolutions.resolutions_per_authority[0].values) > 1:
                           print("DEBUG Setting state", statey,"  TO GET SLOT: ", slot_name)
                           set_statex(handler_input, "swellsuture", statey) 
                           prompt = "Could you clarify which of these you meant?  "
                           values = " or ".join([e.value.name for e in current_slot.resolutions.resolutions_per_authority[0].values])
                           prompt += values + " ?"
                           save_slots(handler_input,'swellsuture' )
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
                            print("debug elif Setting state", statey,"  TO GET SLOT: ", slot_name)
                            set_statex(handler_input, "swellsuture", statey) 

                            #prompt = "Could we talk about {} around suture?".format(current_slot.name)
                            prompt = swellsuture_slotprompt[current_slot.name]
                            save_slots(handler_input,'swellsuture' )
                            return handler_input.response_builder.speak(
                                 prompt).ask(prompt).add_directive(
                                     ElicitSlotDirective(
                                         updated_intent = current_intent,
                                        slot_to_elicit=current_slot.name
                                    )).response
                    else:
                        logger.info("DEBUG", )
        #In case of no synonyms were reach here 
        save_slots(handler_input,'swellsuture' )
        print("DELEGATE END OF LOOP DEBUG")
        return handler_input.response_builder.add_directive(
            DelegateDirective(
                updated_intent=current_intent
            )).response

def swellsuture_do_complete(handler_input):
    current_intent = handler_input.request_envelope.request.intent
    logger.info(" DEBUG in swellsuture_do_complete")
    test_statex(handler_input,"swellsuture")

    set_statex(handler_input,"swellsuture", "swellsuture_complete")
    save_slots(handler_input,"swellsuture") # dialog completed  why save
    filled_slots = handler_input.request_envelope.request.intent.slots
    slot_values = get_slot_values(filled_slots)
    try:
        # TBD move as a session variable and build in pieces 
        speech = ("""Swelling around suture is {}. 
                   """ .format(slot_values["swellsuture_swelling"]["resolved"]) )
        next_conv = recover_conversation(handler_input , init = False)
        speech += next_conv
        handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
        # TBD smart way to set something set_statex(handler_input, "swell", "swellcalf")
                    
    except Exception as e:
        speech = ("I am really sorry. I am unable to access part of my "
                      "memory. Please try again later")
        logger.info("Intent: {}: message: {}".format(
              handler_input.request_envelope.request.intent.name, str(e)))

    """ TBD try this 
    resp = handler_input.response_builder.speak(speech).add_directive(
            ConfirmIntentDirective(
                updated_intent=current_intent
            )).response
    """

    return handler_input.response_builder.speak(speech).add_directive(ConfirmIntentDirective(updated_intent=current_intent)).response

    #return handler_input.response_builder.speak(speech).response

class CompletedSwellSutureIntent(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        # we cant test for statex because dialog can end in any statex 
        return (is_intent_name("swellsuture")(handler_input)
            and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("DEBUG In dialog Completed swellsuture")
        completed_resp = swellsuture_do_complete(handler_input)
        return completed_resp


#
