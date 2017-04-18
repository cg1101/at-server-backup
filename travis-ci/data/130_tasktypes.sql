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
-- Data for Name: tasktypes; Type: TABLE DATA; Schema: public; Owner: gcheng
--

COPY tasktypes (tasktypeid, name, description) FROM stdin;
1	translation	\N
2	text collection	\N
3	markup	\N
4	3-way translation	\N
5	DEFT like	\N
6	audio checking	\N
7	transcription	\N
\.


--
-- Name: tasktypes_tasktypeid_seq; Type: SEQUENCE SET; Schema: public; Owner: gcheng
--

SELECT pg_catalog.setval('tasktypes_tasktypeid_seq', 7, true);


--
-- PostgreSQL database dump complete
--

