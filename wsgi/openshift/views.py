import os
import urllib
import urllib2
import json
import sys
import sendgrid
import cStringIO

from xml.dom import minidom

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie

#Create a bunch of carrier data
verizon = {"name":"Verizon", "sms":"vtext.com", "mms":"vzwpix.com"}
att = {"name":"AT&T", "sms":"txt.att.net","mms":"txt.att.net"}
tmobile = {"name":"T-Mobile", "sms":"tmomail.net", "mms":"tmomail.net"}
sprint = {"name":"Sprint", "sms":"messaging.sprintpcs.com","mms":"messaging.sprintpcs.com"}

carriers = [verizon, att, tmobile, sprint]

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

        #Download cat image
        catImage = cStringIO.StringIO(urllib.urlopen(catImageUrl).read())

        #Init sendgrid API
        sgClient = sendgrid.SendGridClient(api_user, api_key)

        #Determine which carrier we are sending to and how many emails we need to send
        for c in carriers:
          if carrier == c["name"]:

            #If the sms and mms targets are the same, we just send one message
            if(c["sms"] == c["mms"]):
              print phoneNumber + "@" + c["sms"]

              message = sendgrid.Mail()
              message.add_to("Cat Lover <"+phoneNumber + "@" + c["sms"] +">")
              message.set_subject("Requested Cat")
              message.set_text(catFact)
              message.set_from("getcats.me")
              message.add_attachment('catImage.jpg', catImage)

              status, postResponse = sgClient.send(message)

            #Otherwise we have to send two messages; one for the sms target and one for the mms
            else:
              print phoneNumber + "@" + c["sms"]
              print phoneNumber + "@" + c["mms"]

              smsMessage = sendgrid.Mail()
              mmsMessage = sendgrid.Mail()

              smsMessage.add_to("Cat Lover <"+phoneNumber + "@" + c["sms"] +">")
              smsMessage.set_subject("Requested Cat")
              smsMessage.set_text(catFact)
              smsMessage.set_from("getcats.me")

              smsStatus, smsPostResponse = sgClient.send(smsMessage)

              mmsMessage.add_to("Cat Lover <"+phoneNumber + "@" + c["mms"] +">")
              mmsMessage.set_subject("Requested Cat")
              mmsMessage.set_text(" ")
              mmsMessage.add_attachment('catImage.jpg', catImage)
              mmsMessage.set_from("getcats.me")

              mmsStatus, mmsPostResponse = sgClient.send(mmsMessage)

              postResponse = mmsPostResponse

              #TODO handle a scenerio where one post works and the other fails
              #this should result in overall failure sent to the client

            break;

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
