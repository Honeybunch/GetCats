import os
import urllib
import urllib2
import json
import sys
import smtplib

from xml.dom import minidom

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie

@ensure_csrf_cookie
def home(request):
    return render_to_response("home/home.html")

def getCat(request):

    if request.method == "GET":
        response = HttpResponse(getRandomCat())
        return response
    else:
		return HttpResponse("You're in the wrong place")
	
@csrf_protect	
def sendCat(request):
    if request.method == "POST":
        #Data for posting
        api_user = "aarsentufsc2842"
        api_key = "apikey"
        
        #Get user info
        phoneNumber = request.POST.get("phoneNumber", "")
        carrier = request.POST["carrier"]
        
        #Get cat data
        catData = json.loads(getRandomCat())
        catImageUrl = catData["image"]
        catFact = catData["fact"]
		
        apiDataString = "api_user=" + api_user + "&api_key=" + api_key + "&to=" + phoneNumber + "@" + carrier + "&toname=Pussy Lover&subject=Requested Pussy" + "&text=" + catFact + "&from=getpussy.me"
		
        print apiDataString
        
        postResponse = urllib2.urlopen("https://api.sendgrid.com/api/mail.send.json", apiDataString)
        
        response = HttpResponse(postResponse)
        
        response["Access-Control-Allow-Origin"] = "*"  
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"  
        response["Access-Control-Max-Age"] = "1000"  
        response["Access-Control-Allow-Headers"] = "*" 
        return response
    else:
        return HttpResponse("You're in the wrong place")

		
def getRandomCat():
    catImage = ""
    catFact = ""

    catImageResponse = urllib2.urlopen("http://thecatapi.com/api/images/get?format=xml&results_per_page=1&type=jpg").read()
    catFactResponse = urllib2.urlopen("http://catfacts-api.appspot.com/api/facts?number=1").read()

    #Parse image response
    catResponseXML = minidom.parseString(catImageResponse)
    catResponse = findChildNodeByName(catResponseXML, "response")
    catResponseData = findChildNodeByName(catResponse, "data")
    catResponseImages = findChildNodeByName(catResponseData, "images")
    catResponseImage = findChildNodeByName(catResponseImages, "image")
    catResponseURL = findChildNodeByName(catResponseImage, "url")
    catImageSRC = catResponseURL.childNodes[0].nodeValue
	
	#Parse fact response
    catFactJSON = json.loads(catFactResponse)
    
    #Check if everything went okay
    if not catImageSRC == None and not catImageSRC.endswith(".jpg"):
        return "{\"success\":false, \"error\":\"bad image\"}"
		
    if catFactJSON["success"] != "true":
        return "{\"success\":false, \"error\":\"bad fact\"}"

    #Build JSON response
    catImage = catImageResponse;
    catFact = catFactJSON["facts"][0]

    #Return JSON blob
    response = "{\"success\":true , \"image\": \""+catImageSRC+"\" , \"fact\" : \""+catFact+"\"}"
	
    return response

#Gets the first child node
def findChildNodeByName(parent, name):
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.localName == name:
            return node
    return None