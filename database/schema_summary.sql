DROP TABLE IF EXISTS last_changes_dates_primary; 
DROP TABLE IF EXISTS last_data_dates;
DROP TABLE IF EXISTS tt;
DROP TABLE IF EXISTS data;
DROP TABLE IF EXISTS carts;

CREATE TABLE last_changes_dates_primary (
  proc_changes TEXT,
  roz_changes TEXT
);

CREATE TABLE last_data_dates (
  first_date TEXT,
  last_date TEXT
);

CREATE TABLE tt (
  div_name TEXT NOT NULL,  
  reg_name TEXT NOT NULL,  
  city_name TEXT NOT NULL, 
  old_shop INTEGER,     
  shop_name TEXT UNIQUE NOT NULL,   
  shop_id INTEGER UNIQUE NOT NULL 
);

CREATE TABLE data (
  date_month TEXT, 
  shop_id INTEGER,
  old_shop INTEGER,    
  sales_bn REAL, 
  sales_carts_bn REAL,   
  checks_qnt REAL,
  checks_carts_qnt REAL,  
  sales_not_bn REAL,  
  self_cost REAL,
  write_off REAL,
  beer_litres REAL,
  beer_kz_litres REAL,
  FOREIGN KEY (shop_id) REFERENCES tt (shop_id)  
);

CREATE TABLE carts (
  date_month TEXT,  
  shop_id INTEGER,
  old_shop INTEGER,  
  cart INTEGER,
  FOREIGN KEY (shop_id) REFERENCES tt (shop_id)  
);