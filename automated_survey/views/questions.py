from django.core.urlresolvers import reverse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from django.http import HttpResponse

from automated_survey.models import Question
from django.views.decorators.http import require_POST, require_GET

@require_GET
def show_question(request, survey_id, question_id):
    question = Question.objects.get(id=question_id)
    if request.is_sms:
        twiml = sms_question(question)
    else:
        twiml = voice_question(question)

    request.session['answering_question_id'] = question.id
    return HttpResponse(twiml, content_type='application/xml')


def sms_question(question):
    twiml_response = MessagingResponse()

    twiml_response.message(question.body)
    twiml_response.message(SMS_INSTRUCTIONS[question.kind])

    return twiml_response

SMS_INSTRUCTIONS = {
    Question.TEXT: 'Please type your answer',
    Question.YES_NO: 'Please type 1 for yes and 0 for no',
    Question.NUMERIC: 'Please type a number between 1 and 10'
}

def voice_question(question):
    twiml_response = VoiceResponse()
    twiml_response.say(question.body)
    twiml_response.say("Please wait for the next question after answering")
    # twiml_response.say(VOICE_INSTRUCTIONS[question.kind])
    action = save_response_url(question)
    if question.kind == Question.TEXT:
        # twiml_response.record(
        #     action=action,
        #     method='POST',
        #     max_length=6,
        #     transcribe=True,
        #     transcribe_callback=action
        # )
        twiml_response.gather(
            action=action,
            method='POST',
            input='dtmf speech',
            language='en-IN',
            hints='Working,capital,amount,companys,current,assets,minus,liabilities, \
Bank,Reconciliation,Statement,prepared,reconcile,balances,cashbook,maintained,concern,periodical,intervals, \
Depreciation,permanent,gradual,continuous,reduction,book,value,fixed',
            timeout=10,
            # partialResultCallback='https://requestb.in/yyekuoyy'
        )
    else:
        twiml_response.gather(action=action, method='POST')
    return twiml_response

VOICE_INSTRUCTIONS = {
    Question.TEXT: 'Please record your answer after the beep and then hit the pound sign',
    Question.YES_NO: 'Please press the one key for yes and the zero key for no and then hit the pound sign',
    Question.NUMERIC: 'Please press a number between 1 and 10 and then hit the pound sign'
}


def save_response_url(question):
    return reverse('save_response',
                   kwargs={'survey_id': question.survey.id,
                           'question_id': question.id})


@require_GET
def outbound_call(request):
    from twilio.rest import Client
    # Your Account Sid and Auth Token from twilio.com/user/account
    account_sid = "AC75f241336a53e2f30a6686e05fae208a"
    auth_token = "f89268cb35b36f3ec3d0c6af02707e6c"
    client = Client(account_sid, auth_token)
    c_name = request.GET.get("c_name")
    org_name = request.GET.get("org_name")

    #request.session['c_name'] = c_name
    #request.session['org_name'] = org_name
    urlparams = {'c_name': c_name, 'org_name': org_name}
    urlwithparam = add_url_params("http://" + request.get_host() + "/automated-survey/first-survey/", urlparams)
    print("urlwithparam:" + urlwithparam)
    call = client.calls.create(
         to=request.GET.get("to"),
         #from_=request.GET.get("from"),
         from_="+16194323662",
         url=urlwithparam
     )
    # print(call.sid)
    return HttpResponse("Call initiated : call sid(" + call.sid + ") for number:" + request.GET.get("to") )


def add_url_params(url, params):
    from json import dumps

    try:
        from urllib import urlencode, unquote
        from urlparse import urlparse, parse_qsl, ParseResult
    except ImportError:
        # Python 3 fallback
        from urllib.parse import (
            urlencode, unquote, urlparse, parse_qsl, ParseResult
        )
    """ Add GET params to provided URL being aware of existing.

    :param url: string of target URL
    :param params: dict containing requested params to be added
    :return: string with updated URL

    >> url = 'http://stackoverflow.com/test?answers=true'
    >> new_params = {'answers': False, 'data': ['some','values']}
    >> add_url_params(url, new_params)
    'http://stackoverflow.com/test?data=some&data=values&answers=false'
    """
    # Unquoting URL first so we don't loose existing args
    url = unquote(url)
    # Extracting url info
    parsed_url = urlparse(url)
    # Extracting URL arguments from parsed URL
    get_args = parsed_url.query
    # Converting URL arguments to dict
    parsed_get_args = dict(parse_qsl(get_args))
    # Merging URL arguments dict with new params
    parsed_get_args.update(params)

    # Bool and Dict values should be converted to json-friendly values
    # you may throw this part away if you don't like it :)
    parsed_get_args.update(
        {k: dumps(v) for k, v in parsed_get_args.items()
         if isinstance(v, (bool, dict))}
    )

    # Converting URL argument to proper query string
    encoded_get_args = urlencode(parsed_get_args, doseq=True)
    # Creating new parsed result object based on provided with new
    # URL arguments. Same thing happens inside of urlparse.
    new_url = ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, encoded_get_args, parsed_url.fragment
    ).geturl()

    return new_url