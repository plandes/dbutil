-- meta=init_sections=create_tables,create_idx

-- name=create_idx
create index person_name on person(name);

-- name=create_tables
create table person (name text, age int);

-- name=insert_person
insert into person (${cols}) values (?, ?);

-- name=select_people; note that the order is needed for the unit tests only
select ${cols}, rowid as id
       from person
       order by name;

-- name=select_people_by_id
select ${cols}, rowid as id from person where id = ?;

-- name=update_person
update person set name = ?, age = ? where rowid = ?;

-- name=delete_person
delete from person where rowid = ?;
