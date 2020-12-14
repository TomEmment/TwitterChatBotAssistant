import random
import aiml
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize 
import csv
import math
import re
import tweepy
from collections import Counter
stopwords = stopwords.words('english')


consumer_key = 'X4GdKJsPC5FwUypV4R4yQWlWk'
consumer_secret = 'zF9m8Sra9lDnXC7iNkLG8AzT9ZlN7OblRqR64GdSuiPFiOg4TE'
access_token = '1318227698762874884-ahsWaaDBIjf0Zl9fnSST4OBmrG413O'
access_token_secret = '9Derhjj0xTXUXWCHxGyrYFCfYmZrRCApYQIkFIAGnFC42'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)

WORD = re.compile(r"\w+")

#Get bag of words

BagOfWords = []

with open('CourseworkPart1Data.csv', newline='') as csvfile:
    Sentances = csv.reader(csvfile)
    for row in Sentances:
        TempWords = row[0].lower()
        Words = TempWords.split()
        for w in Words:
            if w in BagOfWords:
                Position = BagOfWords.index(w) +1
                BagOfWords[Position] = BagOfWords[Position] +1
            else:
                BagOfWords.append(w)
                BagOfWords.append(1)
    csvfile.close()


def ImplementFrequency(Vector):
    for x in BagOfWords:
        if BagOfWords.index(x)%2 == 0:
            if Vector[x] != 0:
                Vector[x] = Vector[x]/BagOfWords[BagOfWords.index(x) +1]
    return Vector
    
def CleanString(text):
    text = text.lower()
    temp = word_tokenize(text)
    temp1 = temp
    #temp = {w for w in temp if not w in stopwords}
    #if temp == "":
        #temp = temp1
    text = repr(temp)
    words = WORD.findall(text)
    return Counter(words)

def CreateVectors(Message,Orginal = False):
    vectors = CleanString(Message)
    if not Orginal:
        vectors = ImplementFrequency(vectors)
    return vectors

def CalculateCosine(vec1,vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def FindBestResponseInCSV(Message):
    MessageVector = CreateVectors(Message,True)
    Response = ""
    Highest = 0
    Choice = random.randint(1,3)
    with open('CourseworkPart1Data.csv', newline='') as csvfile:
        Sentances = csv.reader(csvfile)
        for row in Sentances:
            MessageVector1 = CreateVectors(row[0].lower())
            Result = CalculateCosine(MessageVector,MessageVector1)
            if Result>Highest:
                Highest = Result
                Response = row[Choice]
        csvfile.close()
    return Response

def FindBestUserInCSV(Message):
    MessageVector = CreateVectors(Message,True)
    Response = ""
    Highest = 0
    with open('TwitterCheck.csv', newline='') as csvfile:
        Sentances = csv.reader(csvfile)
        for row in Sentances:
            MessageVector1 = CreateVectors(row[0].lower())
            Result = CalculateCosine(MessageVector,MessageVector1)
            if Result>Highest:
                Highest = Result
                Response = row[1]
        csvfile.close()
    return Response

kern = aiml.Kernel()
kern.setTextEncoding(None)

kern.bootstrap(learnFiles="CourseworkPart1.xml")

print("Welcome to this Twitter chat bot. Please feel free to ask for me to search for tweets or people for you")

while True:
    try:
        Message = input("Enter your Message: ")
    except (KeyboardInterrupt, EOFError) as e:
        print("Bye!")
        break


    answer = kern.respond(Message)

    if answer[0] == '#':
        params = answer[1:].split('$')
        cmd = int(params[0])
        if cmd == 0:
            print(params[1])
            break
        elif cmd ==1:
            Search = params[1]
            Number = 0
            for tweet in tweepy.Cursor(api.search,q=Search,count=1,lang="en").items():
                if Number == 0:
                    Reply = WORD.findall(tweet.text)
                    Reply = " ".join(Reply)
                    print("My search for ", Search ," found the following most recent tweet: ", Reply)
                Number = Number +1
        elif cmd == 2:
            TwitterName = params[1]
            Return = FindBestUserInCSV(TwitterName)
            if Return == "":
                print("I couldnt find that user")
                Users = api.search_users(TwitterName,15)
                print("Is it any of the following?")
                Number = 0
                with open('TwitterCheck.csv','a', newline='') as csvfile:
                    NewNames = csv.writer(csvfile)
                    while Number <5:
                        try:
                            print(Users[Number].name)
                            NewNames.writerow([Users[Number].name,Users[Number].id])
                            Number = Number +1
                        except:
                            Number = Number +1
                    csvfile.close()
                Choice = input("->")
                Choice = Choice.lower()
                Return = FindBestUserInCSV(Choice)
            Return = api.user_timeline(Return,count=1)
            if Return == "":
                print("Unable to pull tweet, user could be on priavate or tweet contains unique text (1)")
            for status in Return:
                Reply = WORD.findall(status.text)
                Reply = " ".join(Reply)
                print("Most recent tweet by ", TwitterName ,": ", Reply)

        elif cmd == 99:
            Message = Message.lower()
            Return = FindBestResponseInCSV(Message)
            if Return == "TWEETSEARCH":
                Return = FindBestUserInCSV(Message)
                if Return == "":
                    print("I couldnt find that user")
                else:
                    Name = Return
                    Return = api.user_timeline(Return,count=1)
                    if Return == "":
                        print("Unable to pull tweet, user could be on priavate or tweet contains unique text (2)")
                    for status in Return:
                        Reply = WORD.findall(status.text)
                        Reply = " ".join(Reply)
                        print("Most recent tweet by ", Name ,": ", status.text.encode())

            elif Return != "":
                print(Return)
            else:
                print("I dont understand, could you try rephrasing the question?")
    else:
        print(answer)
