from django.shortcuts import render
from django.http import HttpResponse

def hello_pawcat(request):
    return HttpResponse("hello pawcat")