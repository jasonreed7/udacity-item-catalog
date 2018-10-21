from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
# from sqlalchemy import create_engine, asc, desc
from sqlalchemy import asc, desc
# from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
db = SQLAlchemy(app)

# Connect to Database and create database session
# engine = create_engine('sqlite:///catalog.db')
# Base.metadata.bind = engine

# DBSession = sessionmaker(bind=engine)
# session = DBSession()

@app.route('/')
def showCatalogHome():
    categories = db.session.query(Category).order_by(asc(Category.name))
    items = db.session.query(Item).order_by(desc(Item.id)).limit(10)
    print(items[0].category.name)
    return render_template('catalogHome.html', categories=categories, items = items)

@app.route('/catalog/<string:category_name>/items/')
def showCategory(category_name):
    categories = db.session.query(Category).order_by(asc(Category.name))
    selectedCategory = db.session.query(Category).\
        filter_by(name=category_name).one()
    items = db.session.query(Item).\
        filter_by(category_id=selectedCategory.id).\
        order_by(desc(Item.id))
    return render_template('category.html', categories=categories, selectedCategory=selectedCategory, items=items)

@app.route('/catalog/<string:category_name>/<string:item_name>/')
def showItem(category_name, item_name):
    item, category = db.session.query(Item, Category).\
        filter(Item.category_id == Category.id).\
        filter(Category.name == category_name, Item.name == item_name).one()
    print(item)
    return render_template('item.html', item=item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)