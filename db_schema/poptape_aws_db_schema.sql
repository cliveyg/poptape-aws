--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: poptape_aws
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO poptape_aws;

--
-- Name: aws_details; Type: TABLE; Schema: public; Owner: poptape_aws
--

CREATE TABLE public.aws_details (
    public_id character varying(36) NOT NULL,
    "aws_CreateUserRequestId" character varying(300),
    "aws_UserId" character varying(300),
    "aws_UserName" character varying(300),
    "aws_AccessKeyId" character varying(300),
    "aws_SecretAccessKey" character varying(300),
    "aws_PolicyName" character varying(100),
    "aws_Arn" character varying(500),
    "aws_CreateDate" timestamp without time zone NOT NULL
);


ALTER TABLE public.aws_details OWNER TO poptape_aws;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: poptape_aws
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: aws_details aws_details_aws_AccessKeyId_key; Type: CONSTRAINT; Schema: public; Owner: poptape_aws
--

ALTER TABLE ONLY public.aws_details
    ADD CONSTRAINT "aws_details_aws_AccessKeyId_key" UNIQUE ("aws_AccessKeyId");


--
-- Name: aws_details aws_details_aws_Arn_key; Type: CONSTRAINT; Schema: public; Owner: poptape_aws
--

ALTER TABLE ONLY public.aws_details
    ADD CONSTRAINT "aws_details_aws_Arn_key" UNIQUE ("aws_Arn");


--
-- Name: aws_details aws_details_aws_SecretAccessKey_key; Type: CONSTRAINT; Schema: public; Owner: poptape_aws
--

ALTER TABLE ONLY public.aws_details
    ADD CONSTRAINT "aws_details_aws_SecretAccessKey_key" UNIQUE ("aws_SecretAccessKey");


--
-- Name: aws_details aws_details_aws_UserId_key; Type: CONSTRAINT; Schema: public; Owner: poptape_aws
--

ALTER TABLE ONLY public.aws_details
    ADD CONSTRAINT "aws_details_aws_UserId_key" UNIQUE ("aws_UserId");


--
-- Name: aws_details aws_details_aws_UserName_key; Type: CONSTRAINT; Schema: public; Owner: poptape_aws
--

ALTER TABLE ONLY public.aws_details
    ADD CONSTRAINT "aws_details_aws_UserName_key" UNIQUE ("aws_UserName");


--
-- Name: aws_details aws_details_pkey; Type: CONSTRAINT; Schema: public; Owner: poptape_aws
--

ALTER TABLE ONLY public.aws_details
    ADD CONSTRAINT aws_details_pkey PRIMARY KEY (public_id);


--
-- PostgreSQL database dump complete
--

