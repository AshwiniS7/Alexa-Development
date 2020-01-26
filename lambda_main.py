
 # -*- coding: utf-8 -*-
from __future__ import print_function
import logging
import json
import requests
import six
import random

from ask_sdk_core.skill_builder import SkillBuilder
#from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.serialize import DefaultSerializer
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
from jointpain import *
from swelling_suture import *
from redness_suture import *
from fever import *
from dailystats import *
from bloodpressure import *
from joint_exercises import *
import traceback
from aws_ses_email import * 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

'''questions = ["How is your joint pain?", "On a scale from 1-10, how is your joint pain?",
    "Have you been taking your pain medications?", "Is there any swelling around your suture area?",
    "Has the swelling been improving?", "Are you applying ice?"]

slotnames = ["jointPainCondition", "jointPainScale", "jointPainMeds"]'''

# Request Handler classes
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for skill launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In LaunchRequestHandler")
        
        attr = handler_input.attributes_manager.session_attributes
        attr["launch"] = "completed"
        send_it()

        init_beginstates(handler_input)

        speech = recover_conversation(handler_input, init = True)
        reprompt = speech
        # end changes
        # Set the default state
        #cant save slots since we dont have intent here
        handler_input.response_builder.speak(speech).ask(reprompt)
        return handler_input.response_builder.response



class GetConversationBackIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        logger.info(" last GET CONVERSATION BACK INTENT ")
        return True

    def handle(self, handler_input):
        logger.info("In CompletedConversationIntent")
        speech = "sorry, I got distracted and forgot what we were talking about. "
        try:
            current_intent = handler_input.request_envelope.request.intent
            intent_name = handler_input.request_envelope.request.intent.name
            if intent_name :
                statex = get_statex(handler_input, intent_name)
                if statex in valid_completedstates:
                    utterance = intent_to_utterance.get(intent_name, intent_name)
                    speech += " Did we already talk about %s"%(utterance)
                logger.info("GetConversationBackIntent %s %s "%(intent_name, statex))
            else:
                logger.info("no intent identified None")
        except:
            logger.info("GetConversationBackIntent  ERROR ")
            traceback.print_exc()
        
        speech +=  recover_conversation(handler_input)
        return handler_input.response_builder.speak(speech).add_directive(
            ConfirmIntentDirective(
                updated_intent=current_intent
            )).response

        #return handler_input.response_builder.speak(speech).response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for handling fallback intent.

     2018-May-01: AMAZON.FallackIntent is only currently available in
     en-US locale. This handler will not be triggered except in that
     locale, so it can be safely deployed for any locale."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = recover_conversation(handler_input)
        
        reprompt = speech
        handler_input.response_builder.speak(speech).ask(reprompt)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for help intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")
        speech = "I am nurse Nightingale I assist your doctor in collecting information."
        speech += recover_conversation(handler_input, init = False)
        reprompt = speech

        handler_input.response_builder.speak(speech).ask(reprompt).set_should_end_session(
            False)
        return handler_input.response_builder.response


class ExitIntentHandler(AbstractRequestHandler):
    """Single Handler for Cancel, Stop and Pause intents."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In ExitIntentHandler")
        handler_input.response_builder.speak("Bye").set_should_end_session(
            True)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for skill session end."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")
        logger.info("Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response

# Exception Handler classes
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch All Exception handler.

    This handler catches all kinds of exceptions and prints
    the stack trace on AWS Cloudwatch with the request envelope."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "Internal EXCEPTION %s"%(exception)
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


# Request and Response Loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.info("Request Envelope: {}".format(
            handler_input.request_envelope))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.info("Response: {}".format(response))



# Skill Builder object

sb = SkillBuilder()
# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())

sb.add_request_handler(jointPain_takingmeds_handler())
sb.add_request_handler(jointPain_painscale_handler())
sb.add_request_handler(jointPain_paincondition_handler())
#---- swellsuture
sb.add_request_handler( swellsuture_improve_ice_handler() )
sb.add_request_handler( swellsuture_swellimprove_handler() )
sb.add_request_handler( swellsuture_swell_handler() )
sb.add_request_handler( InProgressswellsuture_Intent() )
sb.add_request_handler( CompletedSwellSutureIntent() )
#sb.add_request_handler( swellsuture__FallbackIntentHandler() )
#sb.add_request_handler( swellsuture__HelpIntentHandler() )

#----swellsuture


#--redness
sb.add_request_handler( redsuture_improve_pus())
sb.add_request_handler( redsuture_improve_handler())
sb.add_request_handler( redsuture_handler())
sb.add_request_handler( InProgressredsuture_Intent())
sb.add_request_handler( CompletedredsutureIntent())
#--redness

#-----fever
sb.add_request_handler(fever_temp_handler())
sb.add_request_handler(fever_handler())
sb.add_request_handler(InProgress_fever_Intent())
sb.add_request_handler(Completedfever_Intent())

#---fever
# sb.add_request_handler(GetConversationBackIntent())

#-- daily stats
sb.add_request_handler(dailystats_handler())
sb.add_request_handler(dailystats_Completedhandler())


sb.add_request_handler(bloodpressure_diastolic_handler())
sb.add_request_handler(bloodpressure_systolic_handler())
sb.add_request_handler(bloodpressure_checked_handler())

sb.add_request_handler(jointexercises_doing_handler())
# Add exception handler to the skill.
sb.add_request_handler(HelpIntentHandler())
# LAST CHANCE TO RECOVER
sb.add_request_handler(GetConversationBackIntent())


sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(ExitIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())


# Add response interceptor to the skill.
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())


# Expose the lambda handler to register in AWS Lambda.
lambda_handler = sb.lambda_handler()
