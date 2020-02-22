from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect    
import requests
import json
import time

import hubspotDeals 

broadcastTables = False

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

def getDealId():
    response = requests.get("https://aqueous-wave-55186.herokuapp.com/getDeal")
    if response.status_code == 200:
        test = response.json()
        dealID = test['dealID']
    else:
        print('No Deals')
        dealID = 0
    return dealID

@socketio.on('connect')
def initalBrowserConnect():
    global broadcastTables
    print ("connected")
    #
    # update deal tables
    #
   #hubspotDeals.getRecentDeals()
    broadcastTables = True



def background_thread():
    """Example of how to send server generated events to clients."""
    global broadcastTables
    prevDealID = 0
    while True:
        #socketio.sleep(5)
        time.sleep(5)
        print ("Getting Deals")
        dealID = getDealId()
        print (dealID)

        #
        # if a new client joins, send the tables
        #
        if broadcastTables:
            broadcastTables = False

            try:
                sortedDollarTable
            except NameError:
                hubspotDeals.getRecentDeals()


            sortedDollarTable = hubspotDeals.getDealTotalDollar()
            sortedCountTable  = hubspotDeals.getDealTotalCount()
            #print ('Sorted Dollar = ' + str(sortedDollarTable) )
            #print ('Sorted Count = ' + str(sortedCountTable) )

            socketio.emit('totalDollar', sortedDollarTable, namespace='/test')
            socketio.emit('totalCount', sortedCountTable, namespace='/test')    
            print ('Inital Table Sent')


        if dealID > 0 : #and prevDealID != dealID:
            dealInfo    = hubspotDeals.getDealDetails(dealID)
            dealOwner   = hubspotDeals.getDealOwner(dealInfo ['properties']['hubspot_owner_id']['value'])
            firstName   = dealOwner['firstName']
            lastName    = dealOwner['lastName']
            #print (dealOwner)
            socketio.emit('my_response',
                          {'data': 'Deal Closed ', 'ID': dealID, 'Name' : dealInfo ['properties']['dealname']['value']  , 'Value' :  dealInfo ['properties']['amount']['value'] , 'firstName' : firstName, 'lastName' : lastName },
                          namespace='/test')
            prevDealID = dealID
            #
            # update deal tables
            #
            hubspotDeals.getRecentDeals()
            sortedDollarTable = hubspotDeals.getDealTotalDollar()
            sortedCountTable  = hubspotDeals.getDealTotalCount()
            print ('Sorted Dollar = ' + str(sortedDollarTable) )
            print ('Sorted Count = ' + str(sortedCountTable) )

            socketio.emit('totalDollar', sortedDollarTable, namespace='/test')
            socketio.emit('totalCount', sortedCountTable, namespace='/test')


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    #emit('my_response', {'data': 'Connected', 'count': 0})


if __name__ == '__main__':
    print ("hello")
    socketio.run(app)

