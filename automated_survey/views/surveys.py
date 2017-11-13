from automated_survey.models import Survey, Question
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from automated_survey.views.questions import add_url_params

@require_GET
def show_survey_results(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    responses_to_render = [response.as_dict() for response in survey.responses]

    template_context = {
        'responses': responses_to_render,
        'survey_title': survey.title
    }

    return render_to_response('results.html', context=template_context)

@csrf_exempt
def show_survey(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    first_question = survey.first_question

    first_question_ids = {
        'survey_id': survey.id,
        'question_id': first_question.id
    }

    first_question_url = reverse('question', kwargs=first_question_ids)

    #welcome = 'Hi Alex, Welcome to the %s , You will be asked 3 questions, You will need to answer each question in max 10 seconds, Press # key when you have finished your answer' % survey.title
    c_name = request.GET.get("c_name")
    org_name = request.GET.get("org_name")

    if (c_name != None and c_name != 'None'):
        c_name=c_name
    else:
        c_name='candidate'

    if (org_name != None and org_name != 'None'):
        title=org_name
    else:
        title=survey.title

    welcome = 'Hi %s, Welcome to the %s , You will be asked 3 questions, You will need to answer each question in max 10 seconds, Press # key when you have finished your answer' % (c_name,title)

    if request.is_sms:
        twiml_response = MessagingResponse()
        twiml_response.message(welcome)
        twiml_response.redirect(first_question_url, method='GET')
    else:
        twiml_response = VoiceResponse()
        twiml_response.say(welcome)
        twiml_response.redirect(first_question_url, method='GET')

    return HttpResponse(twiml_response, content_type='application/xml')



@require_POST
def redirects_twilio_request_to_proper_endpoint(request):
    answering_question = request.session.get('answering_question_id')
    c_name = request.session.get("c_name")
    org_name = request.session.get("org_name")
    #c_name = request.POST.get("c_name")
    #org_name = request.POST.get("org_name")
    c_name = request.GET.get("c_name")
    org_name = request.GET.get("org_name")

    if not answering_question:
        first_survey = Survey.objects.first()
        redirect_url = reverse('survey',
                               kwargs={'survey_id': first_survey.id})
    else:
        question = Question.objects.get(id=answering_question)
        redirect_url = reverse('save_response',
                               kwargs={'survey_id': question.survey.id,
                                       'question_id': question.id})
    urlparams = {'c_name': c_name, 'org_name': org_name}
    redirect_url = add_url_params(redirect_url, urlparams)
    #print("redirect_url:" + redirect_url)
    return HttpResponseRedirect(redirect_url)


@require_GET
def redirect_to_first_results(request):
    first_survey = Survey.objects.first()
    results_for_first_survey = reverse(
        'survey_results', kwargs={
            'survey_id': first_survey.id})
    return HttpResponseRedirect(results_for_first_survey)
