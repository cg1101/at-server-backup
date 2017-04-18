--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.2
-- Dumped by pg_dump version 9.6.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

--
-- Data for Name: filehandlers; Type: TABLE DATA; Schema: public; Owner: gcheng
--

COPY filehandlers (handlerid, name, description) FROM stdin;
1	plaintext	\N
2	tdf	\N
\.


--
-- Name: filehandlers_handlerid_seq; Type: SEQUENCE SET; Schema: public; Owner: gcheng
--

SELECT pg_catalog.setval('filehandlers_handlerid_seq', 2, true);


--
-- PostgreSQL database dump complete
--

