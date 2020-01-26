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
#intent_name fev
 
class fever_temp_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("fever")(handler_input)  and 
                  is_current_statex(handler_input, "fever", "fever_collect_temp") and 
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In fever_temp_handler")
        current_intent = handler_input.request_envelope.request.intent

        test_statex(handler_input, "fever_temp") 
        # get the swell improvement from the slot and save it in session attributes 
        cur_slot_name = "fever_temperaturex"
        assert(cur_slot_name in valid_slots)
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = current_intent.name # TBD make this change everywhere 

        print(" DEBUG fever_temp_handler ", cur_slot_value)
        try:
            cur_slot_value  = float(cur_slot_value)
        except:
            cur_slot_value = None


        # talking about swelling is improvong 
        if cur_slot_value == None  :

            # TBD prompt 
            prompt = "What is your temperature? I have %s "%(cur_slot_value)
            reprompt = "What did your thermometer read"
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
            if debug: test_statex(handler_input,"fever") 
            # no further states , complete 
            #set_statex(handler_input,"fever", "fever_completedx")
            
            #save_slots(handler_input,'fever' )
            return do_fever_complete(handler_input)
            #return completed_resp
            

class fever_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("fever")(handler_input)  and 
                  is_current_statex(handler_input, "fever", "fever_beginx") and
                  handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)
        return test


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        print("DEBUG in fever_handler")
      
        current_intent = handler_input.request_envelope.request.intent
        # get the swell improvement from the slot and save it in session attributes 
        cur_slot_name = "fever_yesNo"
        try:
            assert(cur_slot_name in valid_slots)
        except:
            print("exception ",cur_slot_name,"not in ", valid_slots)
            raise("exception in slot name ")
        cur_slot_value = get_resolved_value_from_handler(handler_input,cur_slot_name)
        cur_intent_name = "fever"
        assert(cur_intent_name == current_intent.name) # TBD remove cur_intent_name = "fever"
        logger.info("fever_handler slotval : %s"%cur_slot_value)
        # we are talking about the value of swelling 
        
        if cur_slot_value == None :
            
            prompt = "Do you have a fever? "
            save_slots(handler_input,cur_intent_name )
            return handler_input.response_builder.speak(
              prompt).ask(prompt).add_directive(
              ElicitSlotDirective(slot_to_elicit=cur_slot_name, updated_intent=current_intent)
              ).response
        # no swelling we are done 
        elif cur_slot_value == 'no': 
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # no further states 
            print("COMPLETED DIALOG\n")
            #set_statex(handler_input, cur_intent_name, "fever_completedx")

            #we have a bug this doesnt really work because state is not set to completed 
            #handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            #save_slots(handler_input, cur_intent_name )
            # changes state and moves on to next intent 
            handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
            return do_fever_complete(handler_input)
           
        elif cur_slot_value == 'yes': 
            set_session_attr(handler_input, cur_intent_name, cur_slot_name, cur_slot_value) 
            # TBD proper noise on swelling
            next_state = 'fever_collect_temp'
            set_statex(handler_input, cur_intent_name, next_state)
            next_slot = fever_state_to_slots[next_state][0]
            save_slots(handler_input,cur_intent_name )

            prompt = " Tell me in Fahrenheit What is the temperature of the fever "
            repromptx = "How much fever do you have " 
            #removed the .ask(reprompt)
            return handler_input.response_builder.speak(
              prompt).ask(repromptx).add_directive(
              ElicitSlotDirective(slot_to_elicit='fever_temperaturex',updated_intent=current_intent)
              ).response
        else:
            print ("crashing and burning fever")
            if debug: raise

# waterfall makes sure of order

#TBD THIS INPROGRESS CAN BE MADE COMMON TO MANY INTENTS ? 

class InProgress_fever_Intent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        current_intent = handler_input.request_envelope.request.intent
        #print("DEBUG InProgress_fever_intent_can_handle", current_intent.name, 
        #            is_intent_name("fever")(handler_input), 
        #            handler_input.request_envelope.request.dialog_state )
        return (is_intent_name("fever")(handler_input)
                and handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # begin workaround why dialogState not being set to complete
        cur_state = get_statex(handler_input, "fever" )
        current_intent = handler_input.request_envelope.request.intent
        cur_intent_name = current_intent.name
        print("DEBUG CURRENT STATE   handler ",cur_state , cur_intent_name)

        if is_current_statex(handler_input, "fever", 'fever_completedx'):
            print("DEBUG fever 165  COMPLETING")
            handler_input.request_envelope.request.dialog_state = DialogState.COMPLETED # try again 
            completed_resp = do_fever_complete(handler_input)
            return completed_resp
        else:
            print("DEBUG2 InProgress_fever_Intent NOT COMPLETING")

        if handler_input.request_envelope.request.dialog_state == DialogState.STARTED:
        
            print(" DEEBUG InProgress fever  RESTORE")

            #tbd do a better job of recovery
            restore_slots(handler_input, cur_intent_name)
            if not (get_statex(handler_input, cur_intent_name)):
                set_statex(handler_input, cur_intent_name, "fever_beginx")
           
        #else:
            # this save is a bit aggressive after after every user responds
            
            #save_slots(handler_input,cur_intent_name) # dialog not completed 
        prompt = ""
        # go through each of the slots 
        for statey in fever_state_to_slots:
            for slot_name in fever_state_to_slots[statey]:
                # dont know why we didnt have a state, Once state is filled a different logic may arise 
                # take the first one that hasnt been filled
                current_slot = current_intent.slots[slot_name] #slot object
                if (current_slot.confirmation_status != SlotConfirmationStatus.CONFIRMED
                        and current_slot.resolutions
                        and current_slot.resolutions.resolutions_per_authority[0]):

                    print(" fever+status_code ", slot_name, current_slot.resolutions.resolutions_per_authority[0].status.code)
                    # deal with equivalents, ask user to fill in one particular equivalent
                    if current_slot.resolutions.resolutions_per_authority[0].status.code == StatusCode.ER_SUCCESS_MATCH:
                        if len(current_slot.resolutions.resolutions_per_authority[0].values) > 1:
                            print("Setting state", statey,"  TO GET SLOT: ", slot_name)
                            set_statex(handler_input, cur_intent_name ,statey) 
                            prompt = "Could you clarify which of these you meant ?  "
                            values = " or ".join([e.value.name for e in current_slot.resolutions.resolutions_per_authority[0].values])
                            prompt += values + " ?"
                            save_slots(handler_input,cur_intent_name )
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
                            set_statex(handler_input, cur_intent_name, statey) 

                            prompt = "Could we talk about Blood Pressure  ?"
                            save_slots(handler_input,cur_intent_name )
                            return handler_input.response_builder.speak(
                                 prompt).ask(prompt).add_directive(
                                     ElicitSlotDirective(
                                         updated_intent = current_intent,
                                        slot_to_elicit=current_slot.name
                                    )).response
        #In case of no synonyms were reach here 
        save_slots(handler_input,cur_intent_name )
        print("DEBUG delegate fever")
        return handler_input.response_builder.add_directive(
            DelegateDirective(
                updated_intent=current_intent
            )).response

def do_fever_complete(handler_input):
    logger.info(" DEBUG in do_fever _complete")

     # dialog completed  why save
    filled_slots = handler_input.request_envelope.request.intent.slots
    slot_values = get_slot_values(filled_slots)
    current_intent = handler_input.request_envelope.request.intent
    cur_intent_name = current_intent.name
    assert(cur_intent_name == 'fever')

    try:
        # TBD move as a session variable and build in pieces 
        set_statex(handler_input,cur_intent_name , "fever_completedx")
        save_slots(handler_input,cur_intent_name)
        print(" do_fever_complete %s"%slot_values)
        tempx = get_session_attr(handler_input,cur_intent_name,"fever_temperaturex" )
        havefever = get_session_attr(handler_input,cur_intent_name,"fever_yesNo" )
        speech = ("""We have collected information about your fever  which is {0} with a temperature of {1}. 
                   """ .format(havefever, tempx) )
        next_conv = recover_conversation(handler_input , init = False)
        speech += next_conv
        
        #current intent was null 
        # funny . if we set it here it crashes. If we set COMPLETED outside the function it doesnt crash
        # but the state never changes maybe because there is no current_intent=update ?  
        #handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
        
                    
    except Exception as e:
        # figure out how to change state set_statex(handler_input, "suture_red", "walk")
        speech = ("I am really sorry. I am unable to access part of my "
                      "memory. Please try again later.")
        logger.info("Intent: {}: message: {}".format(
              handler_input.request_envelope.request.intent.name, str(e)))

    """ TBD try this  seems better to update the intent 
    resp = handler_input.response_builder.speak(speech).add_directive(
            ConfirmIntentDirective(
                updated_intent=current_intent
            )).response
    """

    return handler_input.response_builder.speak(speech).add_directive(
            ConfirmIntentDirective(
                updated_intent=current_intent
            )).response
    
    # this doesnt work properly doesnt transition
    #return handler_input.response_builder.speak(speech).response

class Completedfever_Intent(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        # we cant test for statex because dialog can end in any statex 
        return (is_intent_name("fever")(handler_input)
            and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("DEBUG In Dialog Completed handler : fever")
        completed_resp = do_fever_complete(handler_input)
        intent_name = handler_input.request_envelope.request.intent
        #ebug = get_session_attr(handler_input, intent_name, 'fever_temperaturex')
        #logger.info("In Completed fever temperature : %s"%debug)
        return completed_resp
