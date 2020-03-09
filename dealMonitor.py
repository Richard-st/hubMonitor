from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect    
import requests
import json
import time
import os 

import hubspotDeals 


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None
UPLOAD_FOLDER = 'static/img/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3'}

app = Flask(__name__)
app.config['SECRET_KEY']    = 'secret!'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio                    = SocketIO(app, async_mode=async_mode)
thread                      = None
thread_lock                 = Lock()

sortedDollarTable           = {}
sortedCountTable            = {}


def getFilesInDir():

    staticDir = 'static/img/uploads/'
    uploadDir = {}

    with os.scandir(staticDir) as entries:
        for entry in entries:
            if entry.is_file():
                uploadDir[entry.name] = entry.path

    return uploadDir


#
# valid upload types
#
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#
# check for new closed deals
#
def getDealId():
    response = requests.get("https://aqueous-wave-55186.herokuapp.com/getDeal")
    if response.status_code == 200:
        test = response.json()
        dealID = test['dealID']
    else:
        print('No Deals')
        dealID = 0
    return dealID

#
# when a client browser connects to /index, send tables to browser
#
@socketio.on('connect'  , namespace='/index')
def initalBrowserConnect():
    global broadcastTables
    global sortedDollarTable
    global sortedCountTable

    #
    # if we dont have the deal table information, refresh. Shol donly be required on server startup
    #
    if not sortedDollarTable:
        print ('Refreshing Deals' )
        hubspotDeals.getRecentDeals()
        sortedDollarTable = hubspotDeals.getDealTotalDollar()
        sortedCountTable  = hubspotDeals.getDealTotalCount()

    #
    # send tables to browsers
    #
    socketio.emit('totalDollar', sortedDollarTable, namespace='/index')
    socketio.emit('totalCount', sortedCountTable, namespace='/index')    

#
# when a client browser connects to /admin, send dictionary of thumbnails
#
@socketio.on('connect'  , namespace='/admin')
def sendThumbnailsToAdmin():
    #
    # send tables to browsers
    #
    print ('Emit admin refreshThumbnails')
    fileDiList = getFilesInDir()
    socketio.emit('refreshThumbnails', fileDiList, namespace='/admin')

#
# image file delete
#
@socketio.on('deleteRepImgFile'  , namespace='/admin')
def deleteRepImgFile(fln):
    print ("fln - " + str(fln))
    deleteFln = 'static/img/uploads/' + fln["data"]
    os.remove(deleteFln)
    print("File Removed!")
    sendThumbnailsToAdmin()


#
# thread checking for  new deals. If found, broadcast details to clients
#
def background_thread():
    global broadcastTables
    global sortedDollarTable
    global sortedCountTable   

    prevDealID = 0
    while True:
        socketio.sleep(5)
        print ("Checking for new deals")
        dealID = getDealId()
        print ("Found deal - " + str(dealID)) 



        if dealID > 0 and prevDealID != dealID:
            #
            # send rep information for browser to display
            #
            dealInfo    = hubspotDeals.getDealDetails(dealID)
            dealOwner   = hubspotDeals.getDealOwner(dealInfo ['properties']['hubspot_owner_id']['value'])
            firstName   = dealOwner['firstName']
            lastName    = dealOwner['lastName']

            socketio.emit('new_deal',
                          {'data': 'Deal Closed ', 'ID': dealID, 'Name' : dealInfo ['properties']['dealname']['value']  , 'Value' :  dealInfo ['properties']['amount']['value'] , 'firstName' : firstName, 'lastName' : lastName },
                          namespace='/index')
            prevDealID = dealID

            #
            # update deal tables
            #
            hubspotDeals.getRecentDeals()
            sortedDollarTable = hubspotDeals.getDealTotalDollar()
            sortedCountTable  = hubspotDeals.getDealTotalCount()
            #print ('Sorted Dollar = ' + str(sortedDollarTable) )
            #print ('Sorted Count = ' + str(sortedCountTable) )

            socketio.emit('totalDollar', sortedDollarTable, namespace='/index')
            socketio.emit('totalCount', sortedCountTable, namespace='/index')



#
# main display
#
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

#
# image loading
#
@app.route('/admin')
def admin():
    return render_template('admin.html', async_mode=socketio.async_mode)


@app.route('/file-upload', methods=["POST"])
def fileUpload():
    print ("file upload" )
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return ""  
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            print('No selected file')
            return ""  
        if file and allowed_file(file.filename):
            #filename = secure_filename(file.filename)
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #
            sendThumbnailsToAdmin()
            return ""   
    return ""



print("starting thread")
with thread_lock:
    if thread is None:
        thread = socketio.start_background_task(background_thread)


if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0',debug= True )

