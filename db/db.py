#!/usr/bin/env python

import socket

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

hostname = socket.gethostname()
is_remote = not hostname.startswith('macbookair20')

if is_remote:
	dbUrl = 'postgresql://localhost/atdb'
	echo = False
else:
	#dbUrl = 'postgresql://dbserver/appentext'
	dbUrl = 'postgresql://localhost/atdb'
	echo = False
engine = create_engine(dbUrl, echo=echo)

SS = scoped_session(sessionmaker(bind=engine))

__all__ = ["engine", "SS"]
