from .. import db
from .base_model import BaseModel
from datetime import datetime

class Sale(BaseModel):
    __tablename__ = 'sales'

    total_amount = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False, default=0.0)  # NEW: Track total cost
    payment_type = db.Column(db.String(100), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('SalesItem', back_populates='sale', cascade='all, delete-orphan', lazy='dynamic')
    
    @property
    def total_profit(self):
        '''Calculate total profit for this sale'''
        return self.total_amount - self.total_cost
    
    @property
    def profit_margin_percentage(self):
        '''Calculate profit margin as percentage'''
        if self.total_amount > 0:
            return (self.total_profit / self.total_amount) * 100
        return 0

class SalesItem(BaseModel):  # FIXED: Changed from OrderItem to SalesItem
    __tablename__ = 'sales_items'

    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False, default=0.0)  # NEW: Track unit cost
    product_name = db.Column(db.String(100), nullable=False)

    sale = db.relationship('Sale', back_populates='items')
    product = db.relationship('Product', back_populates='sales_items')  # FIXED: Updated reference

    def get_subtotal(self):
        '''Revenue for this item'''
        return self.quantity * self.unit_price
    
    def get_cost_total(self):
        '''Total cost for this item'''
        return self.quantity * self.unit_cost
    
    def get_profit(self):
        '''Profit for this item'''
        return self.get_subtotal() - self.get_cost_total()
    
    def get_profit_margin_percentage(self):
        '''Profit margin percentage for this item'''
        subtotal = self.get_subtotal()
        if subtotal > 0:
            return (self.get_profit() / subtotal) * 100
        return 0