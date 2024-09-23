import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, Date, ForeignKey, LargeBinary, Enum as SQLAlchemyEnum, Integer
from sqlalchemy.orm import relationship
from database import Base
from schemas import EventStatusEnum

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_restricted = Column(Boolean, default=False)
    create_event = Column(Boolean, default=True)
    create_form = Column(Boolean, default=True)
    view_registrations = Column(Boolean, default=False)

    events = relationship("Event", back_populates="owner")
    pending_events = relationship("PendingEvent", back_populates="user")

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_name = Column(String, index=True)
    venue_address = Column(String)
    event_date = Column(Date)
    audience = Column(Boolean, default=False)
    delegates = Column(Boolean, default=False)
    speaker = Column(Boolean, default=False)
    nri = Column(Boolean, default=False)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    owner = relationship("User", back_populates="events")

    forms = relationship("EventForm", back_populates="event", cascade="all, delete-orphan")
    image = relationship("ImageModel", back_populates="event", uselist=False, cascade="all, delete-orphan")

class PendingEvent(Base):
    __tablename__ = "pending_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_name = Column(String, index=True)
    venue_address = Column(String)
    event_date = Column(Date)
    audience = Column(Boolean, default=False)
    delegates = Column(Boolean, default=False)
    speaker = Column(Boolean, default=False)
    nri = Column(Boolean, default=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    status = Column(SQLAlchemyEnum(EventStatusEnum), default=EventStatusEnum.PENDING)

    user = relationship("User", back_populates="pending_events")

class EventForm(Base):
    __tablename__ = "event_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    name = Column(String, index=True)
    email = Column(String)
    phoneno = Column(String)
    dropdown = Column(String)
    qr_code = Column(LargeBinary)

    event = relationship("Event", back_populates="forms")

class ImageModel(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), unique=True, nullable=False)
    filename = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)

    event = relationship("Event", back_populates="image")