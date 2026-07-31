--
-- PostgreSQL database dump
--

\restrict ZMu4MSW8Z88KI6ACy4QRxHedIYhI5MNndemjqtLDBpdcC5K7iN6hsjEC71lNnN4

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: guidance_chunks; Type: TABLE; Schema: public; Owner: dlab
--

CREATE TABLE public.guidance_chunks (
    id integer NOT NULL,
    guidance_id integer,
    chunk_content text NOT NULL,
    chunk_index integer NOT NULL,
    embedding public.vector(1536),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.guidance_chunks OWNER TO dlab;

--
-- Name: guidance_chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: dlab
--

CREATE SEQUENCE public.guidance_chunks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.guidance_chunks_id_seq OWNER TO dlab;

--
-- Name: guidance_chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dlab
--

ALTER SEQUENCE public.guidance_chunks_id_seq OWNED BY public.guidance_chunks.id;


--
-- Name: guidance_molecules; Type: TABLE; Schema: public; Owner: dlab
--

CREATE TABLE public.guidance_molecules (
    guidance_id integer NOT NULL,
    molecule_id integer NOT NULL
);


ALTER TABLE public.guidance_molecules OWNER TO dlab;

--
-- Name: guidances; Type: TABLE; Schema: public; Owner: dlab
--

CREATE TABLE public.guidances (
    id integer NOT NULL,
    rld_rs_number character varying(100) NOT NULL,
    type character varying(50) NOT NULL,
    route character varying(150) NOT NULL,
    dosage_form character varying(255) NOT NULL,
    date_recommended date NOT NULL,
    pdf_url text NOT NULL,
    pdf_path text,
    markdown_path text,
    markdown_content text,
    pdf_hash character varying(64),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.guidances OWNER TO dlab;

--
-- Name: guidances_id_seq; Type: SEQUENCE; Schema: public; Owner: dlab
--

CREATE SEQUENCE public.guidances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.guidances_id_seq OWNER TO dlab;

--
-- Name: guidances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dlab
--

ALTER SEQUENCE public.guidances_id_seq OWNED BY public.guidances.id;


--
-- Name: molecules; Type: TABLE; Schema: public; Owner: dlab
--

CREATE TABLE public.molecules (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    chembl_id character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.molecules OWNER TO dlab;

--
-- Name: molecules_id_seq; Type: SEQUENCE; Schema: public; Owner: dlab
--

CREATE SEQUENCE public.molecules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.molecules_id_seq OWNER TO dlab;

--
-- Name: molecules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dlab
--

ALTER SEQUENCE public.molecules_id_seq OWNED BY public.molecules.id;


--
-- Name: guidance_chunks id; Type: DEFAULT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidance_chunks ALTER COLUMN id SET DEFAULT nextval('public.guidance_chunks_id_seq'::regclass);


--
-- Name: guidances id; Type: DEFAULT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidances ALTER COLUMN id SET DEFAULT nextval('public.guidances_id_seq'::regclass);


--
-- Name: molecules id; Type: DEFAULT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.molecules ALTER COLUMN id SET DEFAULT nextval('public.molecules_id_seq'::regclass);


--
-- Name: guidance_chunks guidance_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidance_chunks
    ADD CONSTRAINT guidance_chunks_pkey PRIMARY KEY (id);


--
-- Name: guidance_molecules guidance_molecules_pkey; Type: CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidance_molecules
    ADD CONSTRAINT guidance_molecules_pkey PRIMARY KEY (guidance_id, molecule_id);


--
-- Name: guidances guidances_pkey; Type: CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidances
    ADD CONSTRAINT guidances_pkey PRIMARY KEY (id);


--
-- Name: molecules molecules_chembl_id_key; Type: CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.molecules
    ADD CONSTRAINT molecules_chembl_id_key UNIQUE (chembl_id);


--
-- Name: molecules molecules_name_key; Type: CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.molecules
    ADD CONSTRAINT molecules_name_key UNIQUE (name);


--
-- Name: molecules molecules_pkey; Type: CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.molecules
    ADD CONSTRAINT molecules_pkey PRIMARY KEY (id);


--
-- Name: idx_guidance_chunks_embedding; Type: INDEX; Schema: public; Owner: dlab
--

CREATE INDEX idx_guidance_chunks_embedding ON public.guidance_chunks USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: idx_guidances_search; Type: INDEX; Schema: public; Owner: dlab
--

CREATE INDEX idx_guidances_search ON public.guidances USING btree (rld_rs_number, dosage_form, route);


--
-- Name: idx_guidances_unique; Type: INDEX; Schema: public; Owner: dlab
--

CREATE UNIQUE INDEX idx_guidances_unique ON public.guidances USING btree (rld_rs_number, dosage_form, route);


--
-- Name: idx_molecules_name; Type: INDEX; Schema: public; Owner: dlab
--

CREATE INDEX idx_molecules_name ON public.molecules USING btree (name);


--
-- Name: guidance_chunks guidance_chunks_guidance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidance_chunks
    ADD CONSTRAINT guidance_chunks_guidance_id_fkey FOREIGN KEY (guidance_id) REFERENCES public.guidances(id) ON DELETE CASCADE;


--
-- Name: guidance_molecules guidance_molecules_guidance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidance_molecules
    ADD CONSTRAINT guidance_molecules_guidance_id_fkey FOREIGN KEY (guidance_id) REFERENCES public.guidances(id) ON DELETE CASCADE;


--
-- Name: guidance_molecules guidance_molecules_molecule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dlab
--

ALTER TABLE ONLY public.guidance_molecules
    ADD CONSTRAINT guidance_molecules_molecule_id_fkey FOREIGN KEY (molecule_id) REFERENCES public.molecules(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict ZMu4MSW8Z88KI6ACy4QRxHedIYhI5MNndemjqtLDBpdcC5K7iN6hsjEC71lNnN4

