from flask import Flask, render_template, request, redirect, jsonify
import os
from time import time
from wallet import Wallet
from wallet import Account
import firebase_admin
from firebase_admin import credentials
import json
from flask_cors import CORS

STATIC_DIR = os.path.abspath('static')

app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)
app.use_static_for_root = True

myWallet =  Wallet()
account = None
allAccounts = []
user= None
isSignedIn = False

receiverAddress = None
tnxAmount = None

paymentStatus = None

def firebaseInitialization():
    cred = credentials.Certificate("config/newServiceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://testingsep-d4d10-default-rtdb.firebaseio.com'})
    print("🔥🔥🔥🔥🔥 Firebase Connected! 🔥🔥🔥🔥🔥")

firebaseInitialization()

@app.route("/", methods= ["GET", "POST"])
def home():
    global myWallet, account, allAccounts, isSignedIn, receiverAddress, tnxAmount
    isConnected = myWallet.checkConnection()
   
    balance = "No Balance"
    transactions = None
    
    transactionData = {}
    balanceData = {}

    if(isSignedIn):
        allAccounts = myWallet.getAccounts()
        if(account == None and allAccounts):
            account = allAccounts[0]

        if(account):
            address = 0
            if(type(account) == dict):
                balance = myWallet.getBalance(account['address'])
                transactions = myWallet.getTransactions(account['address'])
                address= account['address']
            else:
                balance = myWallet.getBalance(account.address)
                transactions = myWallet.getTransactions(account.address)
                address= account.address

            amountList = []
            colorList=[]
            indicesTransactions = []

            balanceList=[float(balance)]
            indicesBalance = [0]
            

            reverseTransactions = transactions[::-1]
            for index, transaction in enumerate(reverseTransactions):
                amountList.append(float(transaction["amount"]))
                colorList.append("red" if transaction["from"] == address else "blue")
                indicesTransactions.append(index)
                
            traceTnx = {
                'x': indicesTransactions,
                'y': amountList,
                'name': 'Amount',
                'type': 'bar',
                'marker': { 'color' : colorList }
            }
    
            layoutTnx = {
                'title': 'Transaction History',
                'xaxis': { 'title': 'Transaction Index' },
                'yaxis': { 'title': 'Amount(ETH)' }
            }

            transactionData ={
                 'trace': [traceTnx], 
                 'layout': layoutTnx
                 }
            
            transactionData = json.dumps(transactionData)

            for index, transaction in enumerate(transactions):
                if transaction['from'] == address:
                    balance = float(balance) + float(transaction['amount']) 
                else:
                    balance = float(balance) - float(transaction['amount'])
                balanceList.append(balance)
                indicesBalance.append(index+1)
            
            balanceList = balanceList[::-1]
            traceBalance= {
                    'x': indicesBalance,
                    'y': balanceList,
                    'name': 'Account Balance',
                    'mode': 'lines+markers', 
                    'line': {
                        'color': 'blue'
                    },
                    'marker': {
                        'color': colorList
                    }
                }
            layoutBalance = {
                    'title': 'Balance History',
                    'xaxis': { 'title': 'Time' },
                    'yaxis': { 'title': 'Amount(ETH)' },
                }
            balanceData ={
                 'trace': [traceBalance], 
                 'layout': layoutBalance
                 }
            balanceData = json.dumps(balanceData)

    return render_template('index.html', 
                        isConnected=isConnected,  
                        account= account, 
                        balance = balance, 
                        transactions = transactions, 
                        allAccounts=allAccounts,
                        isSignedIn = isSignedIn,
                        transactionData = transactionData,
                        balanceData = balanceData,
                        receiverAddress = receiverAddress,
                        tnxAmount = tnxAmount)



@app.route("/makeTransaction", methods = ["GET", "POST"])
def makeTransaction():
    global myWallet, account, receiverAddress, tnxAmount, paymentStatus

    receiver = request.form.get("receiverAddress")
    amount = request.form.get("amount")

    privateKey = None
    if(type(account) == dict):
            privateKey = account['privateKey']
            sender= account['address']
    else:
            privateKey = account.privateKey
            sender= account.address

    privateKey = account['privateKey']

    tnxHash = myWallet.makeTransactions(sender, receiver, amount, privateKey)
    myWallet.addTransactionHash(tnxHash, sender, receiver,amount)
    if(receiverAddress):
        receiverAddress = None
        tnxAmount =None
        paymentStatus = True

    return redirect("/")


@app.route("/createAccount", methods= ["GET", "POST"])
def createAccount(): 
    global account, myWallet
    username = myWallet.username
    account = Account(username)
    return redirect("/")

@app.route("/changeAccount", methods= ["GET", "POST"])
def changeAccount(): 
    global account, allAccounts
    
    newAccountAddress = int(request.args.get("address"))
    account = allAccounts[newAccountAddress]
    return redirect("/")

@app.route("/signIn", methods= ["GET", "POST"])
def signIn(): 
    global account, allAccounts, isSignedIn, myWallet
    isSignedIn = True
    
    username = request.form.get("user")
    password = request.form.get("password")
    
    isSignedIn = myWallet.addUser(username, password)
    return redirect("/")

@app.route("/signOut", methods= ["GET", "POST"])
def signOut(): 
    global account, allAccounts, isSignedIn
    isSignedIn = False
    return redirect("/")

@app.route('/payment')
def payment():
    global receiverAddress, tnxAmount

    receiverAddress = request.args.get("address")
    tnxAmount = int(request.args.get("amount"))/100000
    
    return redirect('/')

@app.route('/checkPaymentStatus')
def checkPaymentStatus():
    global paymentStatus, account
    address = None
    if(type(account) == dict):
            address= account['address']
    else:
            address= account.address

    if paymentStatus == True:
        paymentStatus = None
        return jsonify(True, address)
    
    return jsonify(paymentStatus, address)

# Create route /renameAccount
@app.route('/renameAccount', methods= ["GET", "POST"])
def renameAccount():
    global myWallet, account
    accountName = request.form.get("name")

    if(type(account) == dict):
        address= account['address']
    else:
        address= account.address

    myWallet.addAccountName(accountName, address)

    return redirect('/')
    
    


# if __name__ == '__main__':
#     app.run(debug = True, port=5000)



