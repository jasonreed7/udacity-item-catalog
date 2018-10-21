from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

soccer = Category(name = 'Soccer')
basketball = Category(name = 'Basketball')
baseball = Category(name = 'Baseball')
frisbee = Category(name = 'Frisbee')
snowboarding = Category(name = 'Snowboarding')
rock_climbing = Category(name = 'Rock Climbing')
foosball = Category(name = 'Foosball')
skating = Category(name = 'Skating')
hockey = Category(name = 'Hockey')

session.add_all([soccer, basketball, baseball, frisbee, snowboarding, rock_climbing, foosball, skating, hockey])
session.commit()

user = User(name = 'First User', email = 'a@b.com')

session.add(user)
session.commit()

snowboard = Item(name = 'Snowboard', 
    description = 'It is a snowboard',
    category_id = snowboarding.id,
    user_id = user.id)

skates = Item(name = 'Skates', 
    description = 'They are skates',
    category_id = skating.id,
    user_id = user.id)

session.add_all([snowboard, skates])
session.commit()
