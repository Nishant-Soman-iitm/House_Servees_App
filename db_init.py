from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, select, Float, DateTime, func
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

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
    base_price = Column(Float)  # Add base price column

class Service_Request(Base):
    __tablename__ = 'service_request'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_email = Column(String, ForeignKey('customer_details.Email'), nullable=False)
    professional_email = Column(String, ForeignKey('professional_details.Email'), nullable=False)
    slot_date = Column(String, nullable=False)
    slot_time = Column(String, nullable=False)
    status = Column(String, default='Pending')  # Add status to track request state
    created_at = Column(DateTime, default=func.current_timestamp())  # Timestamp for request creation
    
    # Relationships
    customer = relationship('Customer_Details', back_populates='service_requests')
    professional = relationship('Professional_details', back_populates='service_requests')

class JobReview(Base):
    __tablename__ = 'job_reviews'
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey('booking.booking_id'), nullable=False)
    review_text = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    booking = relationship('Booking', back_populates='reviews')

class Booking(Base):
    __tablename__ = 'booking'
    booking_id = Column(Integer, primary_key=True)
    slot_time = Column(String)  # No foreign key constraint
    slot_date = Column(String)  # No foreign key constraint
    professional_email = Column(String, ForeignKey('professional_details.Email'))
    customer_email = Column(String, ForeignKey('customer_details.Email'))
    status = Column(String, default='Pending')
    payment_status = Column(String, default='Pending')  # Add payment status column
    start_time = Column(DateTime)  # Add start time column
    end_time = Column(DateTime)  # Add end time column

    # Relationships for professional and customer
    professional = relationship('Professional_details')
    customer = relationship('Customer_Details')
    reviews = relationship('JobReview', back_populates='booking')

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