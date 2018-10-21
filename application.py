from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
# from sqlalchemy import create_engine, asc, desc
from sqlalchemy import asc, desc
# from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask_sqlalchemy import SQLAlchemy
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
db = SQLAlchemy(app)

# Connect to Database and create database session
# engine = create_engine('sqlite:///catalog.db')
# Base.metadata.bind = engine

# DBSession = sessionmaker(bind=engine)
# session = DBSession()

@app.context_processor
def inject_dict_for_all_templates():
    if 'username' in login_session and 'user_id' in login_session:
        return dict(username = login_session['username'], user_id = login_session['user_id'])
    else:
        return dict()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE = state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    print(h.request(url, 'GET')[1])
    result = json.loads(str(h.request(url, 'GET')[1], encoding = 'utf-8'))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/')
@app.route('/catalog')
def showCatalogHome():
    categories = db.session.query(Category).order_by(asc(Category.name))
    items = db.session.query(Item).order_by(desc(Item.id)).limit(10)
    print(items[0].category.name)
    return render_template('catalogHome.html', categories=categories, items = items)

@app.route('/JSON/')
@app.route('/catalog/JSON/')
def showCatalogJson():
    categoryList = []
    categories = db.session.query(Category).order_by(asc(Category.name))
    for category in categories:
        items = db.session.query(Item).\
        filter_by(category_id=category.id)

        itemList = []
        for item in items:
            itemList.append(item.serialize)
        
        categoryDict = {'id': category.id, 'name': category.name, 'items': itemList}
        categoryList.append(categoryDict)

    return jsonify(categoryList)    

@app.route('/catalog/<string:category_name>/items/')
def showCategory(category_name):
    categories = db.session.query(Category).order_by(asc(Category.name))
    selectedCategory = db.session.query(Category).\
        filter_by(name=category_name).one()
    items = db.session.query(Item).\
        filter_by(category_id=selectedCategory.id).\
        order_by(desc(Item.id))
    return render_template('category.html', categories=categories, selectedCategory=selectedCategory, items=items)

@app.route('/catalog/<string:category_name>/items/JSON/')
def showCategoryJson(category_name):
    selectedCategory = db.session.query(Category).\
        filter_by(name=category_name).one()
    items = db.session.query(Item).\
        filter_by(category_id=selectedCategory.id)

    itemList = []
    for item in items:
        itemList.append(item.serialize)
    
    categoryDict = {'id': selectedCategory.id, 'name': selectedCategory.name, 'items': itemList}
    
    return jsonify(category = categoryDict)

@app.route('/catalog/<string:category_name>/<string:item_name>/')
def showItem(category_name, item_name):
    item, category = db.session.query(Item, Category).\
        filter(Item.category_id == Category.id).\
        filter(Category.name == category_name, Item.name == item_name).one()
    print(item)
    return render_template('item.html', item=item)

@app.route('/catalog/<string:category_name>/<string:item_name>/JSON/')
def showItemJson(category_name, item_name):
    item, category = db.session.query(Item, Category).\
        filter(Item.category_id == Category.id).\
        filter(Category.name == category_name, Item.name == item_name).one()
    return jsonify(item = item.serialize)

@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def addItem():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newItem = Item(name = request.form['itemName'], description = request.form['description'], category_id = request.form['category'], 
            user_id = login_session['user_id'])
        db.session.add(newItem)
        db.session.commit()
        flash('%s item created' % newItem.name)
        return redirect(url_for('showCatalogHome'))

    else:
        categories = db.session.query(Category).order_by(asc(Category.name))
        return render_template('newItem.html', categories=categories)

@app.route('/catalog/<string:category_name>/<string:item_name>/edit/', methods=['GET', 'POST'])
def editItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem, category = item, category = db.session.query(Item, Category).\
        filter(Item.category_id == Category.id).\
        filter(Category.name == category_name, Item.name == item_name).one()
    if login_session['user_id'] != editedItem.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit items you did not create.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['itemName']:
            editedItem.name = request.form['itemName']
        if request.form['description']:
            editedItem.description = request.form['description']
        db.session.add(editedItem)
        db.session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showCatalogHome'))
    else:
        return render_template('editItem.html', item=editedItem)

@app.route('/catalog/<string:category_name>/<string:item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete, category = item, category = db.session.query(Item, Category).\
        filter(Item.category_id == Category.id).\
        filter(Category.name == category_name, Item.name == item_name).one()
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete items you did not create.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        db.session.delete(itemToDelete)
        db.session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showCatalogHome'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)

# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    db.session.add(newUser)
    db.session.commit()
    user = db.session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = db.session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = db.session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)