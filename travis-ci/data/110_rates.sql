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
-- Data for Name: rates; Type: TABLE DATA; Schema: public; Owner: gcheng
--

COPY rates (rateid, name, centsperutt, maxcentsperutt, targetaccuracy) FROM stdin;
1	Standard Curve	1	1.04000000000000004	0.849999999999999978
2	Lenient Curve	1	1.04000000000000004	0.849999999999999978
3	Flat Curve	1	1	1
4	Extra Lenient Curve	1	1.04000000000000004	0.849999999999999978
\.


--
-- Name: rates_rateid_seq; Type: SEQUENCE SET; Schema: public; Owner: gcheng
--

SELECT pg_catalog.setval('rates_rateid_seq', 4, true);


--
-- PostgreSQL database dump complete
--

