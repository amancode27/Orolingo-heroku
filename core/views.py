
# todo/views.py

from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, views, viewsets, permissions, status          # add this
from .serializers import *      # add this
from .models import *
from .permissions import UserPermission
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication  # added this
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from requests.exceptions import HTTPError
from social_django.utils import load_strategy, load_backend
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden
import json
from django.core import serializers
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
stripe.api_key = settings.STRIPE_SECRET_KEY
# Email imports
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str,force_str,smart_bytes,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.urls import reverse

class UserView(viewsets.ModelViewSet):       # add this
    # authentication_classes=[TokenAuthentication] #added this
    # permission_classes= [IsAuthenticated] #added this
    permission_classes = (UserPermission,)
    serializer_class = UserSerializerWithToken          # add this
    queryset = User.objects.all()               # add this


@api_view(['GET'])
def current_user(request):  # Determine the current user by their token, and return their data

    serializer = UserSerializer(request.user)
    return Response(serializer.data)

class SocialLoginView(generics.GenericAPIView):
    """Log in using facebook"""
    serializer_class = SocialSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Authenticate user through the provider and access_token"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.data.get('provider', None)
        strategy = load_strategy(request)
        new_account = True

        try:
            backend = load_backend(strategy=strategy, name=provider, redirect_uri=None)

        except MissingBackend:
            return Response({'error': 'Please provide a valid provider'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if isinstance(backend, BaseOAuth2):
                access_token = serializer.data.get('access_token')
            user_details = backend.user_data(access_token)
            if User.objects.filter(username=user_details['email']).exists():
                new_account = False
            user = backend.do_auth(access_token)
        except HTTPError as error:
            return Response({
                "error": {
                    "access_token": "Invalid token",
                    "details": str(error)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except AuthTokenError as error:
            return Response({
                "error": "Invalid credentials",
                "details": str(error)
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            authenticated_user = backend.do_auth(access_token, user=user)
        except HTTPError as error:
            return Response({
                "error": "invalid token",
                "details": str(error)
            }, status=status.HTTP_400_BAD_REQUEST)

        except AuthForbidden as error:
            return Response({
                "error": "invalid token",
                "details": str(error)
            }, status=status.HTTP_400_BAD_REQUEST)

        if authenticated_user and authenticated_user.is_active:
            # generate JWT token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            data = {
                "token": jwt_encode_handler(
                    jwt_payload_handler(user)
                )}
            # customize the response to your needs
            if not (authenticated_user.is_student or authenticated_user.is_trainer):
                new_account = True
            response = {
                "email": authenticated_user.email,
                "username": authenticated_user.username,
                "token": data.get('token'),
                "fullname": authenticated_user.fullname,
                "newAccount": new_account,
                "userId": authenticated_user.id,
                "is_student": authenticated_user.is_student,
                "is_trainer": authenticated_user.is_trainer
            }
            
            return Response(status=status.HTTP_200_OK, data=response)


# Create a new user.A get method for retrieving a list of all User objects.
class UserList(APIView):

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = UserSerializerWithToken(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    # def post(self, request, format=None):
    #     serializer = StudentSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseView(viewsets.ViewSet):

    def list(self, request):
        queryset = Course.objects.all()
        serializer = CourseSerializer(queryset, many = True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)

class AssignmentView(viewsets.ViewSet):

    def list(self, request):
        queryset = Assignment.objects.all()
        serializer = AssignmentSerilaizer(queryset, many = True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = AssignmentSerilaizer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FeedbackView(viewsets.ViewSet):
    def list(self,request):
        queryset = Feedback.objects.all()
        serializer = FeedBackSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = FeedBackSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForumListAPIView(generics.ListAPIView):
    serializer_class = ForumSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        queryset = Forum.objects.all()
        student_course = self.request.query_params.get('student_course', None)
        if student_course is not None:
            queryset = queryset.filter(student_course=student_course)
        return queryset

class ForumCreateAPIView(generics.CreateAPIView):
    serializer_class = ForumSerializer
    queryset = Forum.objects.all()
    permission_classes = [AllowAny]
    Forum.last_activity = naturaltime(Forum.created_at)

class ForumDetailAPIView(generics.RetrieveAPIView):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

class ForumDeleteAPIView(generics.DestroyAPIView):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

class ForumUpdateAPIView(generics.UpdateAPIView):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'



@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def save_stripe_info(request):
    data = request.data
    email = data['email']
    payment_method_id = data['payment_method_id']
    course = Course.objects.get(pk=data['course_id'])
    student = Student.objects.get(pk=data['student_id'])
    customer_data = stripe.Customer.list(email=email).data   
    # creating customer

    if len(customer_data) == 0:
        # creating customer
        customer = stripe.Customer.create(
        email=email, payment_method=payment_method_id)
    else:
        customer = customer_data[0]
    try:
        stripe.PaymentIntent.create(
                customer=customer, 
                payment_method=payment_method_id,  
                currency='inr', # you can provide any currency you want
                amount=(course.cost)*100,
                confirm = True,
                )

        student_course = StudentCourse()
        student_course.student = student
        student_course.course = course
        student_course.completed_percent = 0
        student_course.save()
        return Response(status=status.HTTP_200_OK, 
            data={
            'message': 'Success', 
            'data': {'customer_id': customer.id},
            })

    except stripe.error.CardError as e:
        body = e.json_body
        err = body.get('error', {})
        return Response({"message": f"{err.get('message')}"}, status=HTTP_400_BAD_REQUEST)

    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        messages.warning(self.request, "Rate limit error")
        return Response({"message": "Rate limit error"}, status=HTTP_400_BAD_REQUEST)

    except stripe.error.InvalidRequestError as e:
        print(e)
        # Invalid parameters were supplied to Stripe's API
        return Response({"message": "Invalid parameters"}, status=HTTP_400_BAD_REQUEST)

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        return Response({"message": "Not authenticated"}, status=HTTP_400_BAD_REQUEST)

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        return Response({"message": "Network error"}, status=HTTP_400_BAD_REQUEST)

    except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
        return Response({"message": "Something went wrong. You were not charged. Please try again."}, status=HTTP_400_BAD_REQUEST)

    except Exception as e:
        # send an email to ourselves
        return Response({"message": "A serious error occurred. We have been notifed."}, status=HTTP_400_BAD_REQUEST)

    return Response({"message": "Invalid data received"}, status=HTTP_400_BAD_REQUEST)

class VideosView(viewsets.ViewSet):
    def list(self, request):
        queryset = Videos.objects.all()
        serializer = VideosSerializer(queryset, many = True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = VideosSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TellUsView(viewsets.ViewSet):
    def list(self, request):
        queryset = TellUs.objects.all()
        serializer = TellUsSerializer(queryset, many = True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = TellUsSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

import jwt
import base64
import hashlib
import hmac
import requests
import json
import time
from django.conf import settings
from django.http import JsonResponse


ZOOM_API_KEY = 'nY9FhJK4QQmnM90nykssNg'
ZOOM_API_SECRET = 'HOGHZ4SBspALOgX5Yzw87Hku8Zd5kiNVffSZ'
ZOOM_USER_ID = 'Aryan'


def ZoomJWTToken(request):
    token = jwt.encode(
        # Create a payload of the token containing API Key & exp time
        {"iss": ZOOM_API_KEY, "exp": time.time() + 60000},
        # Secret used to generate token signature
        ZOOM_API_SECRET,
        # Specify the hashing alg
        algorithm='HS256'
    ).decode('utf-8')

    meeting_data = {
        "topic": "Sample Discussion",
        "type": "1",
        "duration": "60",
        "password": "IamThe",
        "agenda": "To discuss various plans meeting",
        "settings": {
            "host_video": "true",
            "participant_video": "true",
            "join_before_host": "true",
            "mute_upon_entry": "true",
            "watermark": "true",
            "use_pmi": "false",
            "approval_type": "0",
            "audio": "both",
            "auto_recording": "cloud"
        }
    }
    # simplejson(meeting_data)
    meeting_json_data = json.dumps(meeting_data)
    URL = 'https://api.zoom.us/v2/users/' + ZOOM_USER_ID + '/meetings'
    print(f"URL: {URL}    Data: {meeting_json_data} \n\n Typeof dta: {type(meeting_json_data)}")
    req = requests.post(URL, data=meeting_json_data,
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}).json()
    return JsonResponse({'zoom_signature': token, 'meeting_response': req})


def ZoomMeetingSignature(request):
    zoom_meeting_role = '1'
    timestamp = int(round(time.time() * 1000)) - 30000
    string_message = ZOOM_API_KEY + str(request.GET.get('meeting_number')) + str(timestamp) + \
                     zoom_meeting_role
    message = base64.b64encode(bytes(string_message, 'utf-8'))
    secret = bytes(ZOOM_API_SECRET, 'utf-8')
    hashing = hmac.new(secret, message, hashlib.sha256)
    hashing = base64.b64encode(hashing.digest())
    hashing = hashing.decode("utf-8")
    temp_string = "%s.%s.%s.%s.%s" % (ZOOM_API_KEY, str(request.GET.get('meeting_number')), str(timestamp),
                                      zoom_meeting_role, hashing)
    signature = base64.b64encode(bytes(temp_string, "utf-8"))
    signature = signature.decode("utf-8")
    print(f"Meeting No: {request.GET.get('meeting_number')}")
    return JsonResponse({'signature': signature.rstrip("=")})

# Password Reset

class RequestPasswordResetEmail(generics.GenericAPIView):

    serializer_class = RequestPasswordResetEmailSerializer
    permission_classes = (permissions.AllowAny,)
    def post(self,request):
        serializer = self.serializer_class(data = request.data)
        email = request.data['email']
        if User.objects.filter(email = email).exists():
            user = User.objects.get(email = email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request = request).domain
            relativeLink = reverse('password-reset-confirm' , kwargs = {'uidb64':uidb64 ,'token':token })
            # absurl = 'http://' + current_site + relativeLink
            absurl = 'https://orolingo-staging.herokuapp.com/password-reset-confirm/'
            email_body = 'Hello, \n Please use the below link to reset your password. Enter the one-time token and ID for password reset. Thank you!\n' + 'http://'+absurl
            email_body += '\nID: ' + str(uidb64) + '\nToken: ' + str(token)
            email_body+= '\n\nRegards,\nTeam Orolingo'
            data = {'email_body':email_body , 'to_email': user.email , 
                'email_subject':'Reset your password'
            }
            Util.send_email(data)
            return Response({'success':'We have sent you a link to reset your password'}, status = status.HTTP_200_OK)
        else:
            return Response({'Falure':'User does not have a account'}, status = status.HTTP_400_BAD_REQUEST)

class PasswordTokenCheckAPI(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self,request,uidb64,token):
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id = id)

            if not PasswordResetTokenGenerator().check_token(user,token):
                return Response({'error':'Token is not valid anymore, please request a new one'},status = status.HTTP_400_BAD_REQUEST)
            return Response({'success': True , 'message': 'Credentials Valid' , 'uidb64': uidb64, 'token': token} , status = status.HTTP_200_OK)

        except DjangoUnicodeDecodeError as identifier:
            return Response({'error':'Token is not valid anymore, please request a new one'},status = status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class =  SetNewPasswordSerializer
    permission_classes = (permissions.AllowAny,)
    def patch(self,request):
        serializer = self.serializer_class(data = request.data)

        serializer.is_valid(raise_exception = True)
        return Response({'success':True , 'message':'Password reset success'}, status = status.HTTP_200_OK)
