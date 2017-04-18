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
-- Data for Name: batchingmodes; Type: TABLE DATA; Schema: public; Owner: gcheng
--

COPY batchingmodes (modeid, name, description, requirescontext) FROM stdin;
1	None	\N	t
2	Performance	\N	t
3	File	\N	t
5	Custom Context	\N	t
6	Allocation Context	\N	t
\.


--
-- Name: batchingmodes_modeid_seq; Type: SEQUENCE SET; Schema: public; Owner: gcheng
--

SELECT pg_catalog.setval('batchingmodes_modeid_seq', 6, true);


--
-- PostgreSQL database dump complete
--

