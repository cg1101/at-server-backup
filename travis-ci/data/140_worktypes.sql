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
-- Data for Name: worktypes; Type: TABLE DATA; Schema: public; Owner: gcheng
--

COPY worktypes (worktypeid, name, description, modifiestranscription) FROM stdin;
1	Work	\N	t
2	QA	\N	f
3	Rework	\N	t
4	2ndPass_work	\N	t
6	2ndPass_rework	\N	t
\.


--
-- Name: worktypes_worktypeid_seq; Type: SEQUENCE SET; Schema: public; Owner: gcheng
--

SELECT pg_catalog.setval('worktypes_worktypeid_seq', 6, true);


--
-- PostgreSQL database dump complete
--

