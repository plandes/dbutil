-- meta=init_sections=create_tables,create_idx

-- name=create_idx
create index item_uid on item(uid);

-- name=create_tables
create table item (uid text, dat blob, primary key (uid));

-- name=insert_item
insert into item (uid, dat) values (?, ?);

-- name=select_item_by_id
select dat from item where uid = ?;

-- name=update_item
update item set dat = ? where uid = ?;

-- name=delete_item
delete from item where uid = ?;

-- name=entries_ids
select uid from item;

-- name=select_item_exists_by_id
select count(*) from item where uid = ?;

-- name=entries_count
select count(*) from item;
