import json
import time

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

from ..models import AdoptionApplication


@login_required
def initKhalti(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")

    try:
        application_id = request.POST.get('application_id') or request.POST.get('booking_id')
        application = AdoptionApplication.objects.get(id=application_id, user=request.user)

        order_id = f"ORDER-{application.id}-{int(time.time())}"
        amount = int(application.total_amount * 100)

        payload = {
            "return_url": settings.KHALTI_RETURN_URL,
            "website_url": settings.KHALTI_WEBSITE_URL,
            "amount": amount,
            "purchase_order_id": order_id,
            "purchase_order_name": f"Pet Adoption - {application.pet.name}",
            "customer_info": {
                "name": application.adopter.full_name,
                "email": application.adopter.email,
                "phone": application.adopter.phone,
            },
        }

        headers = {
            'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        url = f"{settings.KHALTI_API_BASE}epayment/initiate/"

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()

        if response.status_code == 200:
            request.session['payment_order_id'] = order_id
            request.session['application_id'] = application_id
            payment_url = response_data.get('payment_url')

            if payment_url:
                return HttpResponseRedirect(payment_url)
            return JsonResponse({
                'success': False,
                'message': 'Payment URL not found in response',
            })
        error_msg = response_data.get('detail', 'Payment initialization failed')
        return JsonResponse({
            'success': False,
            'message': error_msg,
            'debug_info': response_data,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def verifyKhalti(request):
    if request.method == 'GET':
        url = f"{settings.KHALTI_API_BASE}epayment/lookup/"
        headers = {
            'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        pidx = request.GET.get('pidx')
        if not pidx:
            return redirect('index')

        data = json.dumps({'pidx': pidx})
        response = requests.post(url, headers=headers, data=data)
        new_res = response.json()

        if new_res.get('status') == 'Completed':
            application_id = request.session.get('application_id')
            if not application_id:
                purchase_order_id = request.GET.get('purchase_order_id', '')
                parts = purchase_order_id.split('-', 2)
                if len(parts) >= 2 and parts[0] == 'ORDER':
                    application_id = parts[1]
            if application_id:
                application = get_object_or_404(AdoptionApplication, id=application_id)
                if application.status == 'verified':
                    application.status = 'paid'
                    application.pet.is_available = False
                    application.pet.save()
                    application.save()
                    if hasattr(application.user, 'loyalty_points'):
                        application.user.loyalty_points.add_points(50)
                messages.success(request, 'Payment successful!')
                return redirect('my_applications')
            return redirect('my_applications')
        return redirect('my_applications')

    return redirect('my_applications')


@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        token = data.get("token")
        amount = data.get("amount")

        headers = {
            "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
        }
        payload = {
            "token": token,
            "amount": amount,
        }

        response = requests.post(
            f"{settings.KHALTI_API_BASE}payment/verify/",
            data=payload,
            headers=headers,
        )
        response_data = response.json()

        if response.status_code == 200:
            return JsonResponse({"message": "Payment Successful", "data": response_data})
        return JsonResponse(
            {"message": "Payment Verification Failed", "data": response_data},
            status=400,
        )

    return JsonResponse({"error": "Invalid request"}, status=400)
