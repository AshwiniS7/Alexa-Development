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

# hope we didnt mess the spelling
daily_stats_slots = [
"patientname", 
"patientdob", 
"Appetite",
"Energy",
"smoking",
"drinking",
"spirometry"]

class dailystats_handler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("dailystats")(handler_input)  
        	      and get_statex(handler_input,"dailystats") == "collectstats"
                  and handler_input.request_envelope.request.dialog_state != DialogState.COMPLETED
                )
            
        return test
    def handle(self, handler_input):
        l = {}
        speech = "Please wait momentarily while we fix some technical issues."
        current_intent = handler_input.request_envelope.request.intent
        for slot_name in daily_stats_slots:
            valx = get_resolved_value(handler_input, slot_name)
            l [slot_name] = valx
            if valx == None :
                prompt = "Sorry I couldn't understand your response %s for %s "%(valx, slot_name)
                save_slots(handler_input)
                return handler_input.response_builder.speak(prompt).ask(prompt).add_directive(
                                       ElicitSlotDirective(
                                               updated_intent = current_intent,
                                               slot_to_elicit = slot_name))
        set_statex(handler_input, current_intent.name, "done_with_stats")
        save_slots(handler_input,current_intent.name)
        speech += recover_conversation(handler_input)
        handler_input.request_envelope.request.intent.dialog_state = DialogState.COMPLETED
        return handler_input.response_builder.speak(speech).response

class dailystats_Completedhandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        test = (is_intent_name("dailystats")(handler_input)  
                  and handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED)
        return test
    def handle(self, handler_input):
        current_intent = handler_input.request_envelope.request.intent
        print("daily stats COMPLETED HANDLER")
        set_statex(handler_input, current_intent.name, "done_with_stats")
        save_slots(handler_input,current_intent.name)
        speech = recover_conversation(handler_input)
        #speech += "debug !! DIALOG IS completed"
        return handler_input.response_builder.speak(speech).add_directive(
            ConfirmIntentDirective(
                updated_intent=current_intent
            )).response
        #return handler_input.response_builder.speak(speech).response

