import rest_framework.authtoken.models
from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from .models import Country
from .serializers import CountrySerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import mixins
from rest_framework import generics
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authtoken.models import Token


# Create your views here.

class GenericApiView(generics.GenericAPIView,mixins.ListModelMixin,mixins.CreateModelMixin,mixins.UpdateModelMixin,mixins.DestroyModelMixin,mixins.RetrieveModelMixin):

    # authentication_classes = [BasicAuthentication, SessionAuthentication]
    # authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = CountrySerializer
    queryset = Country.objects.all()
    lookup_field = 'id'

    def get(self,request, id):
        if id:
            return self.retrieve(request, id)
        return self.list(request)
    def post(self,request):
        return self.create(request)
    def put(self,request, id):
        return self.update(request,id)
    def delete(self,request,id):
        return self.destroy(request,id)









class CountryView(APIView):
    def get(self, request):
        obj = Country.objects.all()
        serializer = CountrySerializer(obj, many=True)

        return Response(serializer.data)
    def post(self, request):
        serializer = CountrySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

@api_view(["GET", "POST"])
def country_list(request):
    if request.method == 'GET':
        obj = Country.objects.all()
        serializer = CountrySerializer(obj, many=True)

        return Response(serializer.data)
    elif request.method == 'POST':
        # data = JSONParser().parse(request)
        serializer = CountrySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_400_BAD_REQUEST)

class CountryDetailView(APIView):
    def get_object(self, pk):
        try:
            return Country.objects.get(pk=pk)
        except Country.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        country = self.get_object(pk)
        serializer = CountrySerializer(country)
        return Response(serializer.data)
    def put(self, request, pk):
        country = self.get_object(pk)
        serializer = CountrySerializer(country, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        country = self.get_object(pk)

        country.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



@csrf_exempt
def country_detail(request, pk):
    try:
        country = Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = CountrySerializer(country)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = CountrySerializer(country, data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)


    elif request.method == 'DELETE':
        country.delete()
        return HttpResponse(status=204)


@api_view(["GET", "POST"])
def login(request):
    data = request.data

    auth = authenticate(request, username=data['username'], password=data['password'])

    if auth :
        token = Token.objects.filter(user=auth).first()

        if not token:
            token = Token.objects.create(user=auth)

        return Response({"success": True,"token": token.key})

    return Response({"success": False, "message": "Invalid credentials"}, status=401)

@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(True)