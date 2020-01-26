

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


# Particular to general 
# suture +swellswellimprove_ice basically completes the conversation 
# suture + ice  
# everything  


#last handler only ice 
class redsuture_improve_pus(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("redsuture")(handler_input)  and 
                  get_statex(handler_input,"redsuture") == "redsuture_improve_pusx" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test
    def handle(self, handler_input):
        
        #if pus is not filled, reprompt for pus
        logger.info("In redsuture_pus_handler")
        cur_slot_name = "redsuture_improve_pus"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "redsuture"
        statex = get_statex(handler_input,"redsuture")
        
        logger.info("In redsuture_improve_pus State :   %s"%statex  )

        if not cur_slot_value:
            prompt = " Is there any pus or suture opening?"
            #TBD get the prompt from outside this file
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit= cur_slot_name, updated_intent=current_intent)
              ).response
        elif cur_slot_value in ( 'yes', 'no'):
            # we have a value save it
            set_session_attr(handler_input, cur_intent_name,  cur_slot_name, cur_slot_value )

            #TBD congrat APPLYING ICE IS COOLEST THING TO DO 
            # move on to next slot but there is none this should take to completed
            if debug : 
                print("expect dialog complete")

            set_statex(handler_input, cur_intent_name, "redsuture_completedx")
            
            save_slots(handler_input, cur_intent_name)
            return redsuture_do_complete(handler_input)
            """
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response"""
# handler get swellimproves , jumps out, or proceeds 
class redsuture_improve_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("redsuture")(handler_input)  and 
                  get_statex(handler_input, "redsuture") == "redsuture_improvex" and 
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In redsuture_improvex_handler")
        current_intent = handler_input.request_envelope.request.intent

        test_statex(handler_input, "redsuture") 
        # get the swell improvement from the slot and save it in session attributes 
        cur_slot_name = "redsuture_improve"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "redsuture"

        print(" DEBUG redsuture_swellimprove", cur_slot_value)


        # talking about swelling is improvong 
        if cur_slot_value == None:
            # TBD prompt 
            prompt = "Has the redness around your swelling been improving? "
            
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response

        # not improving 
        elif cur_slot_value == 'no': 
            # go to icing. 
            # TBD remove this and see if it will go to icing by default on delegate directive
            prompt = "I am very sorry to hear that. Is there pus or suture opening? "
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # move to next state 
            
            next_state = "redsuture_improve_pusx"
            next_slot = redsuture_state_to_slots[next_state][0]

            set_statex(handler_input,"redsuture",next_state )
            save_slots(handler_input,'redsuture' )
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot, updated_intent=current_intent)
              ).response
        # swelling is improving so we can stop
        elif cur_slot_value == 'yes' :
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # move on to next slot but there is none this should take to completed
            if debug: test_statex(handler_input,"redsuture") 
            # no further states , complete 
            set_statex(handler_input,"redsuture", "redsuture_completedx")
            
            save_slots(handler_input,'redsuture' )
            completed_resp = redsuture_do_complete(handler_input)
            return completed_resp
            """

            return handler_input.response_builder.add_directive(
                DelegateDirective(
                updated_intent=current_intent
            )).response
            """
        else:
            print("redsuture_swellimprove_handler  neither yes nor no %s"%cur_slot_value) 
            prompt = " did you ice after swelling ?"
            save_slots(handler_input,'redsuture' )
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
                    ElicitSlotDirective(slot_to_elicit='suture_ice',
                    updated_intent = current_intent)
              ).response

class redsuture_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("redsuture")(handler_input)  and 
                  get_statex(handler_input,"redsuture") == "redsuture_beginx" and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
      
        current_intent = handler_input.request_envelope.request.intent
        # get the swell improvement from the slot and save it in session attributes 
        cur_slot_name = "redsuture_yesNo"
        try:
            assert(cur_slot_name in valid_slots)
        except:
            print("exception ",cur_slot_name,"not in ", valid_slots)
            raise("exception in slot name ")
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "redsuture"
        logger.info("In redsuture_swell_handler slotval : %s"%cur_slot_value)
        # we are talking about the value of swelling 
        
        if cur_slot_value == None :
            
            prompt = "do you have redness around suture ? "
            save_slots(handler_input,'redsuture' )
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response
        # no swelling we are done 
        elif cur_slot_value == 'no': 
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # no further states 
            print("COMPLETED DIALOG\n")
            set_statex(handler_input,"redsuture", "redsuture_completedx")

            #we have a bug this doesnt really work because state is not set to completed 
            #handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            save_slots(handler_input,'redsuture' )
            # changes state and moves on to next intent 
            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            return redsuture_do_complete(handler_input)
            """ This thing messes up by getting delegation to extract one more piece of info 
            return handler_input.response_builder.add_directive(
                DelegateDirective(
                 updated_intent=current_intent
            )).response
            """
        elif cur_slot_value == 'yes': 
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # TBD proper noise on swelling
            next_state = 'redsuture_improvex'
            set_statex(handler_input, "redsuture", next_state)
            next_slot = redsuture_state_to_slots[next_state][0]
            save_slots(handler_input,'redsuture' )

            prompt = " A little redness is expected. Is it improving"
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=next_slot,
              updated_intent=current_intent),
              ).response
        else:
            print ("crashing and burning redsuture_swell_handler")
            if debug: raise

# waterfall makes sure of order

class InProgressredsuture_Intent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        #current_intent = handler_input.request_envelope.request.intent
        #print("DEBUG", current_intent.name, 
        #             is_intent_name("redsuture")(handler_input), 
        #            handler_input.request_envelope.request.dialog_state )
        return (is_intent_name("redsuture")(handler_input)
                and handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # begin workaround why dialogState not being set to complete
        cur_state = get_statex(handler_input, "redsuture" )
        print("DEBUG CURRENT STATE   handler ",cur_state )

        if is_current_statex(handler_input, "redsuture", 'redsuture_complete'):
            print("DEBUG 292 COMPLETING")
            handler_input.request_envelope.request.dialog_state = DialogState.COMPLETED # try again 
            completed_resp = redsuture_do_complete(handler_input)
            return completed_resp
        else:
            print("DEBUG suture red  NOT COMPLETING")

        if handler_input.request_envelope.request.dialog_state == DialogState.STARTED:
        
            print(" InProgress redsuture_intent  RESTORE")

            #tbd do a better job of recovery
            restore_slots(handler_input, 'redsuture')
            if not (get_statex(handler_input, "redsuture")):
                set_statex(handler_input, "redsuture", "redsuture_beginx")
           
        else:
            # this save is a bit aggressive after after every user responds
            print(" InProgress redsuture intent SAVE")
            #save_slots(handler_input,'redsuture' ) # dialog not completed 

        current_intent = handler_input.request_envelope.request.intent
        prompt = ""
        # go through each of the slots 
        for statey in redsuture_state_to_slots:
            for slot_name in redsuture_state_to_slots[statey]:
                 #get_statex(handler_input, "redsuture" ) == None:
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
                           set_statex(handler_input, "redsuture", statey) 
                           prompt = "Could you clarify which of these you meant ?  "
                           values = " or ".join([e.value.name for e in current_slot.resolutions.resolutions_per_authority[0].values])
                           prompt += values + " ?"
                           save_slots(handler_input,'redsuture' )
                           return handler_input.response_builder.speak(
                                prompt).ask(prompt).add_directive(
                                       ElicitSlotDirective(
                                               updated_intent = current_intent,
                                               slot_to_elicit=current_slot.name) # may have been restored
                            ).response
                    # otherwise ask user for the slot itself
                    elif current_slot.resolutions.resolutions_per_authority[0].status.code == StatusCode.ER_SUCCESS_NO_MATCH:
                        if current_slot.name in required_slots:
                               # dont understand this why we have to prompt if we are elicitung 
                            print("elif Setting state", statey,"  TO GET SLOT: ", slot_name)
                            set_statex(handler_input, "redsuture", statey) 

                            prompt = "Could we talk about {} around suture ?".format(current_slot.name)
                            save_slots(handler_input,'redsuture' )
                            return handler_input.response_builder.speak(
                                 prompt).ask(prompt).add_directive(
                                     ElicitSlotDirective(
                                         updated_intent = current_intent,
                                        slot_to_elicit=current_slot.name
                                    )).response
        #In case of no synonyms were reach here 
        save_slots(handler_input,'redsuture' )
        print("DELEGATE END OF LOOP DEBUG")
        return handler_input.response_builder.add_directive(
            DelegateDirective(
                updated_intent=current_intent
            )).response

def redsuture_do_complete(handler_input):
    logger.info(" COMPLETING redsuture_do_complete")
    test_statex(handler_input,"redsuture")
    save_slots(handler_input,"redsuture") # dialog completed  why save
    filled_slots = handler_input.request_envelope.request.intent.slots
    slot_values = get_slot_values(filled_slots)
    current_intent = handler_input.request_envelope.request.intent

    try:
        # TBD move as a session variable and build in pieces 
        speech = ("""We have collected information about your swelling as a {}.  
                   """ .format(slot_values["redsuture_yesNo"]["resolved"]) )
        next_conv = recover_conversation(handler_input , init = False)
        speech += next_conv
        print("DEBUG 339")
        #print("changing" , current_intent.dialog_state , "to",DialogState.COMPLETED , "of", DialogState )

        # funny . if we set it here it crashes sometimes . If we set COMPLETED outside the function it doesnt crash
        # but the state never changes maybe because there is no current_intent=update ?  
        handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED

        print(" DEBUG REDNESS IS COMPLETE ")
                    
    except Exception as e:
        print("DEBUG",e)
        # figure out how to change state set_statex(handler_input, "redsuture", "walk")
        speech = ("I am really sorry. I am unable to access part of my "
                      "memory. Please try again later")
        logger.info("Intent: {}: message: {}".format(
              handler_input.request_envelope.request.intent.name, str(e)))

    return handler_input.response_builder.speak(speech).add_directive(
            ConfirmIntentDirective(
                updated_intent=current_intent
            )).response

class CompletedredsutureIntent(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        # we cant test for statex because dialog can end in any statex 
        return (is_intent_name("redsuture")(handler_input)
            and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In Completed redsuture")
        completed_resp = redsuture_do_complete(handler_input)
        return completed_resp
