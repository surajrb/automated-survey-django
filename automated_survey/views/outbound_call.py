from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from twilio.rest import Client

@require_GET
def outbound_call():
    # Your Account Sid and Auth Token from twilio.com/user/account
    account_sid = "AC75f241336a53e2f30a6686e05fae208a"
    auth_token = "f89268cb35b36f3ec3d0c6af02707e6c"
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        #to="+919811101379",
        #to="+919211416649",
        #to="+919711598770",
        #to="+917506191561";


        from_="+16194323662",
        url="http://89d8fc06.ngrok.io/automated-survey/first-survey/"
    )

    print(call.sid)
