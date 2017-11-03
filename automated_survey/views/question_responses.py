from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST

from automated_survey.models import QuestionResponse, Question


@require_POST
def save_response(request, survey_id, question_id):
    question = Question.objects.get(id=question_id)

    save_response_from_request(request, question)

    next_question = question.next()
    if not next_question:
        return goodbye(request)
    else:
        return next_question_redirect(next_question.id, survey_id)


def next_question_redirect(question_id, survey_id):
    parameters = {'survey_id': survey_id, 'question_id': question_id}
    question_url = reverse('question', kwargs=parameters)

    twiml_response = MessagingResponse()
    twiml_response.redirect(url=question_url, method='GET')
    return HttpResponse(twiml_response)


def goodbye(request):
    goodbye_messages = ['That was the last question',
                        'Thanks for answering all the questions, We will get back to you in next 2 days',
                        'Have a nice day']
    if request.is_sms:
        response = MessagingResponse()
        [response.message(message) for message in goodbye_messages]
    else:
        response = VoiceResponse()
        [response.say(message) for message in goodbye_messages]
        response.hangup()
    return HttpResponse(response)

def save_response_from_request(request, question):
    session_id = request.POST['MessageSid' if request.is_sms else 'CallSid']
    # request_body = _extract_request_body(request, question.kind)
    request_body = request.POST['SpeechResult']
    phone_number = request.POST['To']
    confidence = round(float(request.POST['Confidence'])*100,2)
    response = QuestionResponse.objects.filter(question_id=question.id,
                                               call_sid=session_id).first()
    from datetime import datetime
    calltime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score = round(float(getscore(question.body, question.expectedans, request_body))*100,2)
    if not response:
        QuestionResponse(call_sid=session_id,
                         phone_number=phone_number,
                         response=request_body,
                         question=question,
                         score=score,
                         confidence=confidence,
                         calltime=calltime).save()
    else:
        response.response = request_body
        response.save()

def _extract_request_body(request, question_kind):
    Question.validate_kind(question_kind)

    if request.is_sms:
        key = 'Body'
    elif question_kind in [Question.YES_NO, Question.NUMERIC]:
        key = 'Digits'
    elif 'TranscriptionText' in request.POST:
        key = 'TranscriptionText'
    else:
        key = 'RecordingUrl'

    return request.POST.get(key)

def getscore(question,expectedans,actualans):
    if expectedans and actualans:
        question = question.replace('\xa0', ' ')
        expectedans = expectedans.replace('\xa0', ' ')
        actualans = actualans.replace('\xa0', ' ')
        documents = (expectedans, actualans)
        questionwords = question.split()
        from sklearn.feature_extraction import text
        stop_words_new = text.ENGLISH_STOP_WORDS.union(questionwords)
        from sklearn.feature_extraction.text import TfidfVectorizer
        tfidf_vectorizer = TfidfVectorizer(stop_words=stop_words_new)
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        from sklearn.metrics.pairwise import cosine_similarity
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)
        val = [item[1] for item in cosine_sim]
        if question:
            documentsq = (question, actualans)
            tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrixq = tfidf_vectorizer.fit_transform(documentsq)
            cosine_simq = cosine_similarity(tfidf_matrixq[0:1], tfidf_matrixq)
            valq = [item[1] for item in cosine_simq]
            match_indexq = valq[0]
            if match_indexq > 0.95:
                match_index=0.05
            else:
                match_index=round(val[0], 2)
        else:
            match_index=0
    return match_index