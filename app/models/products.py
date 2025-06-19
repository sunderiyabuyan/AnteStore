from .. import db
from .base_model import BaseModel

class Product(BaseModel):
    __tablename__ = 'products'

    name = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.Float, nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, index=True)
    stock_level = db.Column(db.Integer, default=0, nullable=False)
    description = db.Column(db.Text)

    # FIXED: Changed from order_items to sales_items to match relationship
    sales_items = db.relationship('SalesItem', back_populates='product', cascade='all, delete-orphan')

    def is_in_stock(self, quantity=1): 
        return self.stock_level >= quantity 

    @property
    def total_sold(self):
        return sum(item.quantity for item in self.sales_items)

    @property
    def total_revenue(self):
        return sum(item.get_subtotal() for item in self.sales_items)

    def reduce_stock(self, quantity): 
        if self.is_in_stock(quantity):
            self.stock_level -= quantity
            return True
        return False