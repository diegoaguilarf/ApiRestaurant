# Imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from flask_graphql import GraphQLView
import logging
# app initialization
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))


# Configs
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.debug = True

db = SQLAlchemy(app)

# Modules
# TO-DO
# Models
class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=True)
    image = db.Column(db.String(256), index=True)
    tag = db.Column(db.String(256), index=True)
    
    def __repr__(self):
        return '<Restaurant %r>' % self.name

class Rfid(db.Model):
    __tablename__ = 'rfid_tags'
    uid = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.String(256), db.ForeignKey('restaurants.uid'))
    uuid_rfid = db.Column(db.String(256), index=True)
    label = db.Column(db.String(256), index=True)
    def __repr__(self):
        return '<Rfid %r>' % self.uuid_rfid
        
class Meal(db.Model):
    __tablename__ = 'meals'
    uid = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.String(256), db.ForeignKey('restaurants.uid'))
    name = db.Column(db.String(256), index=True)
    price = db.Column(db.Integer)
    image = db.Column(db.String(256), index=True)
    description = db.Column(db.Text)
    def __repr__(self):
        return '<Meal %r>' % self.name

# Schema Objects
class RestaurantObject(SQLAlchemyObjectType):
    class Meta:
        model = Restaurant
        interfaces = (graphene.relay.Node, )

    meals = graphene.List(lambda: MealObject, id=graphene.String())
    def resolve_meals(self, info, id):
        query = Meal.get_query(info)
        return query.filter(Meal.restaurant_id == id).all()

class RfidObject(SQLAlchemyObjectType):
   class Meta:
       model = Rfid
       interfaces = (graphene.relay.Node, )

class MealObject(SQLAlchemyObjectType):
   class Meta:
       model = Meal
       interfaces = (graphene.relay.Node, )

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_restaurants = SQLAlchemyConnectionField(RestaurantObject)
    all_rfid_tags = SQLAlchemyConnectionField(RfidObject)
    all_meals = SQLAlchemyConnectionField(MealObject)

    restaurant = graphene.Field(lambda: RestaurantObject, id=graphene.String())
    def resolve_restaurant(self, info, id):
        query = User.get_query(info)
        return query.filter(Restaurant.id == id).first()

    meal = graphene.relay.Node.Field(RestaurantObject)

class CreateRestaurant(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        image = graphene.String(required=True)
        tag = graphene.String(required=True)
    
    restaurant = graphene.Field(lambda: RestaurantObject)

    def mutate(self, info, name, image, tag):
        restaurant = Restaurant(name=name, image=image, tag=tag)
        
        db.session.add(restaurant)
        db.session.commit()

        return CreateRestaurant(restaurant=restaurant)

class CreateMeal(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Int(required=True)
        image = graphene.String(required=True)
        description = graphene.String(required=True)
        restaurant_id = graphene.ID(required=True)
    
    meal = graphene.Field(lambda: MealObject)

    def mutate(self, info, name, price, image, description, restaurant_id):
        meal = Meal(name=name, price=price, image=image, description=description, restaurant_id=restaurant_id)

        db.session.add(meal)
        db.session.commit()

        return CreateMeal(meal=meal)

class Mutation(graphene.ObjectType):
    create_restaurant = CreateRestaurant.Field()
    create_meal = CreateMeal.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

# Routes
app.add_url_rule(
    '/graphql',
    view_func = GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)

@app.route('/')
def index():
    return '<p> Hello World</p>'
if __name__ == '__main__':
     app.run()
