import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import select

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship

Base = declarative_base()

class Customer_Details(Base):
    __tablename__ = 'customer_details'
    Email = Column(String, primary_key=True,unique=True,nullable=False)
    password = Column(String,nullable=False)
    name = Column(String)
    phone = Column(Integer,unique=True)
    city = Column(String)

class Professional_details(Base):
    __tablename__ = 'professional_details'
    Email = Column(String, primary_key=True)
    password = Column(String)
    name = Column(String)
    phone = Column(String)
    city = Column(String)
    profession = Column(String)

engine = create_engine('sqlite:///HouseServees.db')
Base.metadata.create_all(engine)  # Creates the tables if they don't exist

# Query the database
if __name__ == '__main__':
    stmt = select(Customer_Details)
    print("----------Querying the database----------")
    
    with engine.connect() as connection:
        result = connection.execute(stmt)
        for row in result:
            print(row)

'''class Service_Professional(Base):
    __tablename__ = 'service_professional'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    services = relationship('Service', back_populates='service_professional')

class Service(Base):
    __tablename__ = 'service'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    service_professional_id = Column(Integer, ForeignKey('service_professional.id'))
    service_professional = relationship('Service_Professional', back_populates='services')
    price = Column(Integer)

class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    services = relationship('Service', secondary='booking')# many to many relationship

class Booking(Base):
    __tablename__ = 'booking'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('service'))
    customer_id = Column(Integer, ForeignKey('customer'))
    service = relationship('Service', back_populates='bookings')
    customer = relationship('Customer', back_populates='services')
    date = Column(String)
    time = Column(String)'''