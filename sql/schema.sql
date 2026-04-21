-- =============================================================
-- schema.sql
-- =============================================================

CREATE TABLE stag_orders (
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    amount NUMERIC,
    order_date timestamp,
    stag_order_status TEXT,
    order_date_raw timestamp
);

CREATE TABLE stag_products (
    product_id INT,
    product_name TEXT,
    category TEXT,
    price NUMERIC
);

CREATE TABLE IF NOT EXISTS stag_customers (
    customer_id   INT,
    customer_name text,
    email text,
    city text,
    created_at timestamp
);

CREATE TABLE rejected_orders (
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    amount NUMERIC,
    order_date timestamp,
    stag_order_status TEXT,
    order_date_raw TEXT,
    error_reason TEXT,
    rejected_at timestamp DEFAULT now()
);

CREATE TABLE raw_products_files (
    id BIGSERIAL PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_hash TEXT not null,
    file_content TEXT NOT NULL,
    ingested_at timestamp DEFAULT now() NOT NULL,
    CONSTRAINT uq_file_name UNIQUE (file_hash)
);

CREATE TABLE IF NOT EXISTS products (
    product_id     INT PRIMARY KEY,
    product_name   text NOT NULL,
    category text NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    CONSTRAINT product_product_name_unique UNIQUE (product_name)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id  INT PRIMARY KEY,
    customer_name text NOT NULL,
    email text NOT NULL CHECK (position('@' in email) > 1),
    city text NOT NULL,
    created_at timestamp NOT NULL,
    CONSTRAINT customers_email_unique UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id                 INTEGER           PRIMARY KEY,
    customer_id              int          REFERENCES customers(customer_id),
    product_id               INT NOT NULL  REFERENCES products(product_id),
    quantity                 INTEGER NOT NULL  CHECK (quantity > 0),
    amount                   NUMERIC(8,2) NOT NULL CHECK (amount >= 0),
    order_date               timestamp NOT NULL,
    order_status             VARCHAR(9) NOT NULL,
    created_at               timestamp         DEFAULT now() NOT NULL
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);