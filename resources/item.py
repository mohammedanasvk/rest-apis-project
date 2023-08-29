
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from model.item import ItemModel
from schemas import ItemSchema,ItemUpdateSchema,StoreSchema
from db import db
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import get_jwt, jwt_required

blp=Blueprint("item",__name__,description="operation on items")

@blp.route("/item")
class ItemList(MethodView):
    @jwt_required()
    @blp.response(200,ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()
    
    @blp.arguments(ItemSchema)
    @blp.response(200,ItemSchema)
    def post(self,item_data):
        item=ItemModel(**item_data)
        
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500,"An error occured while inserting item")
        return item

@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @blp.response(200,ItemSchema)
    def get(self,item_id):
        item=ItemModel.query.get_or_404(item_id)
        return item
    
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200,ItemSchema)
    def put(self,item_data,item_id):
        item=ItemModel.query.get(item_id)
        if item:
            item.price=item_data["price"]
            item.name=item_data["name"]
        else:
            item=ItemModel(id=item_id,**item_data)

        db.session.add(item)
        db.session.commit()

        return item
            
    @jwt_required()
    def delete(self,item_id):
        jwt=get_jwt()
        if not jwt.get("is_admin"):
            abort(401,"Admin privileage required")

        item=ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message":"item got deleted"}





