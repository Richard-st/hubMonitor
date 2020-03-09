import requests
import datetime

import time

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
dealSumaryRunning       = False

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
    global ownerDetails

    if (ownerId in ownerDetails.keys() ):
        print ("owner in cache " + str(ownerId))
        return ownerDetails[ownerId]
    else:
        print ("owner NOT in cache " + str(ownerId))
        response = requests.get( config.hubspot['getOwnerEndPoint'] + str(ownerId) + "?hapikey=" + config.hubspot['api'])
        resJson = response.json()
        ownerDetails[ownerId]={}
        if ( (resJson['firstName'] == "") and (resJson['lastName'] == "")):
            ownerDetails[ownerId]['firstName']  = resJson['email'].partition(".")[0].capitalize() 
            ownerDetails[ownerId]['lastName']   = resJson['email'].replace("@yellow.co.nz","").partition(".")[2].capitalize() 
        else:
            ownerDetails[ownerId]['firstName']=resJson['firstName'].capitalize()
            ownerDetails[ownerId]['lastName']=resJson['lastName'].capitalize()
        return ownerDetails[ownerId]


def getDealDetails(dealId):
    response = requests.get( config.hubspot['getDealEndPoint'] + str(dealId) + "?hapikey=" + config.hubspot['api'])
    resJson = response.json()
    return response.json()

def addDealToTablesV2(deal):
    global dealTotalDollar
    global dealTotalCount 
    owner                                    = deal['properties']['hubspot_owner_id']['value']


    ownerDetail = getDealOwner(owner)


    if owner in dealTotalDollar:
        dealTotalDollar[owner]['totalDollar']   =  float ( dealTotalDollar[owner]['totalDollar'])  + float(deal['properties']['hs_closed_amount']['value'])
    else:
        dealTotalDollar[owner]                  =  {}
        dealTotalDollar[owner]['firstName']     =  ownerDetail["firstName"]
        dealTotalDollar[owner]['lastName']      =  ownerDetail["lastName"]
        dealTotalDollar[owner]['totalDollar']   =  float(deal['properties']['hs_closed_amount']['value'])

    if owner in dealTotalCount:
        dealTotalCount[owner]['totalDeals']     =  int( dealTotalCount[owner]['totalDeals'])  + 1
    else:
        dealTotalCount[owner]                   =  {}
        dealTotalCount[owner]['firstName']     =  ownerDetail["firstName"]
        dealTotalCount[owner]['lastName']      =  ownerDetail["lastName"]
        dealTotalCount[owner]['totalDeals']     =  1
    
    



    

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
    global dealSumaryRunning
    
    if dealSumaryRunning: 
        return
    
    dealSumaryRunning = True

    dealTotalDollar         = {}
    dealTotalCount          = {}
    # 
    # get last Sun/Mon midnight
    #
    lastMondayTS    = getLastMondayTS()

    apiOffset       = 0
    dealGetURLBase  = config.hubspot['getRecentDealsEndPoint'] + "?hapikey=" + config.hubspot['api'] + '&since=' + lastMondayTS + '&count=' + config.hubspot['dealRetreiveCount']
    dealGetURL      = dealGetURLBase + '&offset='+ str(apiOffset) 

    print ("Deal URL : " + dealGetURL)
    response        = requests.get( dealGetURL )
    resJson         = response.json()
    moreData        = True


    while moreData:
        for deal in resJson['results']:
            #
            # check if deal is offline and closed
            #
            if deal["dealId"] == '1681786123':
                print ("++++++++++Deal returned")           
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

                    if 'closedate' in deal['properties'].keys():
                        if int(deal['properties']['closedate']['value']) > int(lastMondayTS) :
                            #print('Offline Deal:'+ str(deal['dealId']) + ' Pipeline: ' + deal['properties']['pipeline']['value'] + ' Stage: ' + str(deal['properties']['dealstage']['value']) + 'owner: ' + str(deal['properties']['hubspot_owner_id']['value'])  )
                            #v2 addDealToTables(dealDetail)
                            addDealToTablesV2(deal)

             
        if  resJson['hasMore'] == True:
            #
            # get next block of modified deals
            #
            apiOffset   = resJson['offset']
            dealGetURL  = dealGetURLBase + '&offset='+ str(apiOffset) 
            response    = requests.get( dealGetURL )
            print (dealGetURL)
            resJson     = response.json()
        else:
            moreData    = False
    #
    # Sort tables
    #
    sortedDealTotalDollar = sortDealTable(dealTotalDollar,'totalDollar') 
    sortedDealTotalCount  = sortDealTable(dealTotalCount,'totalDeals') 
    dealSumaryRunning = False


