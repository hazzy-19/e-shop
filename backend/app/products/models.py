from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image_url = Column(String)
    is_active = Column(Boolean, default=True) # Added soft delete
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    order_items = relationship("OrderItem", back_populates="product")
    category = relationship("Category", back_populates="products")
