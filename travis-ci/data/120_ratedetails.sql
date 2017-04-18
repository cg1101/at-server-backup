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
-- Data for Name: ratedetails; Type: TABLE DATA; Schema: public; Owner: gcheng
--

COPY ratedetails (rateid, centsperutt, accuracy) FROM stdin;
1	0	0.599999999999999978
1	0.900000000000000022	0.800000000000000044
1	1	0.930000000000000049
2	0	0.5
2	0.900000000000000022	0.75
2	1	0.930000000000000049
3	1	0
4	0	0.5
4	0.989999999999999991	0.699999999999999956
4	1	0.930000000000000049
\.


--
-- PostgreSQL database dump complete
--

