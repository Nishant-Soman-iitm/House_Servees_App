import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, select
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Slots(Base):
    __tablename__ = 'slots'
    slot_time = Column(String, primary_key=True)
    slot_date = Column(String, primary_key=True)
    professional_email = Column(String, ForeignKey('professional_details.Email'))
    professional = relationship('Professional_details', back_populates='slots')
    service_id = Column(String, ForeignKey('service.id'))
    is_booked = Column(Boolean, default=False)  # Add a field to track if slot is booked
    # Method to update slot status after a booking is made
    def book_slot(self):
        self.is_booked = True


class Customer_Details(Base):
    __tablename__ = 'customer_details'
    Email = Column(String, primary_key=True, unique=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String)
    phone = Column(Integer, unique=True)
    city = Column(String)
    aadhaar = Column(String, unique=True)  # Add Aadhaar card number column

    # Reverse relationship to access service requests for this customer
    service_requests = relationship('Service_Request', back_populates='customer', lazy='subquery')


class Professional_details(Base):
    __tablename__ = 'professional_details'
    professional_id = Column(Integer, primary_key=True, autoincrement=True)
    Email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String)
    phone = Column(String)
    city = Column(String)
    profession = Column(String)
    availability = Column(Boolean, default=True)  # Availability of the professional
    aadhaar = Column(String, unique=True)  # Add Aadhaar card number column
    # Reverse relationship to access service requests for this professional
    service_requests = relationship('Service_Request', back_populates='professional')
    
    # Reverse relationship to access slots for this professional
    slots = relationship('Slots', back_populates='professional')


class service(Base):
    __tablename__ = 'service'
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Service_Request(Base):
    __tablename__ = 'service_request'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_email = Column(String, ForeignKey('customer_details.Email'), nullable=False)
    professional_email = Column(String, ForeignKey('professional_details.Email'), nullable=False)
    slot_date = Column(String, nullable=False)
    slot_time = Column(String, nullable=False)
    status = Column(String, default='Pending')  # Add status to track request state
    created_at = Column(Integer, default=sqlalchemy.func.current_timestamp())  # Timestamp for request creation
    
    # Relationships
    
    customer = relationship('Customer_Details', back_populates='service_requests')
    professional = relationship('Professional_details', back_populates='service_requests')


from sqlalchemy import ForeignKey

class Booking(Base):
    __tablename__ = 'booking'
    booking_id = Column(Integer, primary_key=True)
    slot_time = Column(String)  # No foreign key constraint
    slot_date = Column(String)  # No foreign key constraint
    professional_email = Column(String, ForeignKey('professional_details.Email'))
    customer_email = Column(String, ForeignKey('customer_details.Email'))
    status = Column(String, default='Pending')

    # Relationships for professional and customer
    professional = relationship('Professional_details')
    customer = relationship('Customer_Details')

    # Method to retrieve the slot dynamically
    def get_slot(self, session):
        # Retrieve the corresponding slot from the Slots table based on slot_time and slot_date
        return session.query(Slots).filter_by(
            slot_time=self.slot_time,
            slot_date=self.slot_date
        ).first()




# Create the engine and update the database schema
engine = create_engine('sqlite:///HouseServees.db')
Base.metadata.create_all(engine)  # Creates the tables if they don't exist

# Query the database
if __name__ == '__main__':
    stmt = select(Professional_details)
    print("----------Querying the database----------")
    
    with engine.connect() as connection:
        result = connection.execute(stmt)
        print("Professional_Details : -")
        for row in result:
            print(row)
    stmt2 = select(Customer_Details)
    with engine.connect() as connection:
        result = connection.execute(stmt2)
        print("Customer_Details : -")
        for row in result:
            print(row)
