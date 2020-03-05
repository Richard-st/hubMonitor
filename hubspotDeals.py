import requests
import datetime

import time
import config

#setup empty deal tables

dealTotalDollar         = {}
dealTotalCount          = {}
sortedDealTotalDollar   = {}
sortedDealTotalCount    = {}
ownerDetails            = {}

def getLastMondayTS():
    today           = datetime.date.today()
    lastMonday      = today - datetime.timedelta(days=today.weekday())
    lastMondayTS    = int(time.mktime(lastMonday.timetuple() ) )

    #debug make timestamp 10 minutes ago
    #lastMondayTS    = int(time.time()) - 86400 

    return  str(lastMondayTS * 1000 )


def getMondayTimestamp():
    today = datetime.date.today()
    return  (today - datetime.timedelta(days=today.weekday()) )
    
def getDealOwner(ownerId):

    print("getDealOwneR")
    print (ownerDetails.keys())
    print (ownerId)
    if (ownerId in ownerDetails.keys() ):
        return ownerDetails['ownerId']
    else:
        response = requests.get( config.hubspot['getOwnerEndPoint'] + str(ownerId) + "?hapikey=" + config.hubspot['api'])
        resJson = response.json()
        ownerDetails[ownerId]={}
        ownerDetails[ownerId]['firstName']=resJson['lastName']
        #ownerDetails[ownerId]['lastname']=resJson['lastName']
        print ("owner Details")
        print (str(resJson))        
        print (str(ownerDetails))        
        return ownerDetails[ownerId]


def getDealDetails(dealId):
    response = requests.get( config.hubspot['getDealEndPoint'] + str(dealId) + "?hapikey=" + config.hubspot['api'])
    resJson = response.json()
    return response.json()

def addDealToTablesV2(deal):
    global dealTotalDollar
    global dealTotalCount 
    owner                                    = deal['properties']['hubspot_owner_id']['value']
    ownerDetails                             = getDealOwner(owner)
    if owner in dealTotalDollar:
        dealTotalDollar[owner]['totalDollar']   =  float ( dealTotalDollar[owner]['totalDollar'])  + float(deal['properties']['hs_closed_amount']['value'])
    else:
        dealTotalDollar[owner]                  =  {}
        dealTotalDollar[owner]['firstName']     =  ownerDetails["firstName"]
        #dealTotalDollar[owner]['lastName']      =  ownerDetails["lastName"]
        dealTotalDollar[owner]['totalDollar']   =  float(deal['properties']['hs_closed_amount']['value'])

    if owner in dealTotalCount:
        dealTotalCount[owner]['totalDeals']     =  int( dealTotalCount[owner]['totalDeals'])  + 1
    else:
        dealTotalCount[owner]                   =  {}
        dealTotalDollar[owner]['firstName']     =  ownerDetails["firstName"]
        #dealTotalDollar[owner]['lastName']      =  ownerDetails["lastName"]
        dealTotalCount[owner]['totalDeals']     =  1


def addDealToTables(dealDetail):
    # owner :  1234, Firstname , lastname, total $ {'123456' : ["firstName":"Richard","lastName":"Stanners","total":"123.45" ]}
    # owner, Firstname , lastname, total deals
    global dealTotalDollar
    global dealTotalCount 


    owner                                   = dealDetail['properties']['hubspot_owner_id']['value']
    ownerDetails                            = getDealOwner(owner)

    if owner in dealTotalDollar:
        dealTotalDollar[owner]['totalDollar']   =  float ( dealTotalDollar[owner]['totalDollar'])  + float( dealDetail['properties']['amount']['value'] )
    else:
        dealTotalDollar[owner]                  =  {}
        dealTotalDollar[owner]['firstName']     =  ownerDetails["firstName"]
        dealTotalDollar[owner]['lastName']      =  ownerDetails["lastName"]
        dealTotalDollar[owner]['totalDollar']   =  float(dealDetail['properties']['amount']['value'])

    if owner in dealTotalCount:
        dealTotalCount[owner]['totalDeals']     =  int( dealTotalCount[owner]['totalDeals'])  + 1
    else:
        dealTotalCount[owner]                   =  {}
        dealTotalCount[owner]['firstName']      =  ownerDetails["firstName"]
        dealTotalCount[owner]['lastName']       =  ownerDetails["lastName"]
        dealTotalCount[owner]['totalDeals']     =  1



    #print (dealTotalDollar)
    #print (dealTotalCount)
    #print ("Sorted by Dollar " + str( sorted(dealTotalDollar, key=lambda x: (dealTotalDollar[x]['totalDollar']) ,reverse=True ) ) )
    #print ("Sorted by Count " + str ( sorted(dealTotalCount, key=lambda x: (dealTotalCount[x]['totalDeals']) ,reverse=True ) ) )
    

def sortDealTable(dictToSort, sortKey):

    sortedTable = {}
    sortedKeys =  sorted(dictToSort, key=lambda x: (dictToSort[x][sortKey]) ,reverse=True ) 
    rank = 0

    for key in sortedKeys:
        rank +=1
        #sortedTable['rank'] = rank
        #sortedTable[key] = dictToSort[key]
        sortedTable[rank] = dictToSort[key]

    sortedTable['NoOfRows']   = rank
    #print ('Sorted Keys = ' + str(sortedKeys))
    #print ('Sorted Dict = ' + str(sortedTable))
    return sortedTable


def getDealTotalDollar():
    global sortedDealTotalDollar
    return sortedDealTotalDollar

def getDealTotalCount():
    global sortedDealTotalCount
    return sortedDealTotalCount

def getRecentDeals():

    #
    # clear deal tables
    #
    global dealTotalDollar
    global dealTotalCount
    global sortedDealTotalDollar
    global sortedDealTotalCount

    dealTotalDollar         = {}
    dealTotalCount          = {}
    # 
    # get last Sun/Mon midnight
    #
    lastMondayTS    = getLastMondayTS()

    apiOffset       = 0
    dealGetURLBase  = config.hubspot['getRecentDealsEndPoint'] + "?hapikey=" + config.hubspot['api'] + '&since=' + lastMondayTS + '&count=' + config.hubspot['dealRetreiveCount']
    dealGetURL      = dealGetURLBase + '&offset='+ str(apiOffset) 

    print (dealGetURL)
    response        = requests.get( dealGetURL )
    resJson         = response.json()
    firstcall       = True


    print ('v2 got response')
    while resJson['offset'] < resJson['total'] or firstcall == True:
        firstcall = False
        for deal in resJson['results']:
            #
            # check if deal is offline and closed
            #
            if (deal['isDeleted']                                == False and
                deal['properties']['pipeline']['value']          == config.hubspot['offlineDealPipeline'] and
                str(deal['properties']['dealstage']['value'])    == config.hubspot['OfflineClosedWon']):
                    #
                    # check if the deal was closed won this week
                    #
                    #V2 dealDetail = getDealDetails(deal['dealId'])      
                    #V2 dealCloseTS = int(dealDetail['properties']['closedate']['value'])   #remove ms
                    #V2 print (int(dealDetail['properties']['closedate']['value']) )
                    #V2 if dealCloseTS > int(lastMondayTS) :
                    print ('v2 got deal')

                    if 'closedate' in deal['properties'].keys():
                        print (str(deal['properties']['closedate']))
                        if int(deal['properties']['closedate']['value']) > int(lastMondayTS) :
                            print('Offline Deal:'+ str(deal['dealId']) + ' Pipeline: ' + deal['properties']['pipeline']['value'] + ' Stage: ' + str(deal['properties']['dealstage']['value']) + 'owner: ' + str(deal['properties']['hubspot_owner_id']['value'])  )
                            #v2 addDealToTables(dealDetail)
                            addDealToTablesV2(deal)
                          

        #
        # get next block of modified deals
        #
        apiOffset   = resJson['offset']
        dealGetURL  = dealGetURLBase + '&offset='+ str(apiOffset) 
        response    = requests.get( dealGetURL )
        #print (dealGetURL)
        resJson     = response.json()
    #
    # Sort tables
    #
    sortedDealTotalDollar = sortDealTable(dealTotalDollar,'totalDollar') 
    sortedDealTotalCount  = sortDealTable(dealTotalCount,'totalDeals') 

