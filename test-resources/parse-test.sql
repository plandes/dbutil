-- meta=init_sections=create_tables,create_idx

-- name=create_idx
create index person_name on person(name);

-- name=create_tables
create table person (id int, name text, age int);
